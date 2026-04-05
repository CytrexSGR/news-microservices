"""Planner Node - Decomposes complex requests into execution plans."""

import json
from typing import Dict, Any

from app.agent.state import AgentState, ExecutionPlan
from app.llm.openai_client import get_openai_client
from app.llm.prompts import PLANNER_PROMPT
from app.tools import get_tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_tool_descriptions() -> str:
    """Get formatted tool descriptions for the prompt."""
    registry = get_tool_registry()
    tools = registry.list_tools()
    descriptions = []
    for tool_name in tools:
        tool = registry.get(tool_name)
        if tool:
            descriptions.append(f"- {tool.name}: {tool.description}")
    return "\n".join(descriptions)


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate an execution plan for complex requests.

    Returns updated state with:
    - pending_plan: The generated execution plan
    - requires_planning: True (confirmed)
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "pending_plan": None,
            "requires_planning": False,
            "current_node": "planner",
            "error": "No message to plan for",
        }

    last_message = messages[-1].content
    tool_descriptions = _get_tool_descriptions()

    # Format prompt with tool descriptions
    formatted_prompt = PLANNER_PROMPT.replace("{tool_descriptions}", tool_descriptions)

    client = get_openai_client()

    try:
        response, tokens = await client.invoke(
            system_prompt=formatted_prompt,
            user_message=f"Erstelle einen Ausführungsplan für: {last_message}",
        )

        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            json_lines = [l for l in lines if not l.startswith("```")]
            response_clean = "\n".join(json_lines)

        plan_data = json.loads(response_clean)

        # Validate plan structure
        plan: ExecutionPlan = {
            "goal": plan_data.get("goal", last_message),
            "steps": plan_data.get("steps", []),
            "estimated_tools": plan_data.get("estimated_tools", len(plan_data.get("steps", []))),
            "complexity": plan_data.get("complexity", "medium"),
        }

        logger.info(
            "planner_created_plan",
            goal=plan["goal"],
            steps=len(plan["steps"]),
            complexity=plan["complexity"],
        )

        return {
            "pending_plan": plan,
            "requires_planning": True,
            "plan_confirmed": False,
            "plan_cancelled": False,
            "current_node": "planner",
            "tokens_used": state.get("tokens_used", 0) + tokens,
        }

    except json.JSONDecodeError as e:
        logger.warning("planner_json_parse_error", error=str(e))
        return {
            "pending_plan": None,
            "requires_planning": False,
            "current_node": "planner",
            "error": f"Plan generation failed: {e}",
        }
    except Exception as e:
        logger.error("planner_error", error=str(e))
        return {
            "pending_plan": None,
            "requires_planning": False,
            "current_node": "planner",
            "error": str(e),
        }
