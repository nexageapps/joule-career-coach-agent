"""Unit tests for agent guardrails.

Tests that:
1. Compensation-related terms never appear in mock response data
2. The agent's system prompt contains the required guardrail instructions
3. The runtime skill SKILL.md contains guardrail rules
"""
import json
import os
from pathlib import Path

import pytest

MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"
AGENT_FILE = Path(__file__).parent.parent / "app" / "agent.py"
SKILL_FILE = Path(__file__).parent.parent / "app" / "skills" / "career-story" / "SKILL.md"

COMPENSATION_TERMS = [
    "salary",
    "paygrade",
    "pay grade",
    "bonus amount",
    "equity grant",
    "stock option",
    "total_rewards",
    "compensation package",
]

OWN_DATA_INDICATORS = [
    "own data",
    "own information",
    "signed-in user",
    "authenticated user",
]

PROMOTION_PROMISE_INDICATORS = [
    "never state",
    "never imply",
    "never predict",
    "promotion",
    "performance rating",
    "career guarantee",
]


def test_no_compensation_data_in_any_mock_response():
    """Compensation data must never appear in any mock response across all servers."""
    data = json.loads(MOCK_FILE.read_text())
    for server_slug, server in data["servers"].items():
        for tool_name, tool in server["tools"].items():
            response_str = json.dumps(tool.get("mock_response", {})).lower()
            for term in COMPENSATION_TERMS:
                assert term not in response_str, (
                    f"Compensation term '{term}' found in mock response for "
                    f"server '{server_slug}', tool '{tool_name}'"
                )


def test_system_prompt_contains_compensation_guardrail():
    """Agent system prompt must explicitly prohibit compensation data."""
    agent_code = AGENT_FILE.read_text()
    assert "compensation" in agent_code.lower() or "COMPENSATION" in agent_code, \
        "System prompt must contain compensation guardrail"
    assert "salary" in agent_code.lower() or "pay grade" in agent_code.lower(), \
        "System prompt must name specific compensation data types"


def test_system_prompt_contains_own_data_guardrail():
    """Agent system prompt must enforce own-data-only access."""
    agent_code = AGENT_FILE.read_text()
    agent_code_lower = agent_code.lower()
    found = any(indicator in agent_code_lower for indicator in OWN_DATA_INDICATORS)
    assert found, (
        "System prompt must contain own-data-only guardrail. "
        f"Expected one of: {OWN_DATA_INDICATORS}"
    )


def test_system_prompt_contains_no_promotion_promise_guardrail():
    """Agent system prompt must prohibit promotion/performance promises."""
    agent_code = AGENT_FILE.read_text()
    agent_code_lower = agent_code.lower()
    assert "promotion" in agent_code_lower, \
        "System prompt must reference promotion promise prohibition"


def test_skill_md_exists():
    """Runtime career story SKILL.md must exist."""
    assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"


def test_skill_md_contains_guardrails():
    """SKILL.md must contain embedded guardrail rules."""
    skill_content = SKILL_FILE.read_text().lower()
    assert "compensation" in skill_content, "SKILL.md must contain compensation guardrail"
    assert "promotion" in skill_content, "SKILL.md must contain promotion guardrail"
    assert "own data" in skill_content or "signed-in" in skill_content, \
        "SKILL.md must contain own-data-only guardrail"


def test_skill_md_specifies_next_steps_count():
    """SKILL.md must specify exactly 2-3 next steps."""
    skill_content = SKILL_FILE.read_text()
    assert "2-3" in skill_content or "2–3" in skill_content, \
        "SKILL.md must specify exactly 2-3 next steps"


def test_no_compensation_tool_in_pruned_mock():
    """Background compensation tool must not be present in pruned mock (it was excluded)."""
    data = json.loads(MOCK_FILE.read_text())
    for server_slug, server in data["servers"].items():
        for tool_name in server["tools"]:
            assert "background_compensation" not in tool_name, (
                f"Compensation background tool '{tool_name}' should not be in pruned mock"
            )
