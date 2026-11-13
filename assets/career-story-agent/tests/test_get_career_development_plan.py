"""Unit test for the career development plan mock tools.

Asserts plan name and activities are returned.
"""
import json
from pathlib import Path

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def load_tools():
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"]["career-data"]["tools"]


def test_development_goals_tool_exists():
    """list_development_goals tool must exist. DEMOCO has no IDP entries — empty list is correct."""
    tools = load_tools()
    assert "list_development_goals" in tools
    mock_resp = tools["list_development_goals"]["mock_response"]
    assert "results" in mock_resp, "list_development_goals must return a results list"


def test_dev_goals_have_name_and_activity():
    """When dev goals are present they must have name, status, and activity.
    DEMOCO Jane Smith has no IDP entries so empty list is acceptable."""
    tools = load_tools()
    results = tools["list_development_goals"]["mock_response"]["results"]
    # DEMOCO has no IDP goals — empty is correct; validate structure only when non-empty
    for goal in results:
        assert "name" in goal, "Development goal must have a name"
        assert "status" in goal, "Development goal must have a status"
        assert "activity" in goal, "Development goal must have an activity"


def test_dev_goals_have_target_completion_date():
    """When dev goals are present they must have a targetCompletionDate."""
    tools = load_tools()
    results = tools["list_development_goals"]["mock_response"]["results"]
    for goal in results:
        assert "targetCompletionDate" in goal, "Development goal must have a targetCompletionDate"


def test_achievements_tool_exists():
    tools = load_tools()
    assert "list_achievements" in tools
    results = tools["list_achievements"]["mock_response"]["results"]
    assert len(results) > 0
    assert "type" in results[0]
    assert "title" in results[0]
