"""Unit test for the skills mock tools.

Asserts skill name and proficiency level are returned and no compensation data leaks.
"""
import json
from pathlib import Path

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def load_tools():
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"]["career-data"]["tools"]


def test_career_data_server_has_skills_tools():
    data = json.loads(MOCK_FILE.read_text())
    assert "career-data" in data["servers"]
    tools = data["servers"]["career-data"]["tools"]
    assert "list_skills" in tools, "list_skills tool must be present"
    assert "list_role_skills" in tools, "list_role_skills tool must be present"


def test_jane_smith_has_four_skills():
    """DEMOCO: Jane Smith must have exactly 4 skills."""
    tools = load_tools()
    results = tools["list_skills"]["mock_response"]["results"]
    assert len(results) == 4, f"Expected 4 skills for Jane Smith, got {len(results)}"


def test_jane_skills_match_democo_facts():
    """Skills must exactly match DEMOCO specification."""
    tools = load_tools()
    results = tools["list_skills"]["mock_response"]["results"]
    skill_map = {s["skillName"]: s for s in results}
    assert "Financial Analysis" in skill_map
    assert skill_map["Financial Analysis"]["proficiencyLevel"] == "Advanced"
    assert "FP&A Modelling" in skill_map
    assert skill_map["FP&A Modelling"]["proficiencyLevel"] == "Advanced"
    assert "SAP Analytics Cloud" in skill_map
    assert skill_map["SAP Analytics Cloud"]["proficiencyLevel"] == "Intermediate"
    assert "Data Storytelling" in skill_map
    assert skill_map["Data Storytelling"]["proficiencyLevel"] == "Beginner"


def test_rated_skill_mapping_has_proficiency_level():
    tools = load_tools()
    assert "list_skills" in tools
    results = tools["list_skills"]["mock_response"]["results"]
    assert len(results) > 0
    for item in results:
        assert "skillId" in item, "Each skill must have skillId"
        assert "skillName" in item, "Each skill must have skillName"
        assert "proficiencyLevel" in item, "Each skill must have proficiencyLevel"
        assert "addedDate" in item, "Each skill must have addedDate"


def test_skill_entity_has_name_and_proficiency():
    tools = load_tools()
    results = tools["list_skills"]["mock_response"]["results"]
    assert len(results) > 0
    for item in results:
        assert "skillName" in item
        assert "proficiencyLevel" in item


def test_role_skills_tool_exists():
    tools = load_tools()
    assert "list_role_skills" in tools
    mock_resp = tools["list_role_skills"]["mock_response"]
    assert "results" in mock_resp


def test_no_compensation_in_skills_response():
    tools = load_tools()
    for tool_name, tool in tools.items():
        response_str = json.dumps(tool.get("mock_response", {})).lower()
        for term in ["salary", "pay grade", "bonus", "equity", "total_rewards"]:
            assert term not in response_str, \
                f"Compensation term '{term}' found in skills mock tool '{tool_name}'"
