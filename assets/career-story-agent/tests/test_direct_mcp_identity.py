"""Direct MCP calls must stay on the authenticated employee.

These tests call the tool wrapper with a fake tool. They do not open a network
connection to the SuccessFactors MCP server.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def _jwt(payload: dict[str, Any]) -> str:
    segment = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"header.{segment}.signature"


def _recording_tool(name: str, result: Any, *fields: str) -> tuple[StructuredTool, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    async def _run(**kwargs: Any) -> str:
        calls.append(dict(kwargs))
        if isinstance(result, str):
            return result
        return json.dumps(result)

    definitions: dict[str, Any] = {
        field: (str, Field(default=None, description="")) for field in fields
    }
    schema = create_model(f"{name}_args", **definitions) if definitions else create_model(f"{name}_args")
    tool = StructuredTool(
        name=name,
        description="Recording tool for identity binding tests.",
        args_schema=schema,
        coroutine=_run,
    )
    return tool, calls


@pytest.fixture
def identity_env(monkeypatch: pytest.MonkeyPatch):
    """Drop demo-mode configuration and any request token left by another test."""
    from mcp_providers.agw import reset_user_token, set_user_token

    monkeypatch.delenv("SF_MCP_DEMO_MODE", raising=False)
    monkeypatch.delenv("SF_MCP_DEFAULT_USER_ID", raising=False)
    monkeypatch.delenv("MCP_PROVIDER", raising=False)
    token = set_user_token(None)
    try:
        yield
    finally:
        reset_user_token(token)


@pytest.mark.asyncio
async def test_foreign_user_id_is_not_forwarded(identity_env):
    from mcp_providers.agw import _wrap_tool, set_user_token

    tool, calls = _recording_tool(
        "get_employee",
        {"employee": {"user_id": "100200", "display_name": "Alex Chen"}},
        "user_id",
        "employee",
    )
    set_user_token(_jwt({"user_id": "100200", "sub": "11111111-1111-1111-1111-111111111111"}))
    wrapped = _wrap_tool(tool)

    await wrapped.ainvoke({"user_id": "999999", "employee": "888888"})

    assert calls == [{"user_id": "100200", "employee": "100200"}]


@pytest.mark.asyncio
async def test_missing_auth_is_rejected_without_calling_the_tool(identity_env):
    from mcp_providers.agw import _wrap_tool

    tool, calls = _recording_tool("get_employee", {"ok": True}, "user_id")
    wrapped = _wrap_tool(tool)

    raw = await wrapped.ainvoke({"user_id": "100045"})

    assert calls == []
    payload = json.loads(raw)
    assert payload["ok"] is False
    assert payload["error_type"] == "identity_required"
    assert "No authenticated employee identity" in payload["message"]
    assert "100045" not in raw


@pytest.mark.asyncio
async def test_default_user_id_alone_does_not_bind_demo_employee(identity_env, monkeypatch):
    from mcp_providers.agw import _wrap_tool

    monkeypatch.setenv("SF_MCP_DEFAULT_USER_ID", "100045")
    tool, calls = _recording_tool("get_employee", {"ok": True}, "user_id")

    raw = await _wrap_tool(tool).ainvoke({})

    assert calls == []
    assert json.loads(raw)["ok"] is False


@pytest.mark.asyncio
async def test_token_without_employee_id_is_rejected(identity_env):
    from mcp_providers.agw import _wrap_tool, set_user_token

    set_user_token(_jwt({
        "sub": "11111111-2222-3333-4444-555555555555",
        "email": "alex@example.com",
    }))
    tool, calls = _recording_tool("get_goals", {"ok": True}, "user_id")

    raw = await _wrap_tool(tool).ainvoke({"user_id": "100045"})

    assert calls == []
    payload = json.loads(raw)
    assert "did not include an employee id" in payload["message"]


@pytest.mark.asyncio
async def test_authenticated_token_binds_to_that_caller(identity_env, monkeypatch):
    from mcp_providers.agw import _wrap_tool, set_user_token

    monkeypatch.setenv("SF_MCP_DEMO_MODE", "1")
    monkeypatch.setenv("SF_MCP_DEFAULT_USER_ID", "100045")
    set_user_token(_jwt({"user_name": "alex.chen", "sub": "not-a-user-id"}))
    tool, calls = _recording_tool("get_employee", {"user_id": "alex.chen"}, "user_id")

    await _wrap_tool(tool).ainvoke({"user_id": "100045"})

    assert calls == [{"user_id": "alex.chen"}]


@pytest.mark.asyncio
async def test_login_name_in_nested_claim_binds_caller(identity_env):
    from mcp_providers.agw import _wrap_tool, set_user_token

    set_user_token(_jwt({"ext_attr": {"employee_id": ["100200"]}}))
    tool, calls = _recording_tool("get_employee", {"ok": True}, "user_id")

    await _wrap_tool(tool).ainvoke({"user_id": "100045"})

    assert calls == [{"user_id": "100200"}]


@pytest.mark.asyncio
async def test_non_uuid_sub_binds_when_no_explicit_employee_claim(identity_env):
    from mcp_providers.agw import _wrap_tool, set_user_token

    set_user_token(_jwt({"sub": "100200"}))
    tool, calls = _recording_tool("get_employee", {"ok": True}, "user_id")

    await _wrap_tool(tool).ainvoke({})

    assert calls == [{"user_id": "100200"}]


@pytest.mark.asyncio
async def test_demo_mode_cannot_be_overridden_and_is_not_signed_in(identity_env, monkeypatch):
    from mcp_providers.agw import _wrap_tool

    monkeypatch.setenv("SF_MCP_DEMO_MODE", "1")
    monkeypatch.setenv("SF_MCP_DEFAULT_USER_ID", "100045")
    employee, employee_calls = _recording_tool(
        "get_employee",
        {"employee": {"display_name": "Jane Smith", "title": "Finance Analyst"}},
        "user_id",
    )
    whoami, whoami_calls = _recording_tool(
        "who_am_i",
        {"signed_in": True, "user_id": "999999", "display_name": "Someone Else"},
    )
    wrapped_employee = _wrap_tool(employee)
    wrapped_whoami = _wrap_tool(whoami, employee_lookup=employee)

    await wrapped_employee.ainvoke({"user_id": "999999"})
    raw = await wrapped_whoami.ainvoke({})

    assert employee_calls[0] == {"user_id": "100045"}
    assert whoami_calls == [{}]
    # The profile lookup uses the configured demo id, not the foreign id.
    assert employee_calls[-1] == {"user_id": "100045"}
    payload = json.loads(raw)
    assert payload["signed_in"] is False
    assert payload["demo"] is True
    assert payload["user_id"] == "100045"
    assert payload["mode"] == "democo_demo_employee"
    assert payload["display_name"] == "Jane Smith"
    assert "Someone Else" not in raw


@pytest.mark.asyncio
async def test_demo_mode_without_configured_id_is_rejected(identity_env, monkeypatch):
    from mcp_providers.agw import _wrap_tool

    monkeypatch.setenv("SF_MCP_DEMO_MODE", "1")
    tool, calls = _recording_tool("get_employee", {"ok": True}, "user_id")

    raw = await _wrap_tool(tool).ainvoke({"user_id": "100045"})

    assert calls == []
    assert "SF_MCP_DEFAULT_USER_ID" in json.loads(raw)["message"]


@pytest.mark.asyncio
async def test_authenticated_who_am_i_uses_the_caller(identity_env):
    from mcp_providers.agw import _wrap_tool, set_user_token

    set_user_token(_jwt({"userId": 100200}))
    matched, matched_calls = _recording_tool(
        "who_am_i",
        {"signed_in": True, "user_id": "100200", "display_name": "Alex Chen"},
    )
    foreign, foreign_calls = _recording_tool(
        "who_am_i",
        {"signed_in": True, "user_id": "100045", "display_name": "Jane Smith"},
    )

    matched_raw = await _wrap_tool(matched).ainvoke({})
    foreign_raw = await _wrap_tool(foreign).ainvoke({})

    assert matched_calls == [{}]
    assert json.loads(matched_raw)["display_name"] == "Alex Chen"
    assert json.loads(matched_raw)["signed_in"] is True
    assert foreign_calls == [{}]
    foreign_payload = json.loads(foreign_raw)
    assert foreign_payload["signed_in"] is True
    assert foreign_payload["user_id"] == "100200"
    assert foreign_payload["mode"] == "authenticated_employee"
    assert "Jane Smith" not in foreign_raw


def test_direct_mode_stays_off_under_pytest_and_api_key_is_empty(identity_env, monkeypatch):
    from mcp_providers.agw import _SF_MCP_API_KEY, _use_direct_mcp

    assert _SF_MCP_API_KEY == ""
    monkeypatch.setenv("SF_MCP_API_KEY", "not-a-real-key")
    assert "PYTEST_CURRENT_TEST" in os.environ
    assert _use_direct_mcp() is False

    monkeypatch.setenv("MCP_PROVIDER", "direct")
    assert _use_direct_mcp() is True


@pytest.mark.asyncio
async def test_pytest_mock_tools_still_load_without_direct_mode(identity_env):
    from mcp_providers.agw import get_mcp_tools

    assert os.environ.get("IBD_TESTING") == "1"
    tools = await get_mcp_tools()
    assert len(tools) > 0
    assert "PYTEST_CURRENT_TEST" in os.environ
