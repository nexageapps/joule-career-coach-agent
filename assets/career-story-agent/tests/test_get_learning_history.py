"""Unit test for the learning history mock tools.

Asserts course name and completion date are returned.
"""
import json
from pathlib import Path

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def load_tools():
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"]["career-data"]["tools"]


def test_learning_tools_exist():
    data = json.loads(MOCK_FILE.read_text())
    tools = data["servers"]["career-data"]["tools"]
    assert "list_learning" in tools
    assert "list_certifications" in tools


def test_dev_learning_has_course_name():
    tools = load_tools()
    results = tools["list_learning"]["mock_response"]["results"]
    assert len(results) > 0
    for item in results:
        assert "courseName" in item, "Learning item must have a courseName"
        assert "status" in item, "Learning item must have a status"


def test_certifications_tool_present():
    """DEMOCO: Jane has exactly 1 certification (SAP Analytics Cloud, In Progress)."""
    tools = load_tools()
    results = tools["list_certifications"]["mock_response"]["results"]
    assert len(results) == 1
    cert = results[0]
    assert cert["certId"] == "CERT-SAC-100045"
    assert cert["name"] == "SAP Analytics Cloud"
    assert cert["status"] == "In Progress"


def test_learning_has_four_courses():
    """DEMOCO: Jane has exactly 4 learning courses."""
    tools = load_tools()
    results = tools["list_learning"]["mock_response"]["results"]
    assert len(results) == 4, f"Expected 4 learning courses, got {len(results)}"


def test_learning_has_overdue_filter_metadata():
    """list_learning must carry overdueFilter metadata showing 0 overdue, source count 4."""
    tools = load_tools()
    mock_resp = tools["list_learning"]["mock_response"]
    assert "overdueFilter" in mock_resp, "overdueFilter metadata must be present"
    od = mock_resp["overdueFilter"]
    assert od["count"] == 0, "No overdue activities expected"
    assert od["activities"] == [], "Overdue activities list must be empty"


def test_learning_courses_match_democo_facts():
    """Learning course IDs and statuses must match DEMOCO specification."""
    tools = load_tools()
    results = tools["list_learning"]["mock_response"]["results"]
    id_map = {c["learningId"]: c for c in results}
    assert "LMS-FIN-201" in id_map
    assert id_map["LMS-FIN-201"]["status"] == "Completed"
    assert id_map["LMS-FIN-201"]["completedDate"] == "2025-12-05"
    assert "LMS-SAC-110" in id_map
    assert id_map["LMS-SAC-110"]["status"] == "Completed"
    assert "LMS-LEAD-101" in id_map
    assert id_map["LMS-LEAD-101"]["status"] == "In Progress"
    assert id_map["LMS-LEAD-101"]["completedDate"] is None
    assert "LMS-COC-2026" in id_map
    assert id_map["LMS-COC-2026"]["status"] == "Completed"
    assert id_map["LMS-COC-2026"]["mandatory"] is True
