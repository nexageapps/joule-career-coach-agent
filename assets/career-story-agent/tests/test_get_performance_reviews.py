"""Unit test for the performance review mock tool.

Asserts narrative/comments are returned and no raw compensation data appears.
"""
import json
from pathlib import Path

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def load_tools():
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"]["career-data"]["tools"]


def test_performance_review_tool_exists():
    data = json.loads(MOCK_FILE.read_text())
    assert "get_performance_review" in data["servers"]["career-data"]["tools"]


def test_get_review_has_steps():
    tools = load_tools()
    assert "get_performance_review" in tools
    mock_resp = tools["get_performance_review"]["mock_response"]
    assert "steps" in mock_resp, "Review response must include steps"
    assert len(mock_resp["steps"]) > 0


def test_review_manager_step_has_exact_democo_comments():
    """Manager comments must match exact DEMOCO specification text."""
    tools = load_tools()
    mock_resp = tools["get_performance_review"]["mock_response"]
    manager_step = next((s for s in mock_resp["steps"] if "Manager" in s.get("stepName", "")), None)
    assert manager_step is not None, "Manager review step must exist"
    assert manager_step["comments"] == (
        "Consistently reliable close ownership and a standout reporting automation project."
    ), "Manager comments must match exact DEMOCO text"


def test_review_response_has_no_compensation():
    tools = load_tools()
    for tool_name, tool in tools.items():
        response_str = json.dumps(tool.get("mock_response", {})).lower()
        for term in ["salary", "pay grade", "paygrade", "bonus", "equity", "stock option"]:
            assert term not in response_str, \
                f"Compensation term '{term}' found in performance review tool '{tool_name}'"


def test_review_has_review_period():
    tools = load_tools()
    mock_resp = tools["get_performance_review"]["mock_response"]
    assert "reviewPeriod" in mock_resp, "Review must have a reviewPeriod"


def test_review_matches_democo_facts():
    """Latest review must be PR-2025-100045 with rating 4.0 / Exceeds Expectations."""
    tools = load_tools()
    mock_resp = tools["get_performance_review"]["mock_response"]
    assert mock_resp["reviewId"] == "PR-2025-100045"
    assert mock_resp["reviewPeriod"] == "2025"
    assert mock_resp["rating"] == 4.0
    assert mock_resp["overallRating"] == "Exceeds Expectations"
    assert mock_resp["reviewCount"] == 2


def test_review_previous_review_matches_democo_facts():
    """Previous review must be PR-2024-100045 with rating 3.5 / Meets Expectations."""
    tools = load_tools()
    mock_resp = tools["get_performance_review"]["mock_response"]
    prev = mock_resp["previousReviews"]
    assert len(prev) == 1
    assert prev[0]["reviewId"] == "PR-2024-100045"
    assert prev[0]["rating"] == 3.5
    assert prev[0]["overallRating"] == "Meets Expectations"
    assert prev[0]["summary"] == "Solid core delivery; ready to lead small automation initiatives."


def test_review_no_promotion_implication_in_manager_comments():
    """Manager comments must describe skills/work only — no promotion implication."""
    tools = load_tools()
    mock_resp = tools["get_performance_review"]["mock_response"]
    manager_step = next((s for s in mock_resp["steps"] if "Manager" in s.get("stepName", "")), None)
    comments_lower = manager_step["comments"].lower()
    forbidden = ["potential", "ready for", "promote", "promotion", "senior", "step up", "next level"]
    for phrase in forbidden:
        assert phrase not in comments_lower, (
            f"Manager comments must not contain promotion implication '{phrase}'"
        )
