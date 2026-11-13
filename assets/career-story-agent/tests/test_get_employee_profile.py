"""Unit test for the employee profile mock tools.

Asserts profile fields are present and compensation fields are absent.
"""
import json
from pathlib import Path

import pytest

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"
COMPENSATION_TERMS = [
    "salary", "pay grade", "paygrade", "bonus", "equity",
    "stock", "reward", "compensation", "total_rewards", "totalrewards",
]


def load_mock():
    return json.loads(MOCK_FILE.read_text())


def load_tools():
    return load_mock()["servers"]["career-data"]["tools"]


def test_career_data_server_exists():
    data = load_mock()
    assert "career-data" in data["servers"], "career-data server must be present in mcp-mock.json"


def test_public_profile_tool_returns_expected_fields():
    tools = load_tools()
    assert "get_employee_profile" in tools
    mock_resp = tools["get_employee_profile"]["mock_response"]
    for field in ["userId", "firstName", "lastName", "title", "department", "location", "hireDate"]:
        assert field in mock_resp, f"Profile response must include '{field}'"


def test_profile_is_jane_smith_democo():
    """Mock data must use the DEMOCO demo employee Jane Smith."""
    tools = load_tools()
    mock_resp = tools["get_employee_profile"]["mock_response"]
    assert mock_resp["userId"] == "100045"
    assert mock_resp["firstName"] == "Jane"
    assert mock_resp["lastName"] == "Smith"
    assert mock_resp["title"] == "Finance Analyst"
    assert mock_resp["location"] == "New York"
    assert mock_resp["managerId"] == "100001"
    assert mock_resp["hireDate"] == "2021-06-14"


def test_profile_response_contains_no_compensation_data():
    tools = load_tools()
    for tool_name, tool in tools.items():
        response_str = json.dumps(tool.get("mock_response", {})).lower()
        for term in COMPENSATION_TERMS:
            if "compensation" in tool_name:
                pytest.fail(f"Compensation tool '{tool_name}' found — it must be excluded")
            assert term not in response_str, \
                f"Compensation term '{term}' found in mock response for tool '{tool_name}'"


def test_awards_tool_present():
    """list_awards must exist and return a results list.
    DEMOCO Jane Smith has no formal awards (recognition is captured as achievements)
    so an empty results list is correct."""
    tools = load_tools()
    assert "list_awards" in tools
    mock_resp = tools["list_awards"]["mock_response"]
    assert "results" in mock_resp
    # DEMOCO has no awards — empty list is correct; if present must have awardName
    for award in mock_resp["results"]:
        assert "awardName" in award, "Award entry must have an awardName"


def test_work_experience_tool_present():
    tools = load_tools()
    assert "list_work_experience" in tools
    results = tools["list_work_experience"]["mock_response"]["results"]
    assert len(results) > 0
    assert "title" in results[0]
    assert "department" in results[0]
