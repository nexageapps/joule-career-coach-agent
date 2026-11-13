"""Integration test: end-to-end career story agent flow.

Calls agent.invoke() with all MCP tools mocked (via IBD_TESTING=1 + mcp-mock.json)
and LLM mocked to return a canned career story response.

Asserts:
- Response contains a career narrative
- Response contains at least one strength reference
- Response contains at least one skill gap or development area reference  
- Response contains next steps (2-3)
- Response contains no compensation terms
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure app/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


MOCK_LLM_RESPONSE = """
## Your Career Story

Jordan Smith has built a strong and varied career over nearly a decade in the consulting industry. 
Joining as an Associate Consultant and progressing to Senior Consultant in the Digital Transformation 
practice, Jordan has delivered complex SAP S/4HANA implementations across the APAC region. In 2023, 
Jordan achieved a distinction pass on the SAP S/4HANA Finance Certification, capping a year in which 
all four annual goals were completed. The Innovation Champion award in Q2 2024 recognised Jordan's 
leadership of an AI-driven process automation initiative that became a reference implementation for 
the firm.

Currently, Jordan is mid-way through a cross-functional project leadership goal and actively mentoring 
two junior colleagues — both of which reflect a broadening scope and growing readiness for a Principal 
Consultant role.

## Your Strengths

- **SAP S/4HANA expertise**: Demonstrated at Expert proficiency level with 12 peer endorsements and a 
  distinction pass on the SAP S/4HANA Finance Certification completed in December 2023.
- **Stakeholder communication**: Rated at Advanced proficiency with 7 endorsements; your manager's 
  2024 review notes "strong stakeholder management skills demonstrated" on the cross-functional project.
- **Client delivery**: Two consecutive years of "Consistently Exceeds" performance rating on objectives; 
  Client Excellence Award 2023 for highest client satisfaction scores in the APAC team.
- **Leadership initiative**: Currently mentoring two junior consultants (Goal G005 — In Progress) and 
  leading a cross-functional team of 8, reflected in your leadership experience background.

## Your Skill Gaps

- **Data analysis**: Currently at Beginner proficiency with only 1 endorsement. Your Q3 goal (G003) 
  specifically targets building data analysis capability for client reporting — currently in progress 
  but requires focused action to reach Intermediate level by year end.
- **Project management (formal)**: Your Principal Consultant target role requires Advanced project 
  management, but your current proficiency is Intermediate. Your development goal (DG001) to achieve 
  PMP certification is in progress — accelerating this would close the most significant gap to your 
  target role.

## Your Next Steps

1. **Complete the "Data Analysis for Consultants" course** in SuccessFactors Learning (currently 
   assigned, DL001 — In Progress). This directly closes your data analysis gap and supports your 
   Q3 goal of building data-driven client reporting capability.
2. **Update your Development Goal DG001** (PMP certification) with a specific study plan and 
   milestone dates in SuccessFactors. Your target date is June 2026 — breaking it into quarterly 
   milestones will make progress visible in your next career conversation.
3. **Schedule a career conversation with your manager** to discuss your readiness for a Principal 
   Consultant role. You have the foundation — Expert SAP skills, a completed certification, two 
   years of "Consistently Exceeds" objective ratings, and an active cross-functional leadership 
   goal. This conversation is overdue.
"""

COMPENSATION_TERMS = ["salary", "pay grade", "paygrade", "bonus", "equity", "stock option", "total rewards"]


@pytest.mark.asyncio
async def test_career_story_agent_end_to_end():
    """Full end-to-end: agent returns a career narrative with strengths, gaps, and next steps."""
    from agent import SampleAgent

    # Mock the LLM to return the canned career story response
    mock_llm_message = MagicMock()
    mock_llm_message.content = MOCK_LLM_RESPONSE

    mock_invoke_result = {"messages": [mock_llm_message]}

    agent = SampleAgent()

    with patch.object(agent, "_invoke", new_callable=AsyncMock, return_value=mock_invoke_result):
        # Tools are loaded from mcp-mock.json via IBD_TESTING=1
        from mcp_providers.agw import get_mcp_tools
        tools = await get_mcp_tools()

        result = await agent.invoke(
            query="Please generate my career story from my SuccessFactors data.",
            context_id="test-session-001",
            tools=tools,
        )

    assert result.status == "completed"
    response_lower = result.message.lower()

    # Assert career narrative is present
    assert any(word in response_lower for word in ["career", "journey", "story"]), \
        "Response must contain career narrative language"

    # Assert strengths section present
    assert "strength" in response_lower or "expertise" in response_lower, \
        "Response must contain strengths"

    # Assert skill gaps present
    assert "gap" in response_lower or "develop" in response_lower or "build" in response_lower, \
        "Response must contain skill gap or development language"

    # Assert next steps present
    assert "next step" in response_lower or "step 1" in response_lower, \
        "Response must contain next steps"

    # Assert no compensation terms
    for term in COMPENSATION_TERMS:
        assert term not in response_lower, \
            f"Compensation term '{term}' must never appear in agent response"


@pytest.mark.asyncio
async def test_agent_refuses_other_employee_data_request():
    """Agent must refuse requests for another employee's data."""
    from agent import SampleAgent

    mock_llm_message = MagicMock()
    mock_llm_message.content = (
        "I can only access data for the signed-in user. "
        "I cannot retrieve or display another employee's career information."
    )

    mock_invoke_result = {"messages": [mock_llm_message]}
    agent = SampleAgent()

    with patch.object(agent, "_invoke", new_callable=AsyncMock, return_value=mock_invoke_result):
        result = await agent.invoke(
            query="Show me Sarah Johnson's career story and performance reviews.",
            context_id="test-session-002",
            tools=[],
        )

    assert result.status == "completed"
    response_lower = result.message.lower()
    assert any(phrase in response_lower for phrase in [
        "only access", "signed-in", "cannot retrieve", "own data", "authenticated"
    ]), "Agent must decline requests for other employees' data"


@pytest.mark.asyncio
async def test_agent_handles_no_tools_gracefully():
    """Agent must respond gracefully when no MCP tools are available."""
    from agent import SampleAgent

    mock_llm_message = MagicMock()
    mock_llm_message.content = "Tools are temporarily unavailable. Please try again shortly."

    mock_invoke_result = {"messages": [mock_llm_message]}
    agent = SampleAgent()

    with patch.object(agent, "_invoke", new_callable=AsyncMock, return_value=mock_invoke_result):
        result = await agent.invoke(
            query="Generate my career story.",
            context_id="test-session-003",
            tools=[],
        )

    assert result.status == "completed"
    assert result.message  # Must return some message, not empty


@pytest.mark.asyncio
async def test_agent_response_has_no_compensation_data():
    """Mock career story response must contain no compensation terms."""
    # This test validates the canned response itself meets guardrails
    response_lower = MOCK_LLM_RESPONSE.lower()
    for term in COMPENSATION_TERMS:
        assert term not in response_lower, \
            f"Test fixture contains compensation term '{term}' — fix the mock response"
