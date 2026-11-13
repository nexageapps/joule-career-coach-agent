"""Unit test for the goals mock tools.

Asserts goal name and status are returned.
"""
import json
from pathlib import Path

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def load_tools():
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"]["career-data"]["tools"]


def test_goals_tools_exist():
    data = json.loads(MOCK_FILE.read_text())
    tools = data["servers"]["career-data"]["tools"]
    assert "list_goal_plans" in tools
    assert "list_goals" in tools
    assert "list_development_goals" in tools


def test_goal_plan_state_has_plan_name():
    tools = load_tools()
    results = tools["list_goal_plans"]["mock_response"]["results"]
    assert len(results) > 0
    for item in results:
        assert "planName" in item
        assert "state" in item


def test_goals_in_template_have_name_and_status():
    tools = load_tools()
    results = tools["list_goals"]["mock_response"]["results"]
    assert len(results) > 0
    for goal in results:
        assert "name" in goal, "Goal must have a name"
        assert "status" in goal, "Goal must have a status"
    statuses = {g["status"] for g in results}
    # "On Track" is a valid DEMOCO status (G-100045-2: Earn SAP Analytics Cloud certification)
    assert statuses.issubset({"In Progress", "On Track", "Completed", "Not Started", "Missed"}), \
        f"Unexpected goal statuses: {statuses}"


def test_completed_goal_exists_in_mock():
    tools = load_tools()
    results = tools["list_goals"]["mock_response"]["results"]
    completed = [g for g in results if g["status"] == "Completed"]
    assert len(completed) >= 1, "At least one completed goal should exist for a meaningful career story"


def test_no_compensation_in_goals_response():
    tools = load_tools()
    for tool_name, tool in tools.items():
        response_str = json.dumps(tool.get("mock_response", {})).lower()
        for term in ["salary", "pay grade", "bonus", "equity"]:
            assert term not in response_str, \
                f"Compensation term '{term}' found in goals mock tool '{tool_name}'"
