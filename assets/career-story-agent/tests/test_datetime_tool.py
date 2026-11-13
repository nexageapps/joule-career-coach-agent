"""Unit tests for datetime_tool.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from langchain_core.tools import StructuredTool

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def test_get_datetime_tool_returns_structured_tool():
    from datetime_tool import get_datetime_tool
    tool = get_datetime_tool()
    assert isinstance(tool, StructuredTool)


def test_datetime_tool_name():
    from datetime_tool import get_datetime_tool
    tool = get_datetime_tool()
    assert tool.name == "get_current_datetime"


def test_datetime_tool_description():
    from datetime_tool import get_datetime_tool
    tool = get_datetime_tool()
    assert "date" in tool.description.lower() or "time" in tool.description.lower()


def test_datetime_tool_returns_iso_string():
    from datetime_tool import get_datetime_tool, _get_current_datetime
    result = _get_current_datetime()
    assert isinstance(result, str)
    # Should match ISO-8601 format e.g. 2024-01-15T10:30:00Z
    assert "T" in result
    assert result.endswith("Z")
    assert len(result) == 20  # YYYY-MM-DDTHH:MM:SSZ


def test_datetime_tool_invocable_sync():
    from datetime_tool import get_datetime_tool
    tool = get_datetime_tool()
    # Call the underlying sync function
    result = tool.func()
    assert isinstance(result, str)
    assert "T" in result


def test_datetime_tool_has_args_schema():
    from datetime_tool import get_datetime_tool
    tool = get_datetime_tool()
    assert tool.args_schema is not None
    # Schema should have no required fields
    schema = tool.args_schema.model_json_schema()
    required = schema.get("required", [])
    assert len(required) == 0
