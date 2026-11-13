"""Tests for MCP tool loading from mcp-mock.json (IBD_TESTING mode)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


@pytest.mark.asyncio
async def test_get_mcp_tools_returns_tools_in_test_mode():
    """In IBD_TESTING mode, get_mcp_tools() must return tools from mcp-mock.json."""
    from mcp_providers.agw import get_mcp_tools
    tools = await get_mcp_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0, "Must return at least one mock tool"


@pytest.mark.asyncio
async def test_mock_tools_are_callable():
    """Each mock tool must be a valid LangChain tool."""
    from langchain_core.tools import BaseTool
    from mcp_providers.agw import get_mcp_tools
    tools = await get_mcp_tools()
    for tool in tools:
        assert isinstance(tool, BaseTool), f"Tool '{tool}' is not a BaseTool instance"
        assert tool.name, "Tool must have a name"
        assert tool.description, "Tool must have a description"


@pytest.mark.asyncio
async def test_mock_tools_include_skills_tools():
    """Mock tools must include skills-related tools."""
    from mcp_providers.agw import get_mcp_tools
    tools = await get_mcp_tools()
    tool_names = [t.name for t in tools]
    skills_tools = [n for n in tool_names if "skill" in n.lower()]
    assert len(skills_tools) > 0, "Must include at least one skills tool"


@pytest.mark.asyncio
async def test_mock_tools_include_goals_tools():
    """Mock tools must include goals-related tools."""
    from mcp_providers.agw import get_mcp_tools
    tools = await get_mcp_tools()
    tool_names = [t.name for t in tools]
    goals_tools = [n for n in tool_names if "goal" in n.lower()]
    assert len(goals_tools) > 0, "Must include at least one goals tool"


def test_mock_file_has_career_data_server():
    """mcp-mock.json must have the consolidated career-data server."""
    data = json.loads(MOCK_FILE.read_text())
    assert "career-data" in data["servers"], "career-data server must be present in mcp-mock.json"


def test_mock_tool_count_under_50():
    """Total mock tools must stay under 50 to keep LLM context lean."""
    data = json.loads(MOCK_FILE.read_text())
    actual_count = sum(len(s["tools"]) for s in data["servers"].values())
    assert actual_count <= 50, f"Expected ≤50 tools to keep context lean, got {actual_count}"
    assert actual_count >= 10, f"Expected at least 10 career tools, got {actual_count}"
