"""Response Node - Final response formatting."""

from app.agent.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def response_node(state: AgentState) -> dict:
    """
    Format the final response for output.

    This node prepares the response for the API.
    Phase 2: Includes tool execution metadata.
    """
    final_response = state.get("final_response", "")

    if not final_response:
        final_response = "Ich konnte keine Antwort generieren. Bitte versuche es erneut."

    # Collect tool execution info
    tool_results = state.get("tool_results", [])
    tools_used = [r.get("tool_name") for r in tool_results if r.get("success")]

    logger.info(
        "response_formatted",
        response_length=len(final_response),
        tokens_used=state.get("tokens_used", 0),
        tools_used=tools_used,
        tools_executed=state.get("tools_executed", False),
    )

    return {
        "final_response": final_response,
        "current_node": "response",
    }
