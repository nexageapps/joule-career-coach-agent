"""Tests for mcp_providers/agw.py in IBD_TESTING mode (mock path)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


# ---------------------------------------------------------------------------
# _build_mock_tools — the private helper used in test mode
# ---------------------------------------------------------------------------

def test_build_mock_tools_returns_list():
    from mcp_providers.agw import _build_mock_tools
    tools = _build_mock_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0


def test_build_mock_tools_all_have_name_and_description():
    from mcp_providers.agw import _build_mock_tools
    tools = _build_mock_tools()
    for t in tools:
        assert t.name, f"Tool missing name: {t}"
        assert t.description, f"Tool '{t.name}' missing description"


def test_build_mock_tools_missing_file_returns_empty(tmp_path):
    from mcp_providers import agw as agw_module
    # Temporarily redirect the mock file path
    original = agw_module._MOCK_FILE
    try:
        agw_module._MOCK_FILE = tmp_path / "nonexistent.json"
        tools = agw_module._build_mock_tools()
        assert tools == []
    finally:
        agw_module._MOCK_FILE = original


def test_build_mock_tools_invalid_json_returns_empty(tmp_path):
    from mcp_providers import agw as agw_module
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ this is not valid json }")
    original = agw_module._MOCK_FILE
    try:
        agw_module._MOCK_FILE = bad_file
        tools = agw_module._build_mock_tools()
        assert tools == []
    finally:
        agw_module._MOCK_FILE = original


@pytest.mark.asyncio
async def test_get_mcp_tools_in_test_mode_returns_mock_tools():
    from mcp_providers.agw import get_mcp_tools
    # IBD_TESTING is already set to "1" by conftest
    tools = await get_mcp_tools()
    assert len(tools) > 0


def test_build_mock_tools_tools_are_callable():
    """All mock tools must have a coroutine or func."""
    from mcp_providers.agw import _build_mock_tools
    tools = _build_mock_tools()
    for t in tools:
        has_callable = getattr(t, "coroutine", None) is not None or getattr(t, "func", None) is not None
        assert has_callable, f"Tool '{t.name}' has no callable"


def test_build_mock_tools_integer_field():
    """Tools with integer fields in schema should build correctly."""
    from mcp_providers import agw as agw_module
    import tempfile, json

    mock_data = {
        "servers": {
            "test-server": {
                "mcp_server_name": "sap.mcp/test",
                "description": "Test server",
                "tools": {
                    "test_tool": {
                        "description": "A test tool with an integer field.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "count": {"type": "integer", "description": "Count"},
                                "ratio": {"type": "number", "description": "Ratio"},
                                "flag": {"type": "boolean", "description": "Flag"},
                                "name": {"type": "string", "description": "Name"}
                            },
                            "required": ["count"]
                        },
                        "mock_response": {"result": "ok"}
                    }
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(mock_data, f)
        tmp_path = Path(f.name)

    original = agw_module._MOCK_FILE
    try:
        agw_module._MOCK_FILE = tmp_path
        tools = agw_module._build_mock_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
    finally:
        agw_module._MOCK_FILE = original
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# set_user_token / get_user_token / reset_user_token
# ---------------------------------------------------------------------------

def test_set_and_get_user_token():
    from mcp_providers.agw import set_user_token, get_user_token, reset_user_token
    token = set_user_token("test-token-abc")
    assert get_user_token() == "test-token-abc"
    reset_user_token(token)


def test_reset_user_token_restores_previous():
    from mcp_providers.agw import set_user_token, get_user_token, reset_user_token
    # Set initial value
    t1 = set_user_token("first-token")
    # Override
    t2 = set_user_token("second-token")
    assert get_user_token() == "second-token"
    # Reset to first
    reset_user_token(t2)
    assert get_user_token() == "first-token"
    reset_user_token(t1)


# ---------------------------------------------------------------------------
# get_user_sub
# ---------------------------------------------------------------------------

def test_get_user_sub_in_test_mode_no_token():
    from mcp_providers.agw import get_user_sub, set_user_token, reset_user_token
    token = set_user_token(None)
    try:
        # IBD_TESTING=1 → returns "unknown"
        result = get_user_sub()
        assert result == "unknown"
    finally:
        reset_user_token(token)


def test_get_user_sub_decodes_jwt_sub():
    """get_user_sub must decode the sub claim from a real JWT payload."""
    import base64
    from mcp_providers.agw import get_user_sub, set_user_token, reset_user_token

    # Build a minimal JWT: header.payload.signature
    payload = {"sub": "user-12345", "name": "Jordan Smith"}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    fake_jwt = f"header.{payload_b64}.signature"

    token_ctx = set_user_token(fake_jwt)
    try:
        sub = get_user_sub()
        assert sub == "user-12345"
    finally:
        reset_user_token(token_ctx)


def test_get_user_sub_raises_when_no_token_and_not_testing():
    from mcp_providers.agw import get_user_sub, set_user_token, reset_user_token
    token = set_user_token(None)
    try:
        with patch.dict(os.environ, {"IBD_TESTING": "0"}):
            with pytest.raises(ValueError, match="No user token"):
                get_user_sub()
    finally:
        reset_user_token(token)
