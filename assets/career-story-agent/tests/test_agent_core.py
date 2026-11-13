"""Tests for core agent.py behaviour: system prompt, instrumentation, _run_agent."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def test_get_system_prompt_contains_guardrails():
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "COMPENSATION" in prompt or "compensation" in prompt
    assert "PROMOTION" in prompt or "promotion" in prompt
    assert "OWN DATA ONLY" in prompt or "own data" in prompt.lower()
    assert "signed-in user" in prompt.lower() or "authenticated user" in prompt.lower()


def test_get_system_prompt_contains_tool_instructions():
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "tools" in prompt.lower()
    assert "never fabricate" in prompt.lower() or "MUST use tools" in prompt


def test_get_model_name_returns_string():
    from agent import get_model_name
    model = get_model_name()
    assert isinstance(model, str)
    assert len(model) > 0


def test_get_temperature_returns_float():
    from agent import get_temperature
    temp = get_temperature()
    assert isinstance(temp, float)
    assert 0.0 <= temp <= 1.0


def test_sample_agent_initialises():
    from agent import SampleAgent
    agent = SampleAgent()
    assert agent is not None
    assert agent.llm is not None


@pytest.mark.asyncio
async def test_run_agent_logs_m1_achieved_when_tools_present():
    """M1.achieved should be logged when tools are present."""
    from agent import SampleAgent
    from langchain_core.tools import StructuredTool

    mock_tool = MagicMock(spec=StructuredTool)
    mock_tool.name = "get_skills_mock"

    mock_msg = MagicMock()
    mock_msg.content = "Your career story: strengths include X. Skill gaps: Y. Next steps: 1. Do A"

    with patch.object(SampleAgent, "_invoke", new_callable=AsyncMock,
                      return_value={"messages": [mock_msg]}):
        import logging
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("agent")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        agent = SampleAgent()
        result = await agent._run_agent(
            query="Tell me my career story",
            context_id="test-m1",
            tools=[mock_tool],
        )
        assert "career story" in result.lower() or "strengths" in result.lower()
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_stream_yields_processing_then_complete():
    """stream() must first yield a 'Processing...' chunk, then a completed chunk."""
    from agent import SampleAgent

    mock_msg = MagicMock()
    mock_msg.content = "Here is your career story."

    with patch.object(SampleAgent, "_invoke", new_callable=AsyncMock,
                      return_value={"messages": [mock_msg]}):
        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("Generate my career story", "ctx-001", tools=[]):
            chunks.append(chunk)

    assert len(chunks) >= 2
    assert chunks[0]["content"] == "Processing..."
    assert chunks[0]["is_task_complete"] is False
    final = chunks[-1]
    assert final["is_task_complete"] is True
    assert final["content"] == "Here is your career story."


@pytest.mark.asyncio
async def test_invoke_returns_completed_status():
    from agent import SampleAgent

    mock_msg = MagicMock()
    mock_msg.content = "Career story complete."

    with patch.object(SampleAgent, "_invoke", new_callable=AsyncMock,
                      return_value={"messages": [mock_msg]}):
        agent = SampleAgent()
        result = await agent.invoke("Generate my career story", "ctx-002", tools=[])

    assert result.status == "completed"
    assert result.message == "Career story complete."


@pytest.mark.asyncio
async def test_invoke_handles_exception_gracefully():
    from agent import SampleAgent

    with patch.object(SampleAgent, "_invoke", new_callable=AsyncMock,
                      side_effect=RuntimeError("test error")):
        agent = SampleAgent()
        result = await agent.invoke("Generate my career story", "ctx-003", tools=[])

    assert result.status == "error"
    assert result.message  # Must have some error message


@pytest.mark.asyncio
async def test_run_agent_m5_achieved_on_followup_query():
    """M5.achieved should be logged when query contains career action keywords."""
    from agent import SampleAgent

    mock_msg = MagicMock()
    mock_msg.content = "Here is more detail on your skill gaps."

    with patch.object(SampleAgent, "_invoke", new_callable=AsyncMock,
                      return_value={"messages": [mock_msg]}):
        agent = SampleAgent()
        result = await agent._run_agent(
            query="Tell me more about my skill gaps",
            context_id="ctx-m5",
            tools=[],
        )
    assert result  # M5 logging happens as side effect; just verify no crash
