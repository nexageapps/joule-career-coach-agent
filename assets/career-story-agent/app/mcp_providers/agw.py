"""MCP tool provider — Agent Gateway plus an inlined direct MCP client.

Exposes `async def get_mcp_tools() -> list[BaseTool]` which discovers MCP tools
and converts them to LangChain tools.

Behaviour is controlled by MCP_PROVIDER and IBD_TESTING:

  MCP_PROVIDER=direct (or SF_MCP_API_KEY set, outside pytest):
      Uses the inlined custom Python MCP client (no Agent Gateway, no BTP
      destination). This path is checked first, including when IBD_TESTING=1,
      so Joule Studio "Preview with Mock Data" can still reach the live MCP
      server.

  MCP_PROVIDER=agw, or no key / under pytest:
      Production (IBD_TESTING not set):
          Uses the Agent Gateway SDK client. The user token is read from a
          per-request context variable set by JWTContextMiddleware in main.py.
          Tools are fetched per-request (may vary per user).

      Local / test mode (IBD_TESTING=1):
          Reads mcp-mock.json from the directory containing this file's
          grandparent (i.e. <asset-root>/mcp-mock.json) and returns LangChain
          StructuredTool instances built from the mock data — no network calls.

Direct MCP tool calls are bound to the authenticated employee. The request
JWT (set by JWTContextMiddleware) is decoded for an employee id, and every
tool user_id is forced to that id. A model-supplied or caller-supplied
user_id is ignored. If the token is present but does not yield an employee
id, the tool call is rejected and the remote tool is not invoked.

When no request JWT is present, the tool call is rejected. Calls are not
defaulted to a demo employee, and a synthetic binding is not reported as
signed in.

A local DEMOCO preview is opt-in and off by default. Set both
SF_MCP_DEMO_MODE=1 and SF_MCP_DEFAULT_USER_ID to a demo employee id. While
that flag is on and no request JWT is present, tool user_id values are
forced to the configured id and who_am_i is labeled as a demo session
(signed_in is not true). A request JWT takes precedence over demo mode.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, Never

from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from opentelemetry import trace
from pydantic import Field, create_model
from sap_cloud_sdk.agentgateway import create_client
from sap_cloud_sdk.agentgateway.converters import mcp_tool_to_langchain

from util import call_mcp_tool, minify_json, truncate_response

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Direct MCP defaults. The API key is read from SF_MCP_API_KEY and is never
# stored in source. SF_MCP_URL overrides the demo endpoint when set.
_SF_MCP_URL = "https://heisenberglupenix-successfactors-mcp.hf.space/mcp"
_SF_MCP_API_KEY = ""


# Per-request user token, set by JWTContextMiddleware via set_user_token()
_user_token_context: ContextVar[str | None] = ContextVar("user_token", default=None)

# mcp-mock.json lives at the asset root (two levels above mcp_providers/)
_MOCK_FILE = Path(__file__).parent.parent.parent / "mcp-mock.json"

SERVER_NAME = "successfactors"

# Read-only tools the career story needs: identity/profile, job history,
# skills, goals, reviews, achievements, learning and certifications.
DEFAULT_TOOL_ALLOWLIST: tuple[str, ...] = (
    "who_am_i",
    "get_employee",
    "get_employee_profile",
    "get_job_information",
    "get_employment_information",
    "get_position",
    "get_manager",
    "tell_my_story",
    "get_goals",
    "get_skills",
    "get_achievements",
    "get_performance_review",
    "get_learning_activities",
    "get_learning_catalog",
    "get_certifications",
)

# Always excluded, even if someone adds them to the allowlist.
_DENY_PATTERN = re.compile(
    r"(comp|salary|pay|bonus|wage|write|update|create|delete|remove|insert|patch|upsert|approve|submit)",
    re.IGNORECASE,
)

_NON_RETRYABLE_STATUS = {400, 401, 403, 404}

# Claims that are a SuccessFactors userId, then logon names, then a non-UUID sub.
_EXPLICIT_EMPLOYEE_CLAIMS = (
    "user_id",
    "userId",
    "sf_user_id",
    "sfUserId",
    "employee_id",
    "employeeId",
    "empId",
)
_LOGIN_CLAIMS = ("login_name", "loginName", "user_name", "userName")
_NESTED_CLAIM_OBJECTS = ("ext_attr", "attributes", "xs.user.attributes")
_IDENTITY_ARGS = ("user_id", "userId", "employee", "employee_id", "employeeId")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_EMPLOYEE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_DEMO_MODE_ON = {"1", "true", "yes", "on"}

_cache: dict[str, Any] = {"tools": None, "expires": 0.0, "key": None}
# Cached display name/title used when who_am_i must be rewritten for the bound employee.
_demo_profile_cache: dict[str, Any] = {"user_id": None, "profile": None, "expires": 0.0}


class DirectMCPConfigError(RuntimeError):
    """Raised when the direct MCP provider is not configured correctly."""


def set_user_token(token: str | None) -> Token:
    """Set the user token for the current async context (called by JWTContextMiddleware)."""
    return _user_token_context.set(token)


def get_user_token() -> str | None:
    """Get the user token for the current async context."""
    return _user_token_context.get()


def _get_user_token() -> str:
    token = _user_token_context.get()
    assert token is not None, "User token not set in current context"
    return token


def _build_mock_tools() -> list[BaseTool]:
    """Build LangChain StructuredTool instances from mcp-mock.json.

    Returns an empty list (without error) when mcp-mock.json is absent or
    cannot be parsed — add/fix the file to enable tool mocking.
    """
    if not _MOCK_FILE.exists():
        return []

    try:
        mock_data = json.loads(_MOCK_FILE.read_text())
    except Exception:
        logger.warning(
            "Failed to parse mcp-mock.json at %s — returning empty tool list",
            _MOCK_FILE,
            exc_info=True,
        )
        return []

    tools: list[BaseTool] = []

    for _server_slug, server in mock_data.get("servers", {}).items():
        for tool_name, tool_def in server.get("tools", {}).items():
            description = tool_def.get("description", "")
            mock_response = tool_def.get("mock_response", {})
            input_schema = tool_def.get("input_schema", {})

            props = input_schema.get("properties", {})
            required_fields = set(input_schema.get("required", []))
            field_definitions: dict[str, Any] = {}
            for field_name, field_info in props.items():
                json_type = field_info.get("type", "string")
                if json_type == "integer":
                    python_type: type = int
                elif json_type == "number":
                    python_type = float
                elif json_type == "boolean":
                    python_type = bool
                else:
                    python_type = str

                if field_name in required_fields:
                    field_definitions[field_name] = (
                        python_type,
                        Field(description=field_info.get("description", "")),
                    )
                else:
                    field_definitions[field_name] = (
                        python_type,
                        Field(default=None, description=field_info.get("description", "")),
                    )

            args_schema = (
                create_model(f"{tool_name}_args", **field_definitions)
                if field_definitions
                else create_model(f"{tool_name}_args")
            )
            _response = json.dumps(mock_response)

            async def _coroutine(_resp: str = _response, **kwargs: Any) -> str:
                return _resp

            tools.append(
                StructuredTool(
                    name=tool_name,
                    description=description,
                    args_schema=args_schema,
                    coroutine=_coroutine,
                    handle_tool_error=True,
                )
            )

    logger.info("Loaded %d mock MCP tool(s) from %s", len(tools), _MOCK_FILE)
    return tools


def _secret(name: str) -> str:
    """Fallback for Joule Studio, which has no env/secret UI: use inlined constants.

    Disabled under pytest so unit tests that clear the env stay deterministic
    and never pick up the hard-coded key. Environment variables always win
    when they are set.
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        return ""
    if name == "SF_MCP_URL":
        return str(_SF_MCP_URL or "").strip()
    if name == "SF_MCP_API_KEY":
        return str(_SF_MCP_API_KEY or "").strip()
    return ""


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def get_allowlist() -> tuple[str, ...]:
    raw = os.environ.get("SF_MCP_TOOL_ALLOWLIST", "").strip()
    if not raw:
        return DEFAULT_TOOL_ALLOWLIST
    return tuple(n.strip() for n in raw.split(",") if n.strip())


def build_connection() -> dict[str, Any]:
    """Build the MultiServerMCPClient connection config from env or inlined constants."""
    url = (os.environ.get("SF_MCP_URL", "") or _secret("SF_MCP_URL")).strip()
    if not url:
        raise DirectMCPConfigError("SF_MCP_URL is not set")
    if not url.startswith("https://") and not url.startswith("http://localhost"):
        raise DirectMCPConfigError("SF_MCP_URL must use https")

    headers: dict[str, str] = {}
    api_key = (os.environ.get("SF_MCP_API_KEY", "") or _secret("SF_MCP_API_KEY")).strip()
    if api_key:
        header = os.environ.get("SF_MCP_AUTH_HEADER", "Authorization").strip() or "Authorization"
        headers[header] = f"Bearer {api_key}" if header.lower() == "authorization" else api_key
    else:
        logger.warning("SF_MCP_API_KEY not set; calling MCP server without credentials")

    return {
        "transport": "streamable_http",
        "url": url,
        "headers": headers,
        "timeout": timedelta(seconds=_env_float("SF_MCP_HTTP_TIMEOUT_SECONDS", 30)),
        "sse_read_timeout": timedelta(seconds=_env_float("SF_MCP_READ_TIMEOUT_SECONDS", 60)),
    }


def is_read_only_tool(tool: BaseTool, allowlist: tuple[str, ...]) -> bool:
    """Return True only for allowlisted tools that are not write/compensation tools."""
    if tool.name not in allowlist:
        return False
    if _DENY_PATTERN.search(tool.name):
        return False
    meta = tool.metadata or {}
    return not (meta.get("readOnlyHint") is False or meta.get("destructiveHint") is True)


def _status_code(exc: BaseException) -> int | None:
    """Find an HTTP status code inside (possibly grouped) exceptions."""
    stack: list[BaseException] = [exc]
    while stack:
        e = stack.pop()
        resp = getattr(e, "response", None)
        code = getattr(resp, "status_code", None)
        if isinstance(code, int):
            return code
        if isinstance(e, BaseExceptionGroup):
            stack.extend(e.exceptions)
        if e.__cause__ is not None:
            stack.append(e.__cause__)
    return None


def _schema_field_names(schema: Any) -> set[str]:
    """Return argument names declared on a tool args schema (dict or Pydantic)."""
    if schema is None:
        return set()
    if isinstance(schema, dict):
        props = schema.get("properties")
        if isinstance(props, dict):
            return set(props)
        return set()
    fields = getattr(schema, "model_fields", None)
    if isinstance(fields, dict):
        return set(fields)
    fields = getattr(schema, "__fields__", None)
    if isinstance(fields, dict):
        return set(fields)
    return set()


def _tool_accepts_arg(tool: BaseTool, name: str) -> bool:
    """Return True when the tool declares `name` as a parameter."""
    if name in _schema_field_names(getattr(tool, "args_schema", None)):
        return True
    args = getattr(tool, "args", None)
    return isinstance(args, dict) and name in args


@dataclass(frozen=True)
class _CallerIdentity:
    """Employee id a direct MCP call is allowed to read."""

    user_id: str
    source: Literal["jwt", "demo"]


def _demo_mode_enabled() -> bool:
    """Return True only when SF_MCP_DEMO_MODE is an explicit opt-in value."""
    return os.environ.get("SF_MCP_DEMO_MODE", "").strip().lower() in _DEMO_MODE_ON


def _configured_demo_user_id() -> str:
    """Demo employee id when demo mode is on. Empty when the flag is off or unset."""
    if not _demo_mode_enabled():
        return ""
    return os.environ.get("SF_MCP_DEFAULT_USER_ID", "").strip()


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Return the JWT payload object, or None when the token cannot be decoded.

    Signature verification is the platform's job (see get_user_sub). This only
    reads the payload so a tool call can be bound to the authenticated employee.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2 or not parts[1]:
            return None
        payload_segment = parts[1]
        padding = (-len(payload_segment)) % 4
        decoded = base64.urlsafe_b64decode(payload_segment + ("=" * padding))
        payload = json.loads(decoded)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _as_employee_id(value: Any) -> str | None:
    """Return a single employee id from a claim value, or None when it is ambiguous."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list) and len(value) == 1:
        return _as_employee_id(value[0])
    return None


def _claim_from(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        found = _as_employee_id(payload.get(key))
        if found:
            return found
    return None


def _nested_claim(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for name in _NESTED_CLAIM_OBJECTS:
        nested = payload.get(name)
        if isinstance(nested, dict):
            found = _claim_from(nested, keys)
            if found:
                return found
    return None


def _sub_employee_id(payload: dict[str, Any]) -> str | None:
    """Use sub only when it is an employee id, not a UUID or technical subject."""
    sub = _as_employee_id(payload.get("sub"))
    if not sub or "@" in sub or "|" in sub or sub.lower().startswith("sb-"):
        return None
    if _UUID_RE.fullmatch(sub) or not _EMPLOYEE_ID_RE.fullmatch(sub):
        return None
    return sub


def _employee_id_from_token(token: str) -> str | None:
    """Derive a SuccessFactors employee id from a request JWT, or None."""
    payload = _decode_jwt_payload(token)
    if payload is None:
        return None
    return (
        _claim_from(payload, _EXPLICIT_EMPLOYEE_CLAIMS)
        or _nested_claim(payload, _EXPLICIT_EMPLOYEE_CLAIMS)
        or _claim_from(payload, _LOGIN_CLAIMS)
        or _nested_claim(payload, _LOGIN_CLAIMS)
        or _sub_employee_id(payload)
    )


def _identity_error(message: str) -> str:
    return json.dumps(
        {
            "ok": False,
            "error_type": "identity_required",
            "message": message,
        }
    )


def _caller_identity() -> tuple[_CallerIdentity | None, str | None]:
    """Resolve the employee this request may read.

    A request JWT always wins. Demo mode applies only when no token is present
    and both SF_MCP_DEMO_MODE and SF_MCP_DEFAULT_USER_ID are set. There is no
    built-in demo employee.
    """
    token = _user_token_context.get()
    if token and token.strip():
        employee_id = _employee_id_from_token(token.strip())
        if not employee_id:
            return None, (
                "Authenticated token did not include an employee id. "
                "Refusing the tool call."
            )
        return _CallerIdentity(employee_id, "jwt"), None
    demo_id = _configured_demo_user_id()
    if _demo_mode_enabled():
        if not demo_id:
            return None, (
                "SF_MCP_DEMO_MODE is enabled but SF_MCP_DEFAULT_USER_ID is not set. "
                "Refusing the tool call."
            )
        return _CallerIdentity(demo_id, "demo"), None
    return None, (
        "No authenticated employee identity is available. Refusing the tool call."
    )


def _bind_tool_kwargs(tool: BaseTool, kwargs: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Force identity arguments to user_id and drop any the tool does not accept."""
    updated = dict(kwargs)
    for name in _IDENTITY_ARGS:
        if _tool_accepts_arg(tool, name):
            updated[name] = user_id
        else:
            updated.pop(name, None)
    return updated


def _tool_result_text(result: Any) -> str:
    """Normalise a tool result (string, dict, or content blocks) to text."""
    if isinstance(result, list):
        parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in result]
        return "\n".join(parts)
    if isinstance(result, dict):
        return json.dumps(result)
    return str(result)


def _parse_jsonish(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_name_title(payload: Any) -> dict[str, str]:
    """Pull display_name and title from a get_employee-style payload."""
    out: dict[str, str] = {}
    if not isinstance(payload, dict):
        return out
    candidates = [payload]
    for key in ("employee", "person", "profile", "data", "result"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)
    for obj in candidates:
        name = obj.get("display_name") or obj.get("displayName")
        if not name:
            first = obj.get("first_name") or obj.get("firstName") or ""
            last = obj.get("last_name") or obj.get("lastName") or ""
            name = f"{first} {last}".strip()
        title = obj.get("title") or obj.get("jobTitle") or obj.get("job_title")
        if name and "display_name" not in out:
            out["display_name"] = str(name)
        if title and "title" not in out:
            out["title"] = str(title)
    return out


async def _lookup_demo_profile(user_id: str, employee_lookup: BaseTool | None) -> dict[str, str]:
    """Return cached (or freshly looked-up) display name and title for the demo user."""
    now = time.monotonic()
    cached = _demo_profile_cache
    if (
        cached.get("user_id") == user_id
        and cached.get("profile") is not None
        and now < cached.get("expires", 0)
    ):
        return dict(cached["profile"])
    profile: dict[str, str] = {"user_id": user_id}
    if employee_lookup is not None:
        try:
            raw = await asyncio.wait_for(
                employee_lookup.ainvoke({"user_id": user_id}),
                timeout=_env_float("SF_MCP_DEMO_PROFILE_TIMEOUT_SECONDS", 15),
            )
            profile.update(_extract_name_title(_parse_jsonish(_tool_result_text(raw))))
        except Exception:
            logger.info("Demo employee profile lookup failed; binding user_id only")
            # Do not cache a failed lookup, so a later who_am_i can retry.
            return profile
    _demo_profile_cache.update(
        user_id=user_id,
        profile=dict(profile),
        expires=time.monotonic() + _env_float("SF_MCP_CACHE_TTL_SECONDS", 600),
    )
    return profile


def _who_am_i_matches(text: str, user_id: str) -> bool:
    """Return True when who_am_i is already signed in as this employee."""
    data = _parse_jsonish((text or "").strip())
    if not isinstance(data, dict):
        return False
    signed_in = data.get("signed_in") is True or data.get("signedIn") is True
    uid = data.get("user_id") if data.get("user_id") not in (None, "") else data.get("userId")
    return signed_in and str(uid) == user_id


async def _who_am_i_binding(identity: _CallerIdentity, employee_lookup: BaseTool | None) -> str:
    """Build a who_am_i payload for the bound employee.

    Demo mode never claims signed_in. A JWT binding does, because the platform
    already authenticated that employee.
    """
    binding: dict[str, Any]
    if identity.source == "demo":
        binding = {
            "signed_in": False,
            "demo": True,
            "user_id": identity.user_id,
            "mode": "democo_demo_employee",
            "message": "Local DEMOCO preview. This session is not a signed-in employee.",
        }
    elif identity.source == "jwt":
        binding = {
            "signed_in": True,
            "user_id": identity.user_id,
            "mode": "authenticated_employee",
        }
    else:
        unexpected: Never = identity.source
        raise AssertionError(f"unknown identity source: {unexpected}")
    profile = await _lookup_demo_profile(identity.user_id, employee_lookup)
    if profile.get("display_name"):
        binding["display_name"] = profile["display_name"]
    if profile.get("title"):
        binding["title"] = profile["title"]
    return json.dumps(binding)


async def _shape_who_am_i(
    text: str, identity: _CallerIdentity, employee_lookup: BaseTool | None
) -> str:
    """Return who_am_i text for the bound employee only.

    A remote payload for a different employee is discarded. Demo mode always
    replaces the payload so a server-side signed_in flag cannot leak through.
    """
    if identity.source == "jwt" and _who_am_i_matches(text, identity.user_id):
        return text
    return await _who_am_i_binding(identity, employee_lookup)


def _wrap_tool(tool: BaseTool, employee_lookup: BaseTool | None = None) -> BaseTool:
    """Wrap a remote MCP tool so calls stay on the authenticated employee.

    The request JWT (or an explicit demo-mode id) replaces any supplied
    user_id. Missing identity rejects the call before the remote tool runs.
    who_am_i is rewritten so it cannot describe a different employee or claim
    a demo binding is signed in.
    """

    async def _call(**kwargs: Any) -> str:
        identity, error = _caller_identity()
        if identity is None:
            return _identity_error(
                error or "No authenticated employee identity is available. Refusing the tool call."
            )
        kwargs = _bind_tool_kwargs(tool, kwargs, identity.user_id)
        result = await tool.ainvoke(kwargs)
        text = _tool_result_text(result)
        if tool.name == "who_am_i":
            text = await _shape_who_am_i(text, identity, employee_lookup)
        return truncate_response(minify_json(text))

    return StructuredTool(
        name=tool.name,
        description=f"[{SERVER_NAME}] {tool.description}",
        args_schema=tool.args_schema,
        coroutine=_call,
        metadata=tool.metadata,
        handle_tool_error=True,
    )



async def _list_remote_tools(connection: dict[str, Any]) -> list[BaseTool]:
    client = MultiServerMCPClient({SERVER_NAME: connection})
    return await client.get_tools(server_name=SERVER_NAME)


@tracer.start_as_current_span("direct_mcp.get_tools")
async def get_direct_mcp_tools() -> list[BaseTool]:
    """Discover tools on the remote MCP server and return the read-only subset.

    Retries with exponential backoff to ride out HF Space cold starts, within
    SF_MCP_CONNECT_BUDGET_SECONDS. Auth / bad-request errors are not retried.
    """
    connection = build_connection()
    cache_key = connection["url"] + "|" + ",".join(sorted(connection["headers"]))
    now = time.monotonic()
    if _cache["tools"] is not None and _cache["key"] == cache_key and now < _cache["expires"]:
        return list(_cache["tools"])

    budget = _env_float("SF_MCP_CONNECT_BUDGET_SECONDS", 60)
    deadline = now + budget
    delay = 2.0
    attempt = 0
    while True:
        attempt += 1
        try:
            remote = await asyncio.wait_for(
                _list_remote_tools(connection), timeout=max(5.0, deadline - time.monotonic())
            )
            break
        except Exception as exc:
            code = _status_code(exc)
            remaining = deadline - time.monotonic()
            if code in _NON_RETRYABLE_STATUS or remaining <= delay:
                logger.error(
                    "DIRECT_MCP.missed: tool discovery failed after %d attempt(s) (status=%s, %s)",
                    attempt, code, type(exc).__name__,
                )
                raise
            logger.warning(
                "Direct MCP discovery attempt %d failed (status=%s, %s); retrying in %.0fs",
                attempt, code, type(exc).__name__, delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, 16.0)

    allowlist = get_allowlist()
    lookup = next((t for t in remote if t.name == "get_employee"), None)
    selected = [_wrap_tool(t, employee_lookup=lookup) for t in remote if is_read_only_tool(t, allowlist)]
    selected.sort(key=lambda t: t.name)
    # Warm the demo profile only when demo mode is explicitly configured.
    # There is no built-in employee id, and discovery has no request JWT.
    demo_id = _configured_demo_user_id()
    if demo_id and lookup is not None:
        try:
            await _lookup_demo_profile(demo_id, lookup)
        except Exception:
            logger.info("Demo employee profile prefetch did not complete")
    dropped = len(remote) - len(selected)
    logger.info(
        "DIRECT_MCP.achieved: %d read-only tool(s) loaded, %d dropped (attempts=%d)",
        len(selected), dropped, attempt,
    )
    _cache.update(
        tools=selected,
        key=cache_key,
        expires=time.monotonic() + _env_float("SF_MCP_CACHE_TTL_SECONDS", 600),
    )
    return list(selected)


def clear_cache() -> None:
    """Drop the cached tool listing and demo profile (used by tests)."""
    _cache.update(tools=None, expires=0.0, key=None)
    _demo_profile_cache.update(user_id=None, profile=None, expires=0.0)


def _use_direct_mcp() -> bool:
    """Return True when the direct MCP provider should be used.

    MCP_PROVIDER=direct always selects the direct client, even if IBD_TESTING=1.
    MCP_PROVIDER=agw always selects Agent Gateway / mock tools.
    Otherwise the direct client is used when SF_MCP_API_KEY (or the empty
    in-source fallback) is non-empty and the process is not running under pytest.
    """
    provider = os.environ.get("MCP_PROVIDER", "").strip().lower()
    if provider in ("direct", "agw"):
        return provider == "direct"
    if "PYTEST_CURRENT_TEST" in os.environ:
        return False
    key = (os.environ.get("SF_MCP_API_KEY", "") or str(_SF_MCP_API_KEY or "")).strip()
    return bool(key)


async def get_mcp_tools() -> list[BaseTool]:
    """Return LangChain-compatible MCP tools.

    The direct MCP provider is selected first (see _use_direct_mcp), including
    when IBD_TESTING=1. Otherwise, local/test mode (IBD_TESTING=1) returns mock
    tools from mcp-mock.json, and production uses the Agent Gateway SDK.

    The user token is read from the per-request context var set by JWTContextMiddleware.
    Tools are fetched per-request since tool listings may vary per user.
    """
    # Custom Python path: connect straight to the MCP server (no Agent Gateway,
    # no BTP destination). Checked before the IBD_TESTING mock branch.
    if _use_direct_mcp():
        return await get_direct_mcp_tools()

    if os.environ.get("IBD_TESTING") == "1":
        return _build_mock_tools()

    agw_client = create_client()
    mcp_tools = await agw_client.list_mcp_tools(user_token=_get_user_token)

    if not mcp_tools:
        logger.warning("Agent Gateway returned 0 tools — MCP servers may not be available")
        return []

    def _make_caller(t: Any):
        async def call(_tool: Any = None, *, user_token: Any = None, **kwargs: Any) -> str:
            return await call_mcp_tool(
                agw_client, t, user_token=_get_user_token(), **kwargs
            )
        return call

    tools = [
        mcp_tool_to_langchain(t, _make_caller(t), _get_user_token, handle_tool_error=True)
        for t in mcp_tools
    ]

    logger.info("Loaded %d MCP tool(s) from Agent Gateway", len(tools))
    # Sort deterministically so tool order is stable across requests (cache-stability).
    return sorted(tools, key=lambda t: t.name)


def get_user_sub() -> str:
    """Extract the JWT subject claim from the current request's token.

    Decodes the JWT payload (middle segment) without verifying the signature —
    The platform has already verified it before the request reaches this code.

    Returns:
        The 'sub' claim from the token.

    Raises:
        ValueError: If the token is missing or the sub claim cannot be extracted,
                    unless IBD_TESTING=1, in which case returns 'unknown'.
    """
    token = _user_token_context.get()
    if not token:
        if os.environ.get("IBD_TESTING") == "1":
            return "unknown"
        raise ValueError("No user token in context — cannot extract sub claim")

    try:
        payload_segment = token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_segment) % 4
        if padding != 4:
            payload_segment += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_segment))
        sub = payload.get("sub")
        if not sub:
            raise ValueError("JWT payload contains no 'sub' claim")
        return sub
    except (IndexError, ValueError):
        raise
    except Exception as e:
        raise ValueError(f"Failed to decode JWT payload: {e}") from e


def reset_user_token(token: Token) -> None:
    """Restore the user token context to its previous value.

    Args:
        token: The Token returned by a prior set_user_token() call. Passing it to
            ContextVar.reset() unwinds the context stack to the value that was in
            effect before that set_user_token() call, rather than leaving a stale
            or None value behind.
    """
    _user_token_context.reset(token)
    logger.debug("User token context reset to previous value")
