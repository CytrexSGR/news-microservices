"""Brain Node - Main reasoning and response generation."""

import json
from typing import List

from app.agent.state import AgentState, ToolCall
from app.llm.openai_client import get_openai_client
from app.llm.prompts import BRAIN_RESPONSE_PROMPT, format_tool_selection_prompt
from app.tools import get_tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


async def brain_node(state: AgentState) -> dict:
    """
    Generate a response or select tools based on the classified intent.

    Phase 2: Supports tool selection when requires_tools=True.
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "final_response": "Ich habe keine Nachricht erhalten. Wie kann ich dir helfen?",
            "current_node": "brain",
            "confidence": 0.5,
        }

    last_message = messages[-1].content
    intent = state.get("intent", "simple_query")
    requires_tools = state.get("requires_tools", False)
    tools_executed = state.get("tools_executed", False)

    client = get_openai_client()

    # Phase 2: Tool selection path
    if requires_tools and not tools_executed:
        return await _select_tools(state, client, last_message, intent)

    # Direct response path (no tools needed or tools already executed)
    return await _generate_response(state, client, last_message, intent)


async def _select_tools(state: AgentState, client, message: str, intent: str) -> dict:
    """Select appropriate tools for the task."""
    try:
        registry = get_tool_registry()
        tool_descriptions = registry.get_tool_descriptions()

        # Format the tool selection prompt
        system_prompt = format_tool_selection_prompt(tool_descriptions)

        response, tokens = await client.invoke(
            system_prompt=system_prompt,
            user_message=message,
        )

        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            json_lines = [l for l in lines if not l.startswith("```")]
            response_clean = "\n".join(json_lines)

        result = json.loads(response_clean)

        tool_calls: List[ToolCall] = result.get("tool_calls", [])
        can_answer_directly = result.get("can_answer_directly", False)

        logger.info(
            "brain_tool_selection",
            tool_count=len(tool_calls),
            can_answer_directly=can_answer_directly,
            reasoning=result.get("reasoning", "")[:100],
        )

        # If can answer directly, skip tools
        if can_answer_directly or not tool_calls:
            return {
                "tool_calls": [],
                "requires_tools": False,
                "tools_executed": True,
                "current_node": "brain",
                "tokens_used": state.get("tokens_used", 0) + tokens,
            }

        return {
            "tool_calls": tool_calls,
            "current_node": "brain",
            "tokens_used": state.get("tokens_used", 0) + tokens,
        }

    except json.JSONDecodeError as e:
        logger.warning("brain_tool_selection_parse_error", error=str(e))
        # Fall back to no tools
        return {
            "tool_calls": [],
            "requires_tools": False,
            "tools_executed": True,
            "current_node": "brain",
            "error": f"Tool selection parse error: {e}",
        }
    except Exception as e:
        logger.error("brain_tool_selection_error", error=str(e))
        return {
            "tool_calls": [],
            "requires_tools": False,
            "tools_executed": True,
            "current_node": "brain",
            "error": str(e),
        }


async def _generate_response(state: AgentState, client, message: str, intent: str) -> dict:
    """Generate a response, incorporating tool results if available."""
    from app.agent.nodes.tools import format_tool_results_for_llm

    try:
        # Build context with tool results if available
        tool_results = state.get("tool_results", [])
        context_parts = [
            f"Intent: {intent}",
            f"User Message: {message}",
        ]

        if tool_results:
            tool_context = format_tool_results_for_llm(tool_results)
            context_parts.append(f"\n{tool_context}")
            context_parts.append(
                "\nUse the tool results above to provide a comprehensive answer."
            )
        else:
            context_parts.append("\nRespond appropriately based on the intent.")

        context = "\n".join(context_parts)

        response, tokens = await client.invoke(
            system_prompt=BRAIN_RESPONSE_PROMPT,
            user_message=context,
        )

        logger.info(
            "brain_response_generated",
            intent=intent,
            tokens=tokens,
            response_length=len(response),
            had_tool_results=bool(tool_results),
        )

        return {
            "final_response": response,
            "current_node": "brain",
            "confidence": 0.8 if tool_results else 0.7,
            "tokens_used": state.get("tokens_used", 0) + tokens,
        }

    except Exception as e:
        logger.error("brain_response_error", error=str(e))
        return {
            "final_response": "Entschuldigung, es gab einen Fehler bei der Verarbeitung. Bitte versuche es erneut.",
            "current_node": "brain",
            "confidence": 0.0,
            "error": str(e),
        }
