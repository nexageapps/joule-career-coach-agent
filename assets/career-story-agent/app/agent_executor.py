import logging

from langchain_core.messages import SystemMessage
from langchain_core.messages.utils import count_tokens_approximately

from a2a.server.agent_execution import AgentExecutor as A2AAgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent import SampleAgent
from datetime_tool import get_datetime_tool
from load_skill_resources import get_load_skill_resource_tool
from mcp_providers.agw import get_mcp_tools
from prompt_injection_detector import wrap_tool

logger = logging.getLogger(__name__)

# Focused tool allow-list for career story generation.
# Keeping only the handful of tools the agent actually needs limits the token
# overhead (tool schemas in the LLM context) and prevents the model from
# attempting unnecessary API calls that would inflate response time.
_CAREER_TOOL_ALLOWLIST: tuple[str, ...] = (
    # Employee profile & job info
    "get_employee_profile",
    "get_job_info",
    "list_work_experience",
    "list_awards",
    "list_badges",
    # Skills & role gaps
    "list_skills",
    "list_role_skills",
    # Goals
    "list_goal_plans",
    "list_goals",
    "list_development_goals",
    # Performance reviews
    "get_performance_review",
    # Learning & certifications
    "list_certifications",
    "list_learning",
    "list_achievements",
)


def _select_career_tools(tools):
    """Return the focused subset of MCP tools needed for career story generation.

    Filters the full tool list to only the tools in _CAREER_TOOL_ALLOWLIST,
    reducing LLM context size and preventing unnecessary API calls.
    Falls back to the full list if fewer than 3 allowlisted tools are found
    (e.g. a production server with different tool names).
    """
    selected = [t for t in tools if t.name in _CAREER_TOOL_ALLOWLIST]
    if len(selected) < 3:
        logger.warning(
            "_select_career_tools: only %d allowlisted tools found — falling back to full list (%d tools)",
            len(selected), len(tools),
        )
        return tools
    return selected


class AgentExecutor(A2AAgentExecutor):
    def __init__(self):
        self.agent = SampleAgent()
        self.skill_tools = [get_datetime_tool(), *get_load_skill_resource_tool()]

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the agent and stream results back via A2A protocol.

        Discovers and loads MCP tools from Agent Gateway before each execution.
        The user token is read from the context var set by JWTContextMiddleware.

        Args:
            context: Request context containing user input and task info
            event_queue: Queue for publishing task status updates

        Raises:
            ServerError: On unrecoverable agent execution errors
        """
        query = context.get_user_input()
        task = context.current_task
        if not task:
            assert context.message is not None, "Cannot create task without a message"
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Load MCP tools — user token is read from context var set by JWTContextMiddleware
        tools = []
        try:
            raw_tools = await get_mcp_tools()
            if not raw_tools:
                logger.warning("No tools returned from Agent Gateway")
            else:
                tools = _select_career_tools(raw_tools)
                logger.info(
                    "Filtered MCP tools: %d → %d (career story subset)",
                    len(raw_tools), len(tools),
                )
        except Exception as e:
            logger.error(f"Failed to load tools from Agent Gateway: {e}")

        tools = [*tools, *self.skill_tools]

        # Wrap all tools with prompt injection scanning for uniform protection
        tools = [wrap_tool(t) for t in tools]

        from agent import get_system_prompt
        _system_prompt = get_system_prompt()
        _msg_tokens = count_tokens_approximately([SystemMessage(content=_system_prompt)])
        _total_tokens = count_tokens_approximately([SystemMessage(content=_system_prompt)], tools=list(tools))
        logger.info(
            "Loaded %d tool(s); token estimate — prompt: %d, tools: %d, total: %d",
            len(tools), _msg_tokens, _total_tokens - _msg_tokens, _total_tokens,
        )

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query, task.context_id, tools=tools):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                content = item["content"]

                if require_user_input:
                    # Agent requests more input
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(content, task.context_id, task.id),
                        final=True,
                    )
                    break
                elif is_task_complete:
                    # Completed: add artifact and complete task
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))], name="agent_result"
                    )
                    await updater.complete()
                    break
                else:
                    # Working status update
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(content, task.context_id, task.id),
                    )
        except Exception as e:
            logger.exception("Agent execution error")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
