"""Gatekeeper Node - Intent classification."""

import json
from app.agent.state import AgentState
from app.llm.openai_client import get_openai_client
from app.llm.prompts import GATEKEEPER_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)


def _check_plan_confirmation(message: str) -> bool:
    """Check if message is a plan confirmation/cancel response."""
    message_lower = message.lower().strip()
    confirmation_keywords = [
        "ja", "ok", "yes", "bestätigen", "machen", "los", "ausführen",
        "nein", "abbrechen", "stop", "cancel", "nicht",
        "anpassen", "ändern", "modify", "change", "anders"
    ]
    return any(keyword in message_lower for keyword in confirmation_keywords)


async def gatekeeper_node(state: AgentState) -> dict:
    """
    Classify the user's intent and determine routing.

    Returns updated state with:
    - intent: The classified intent
    - complexity_score: 0.0-1.0
    - requires_tools: Whether tools are needed
    - requires_planning: Whether multi-step planning is needed (Phase 3)
    """
    # Get the last user message
    messages = state.get("messages", [])
    if not messages:
        return {
            "intent": "chitchat",
            "complexity_score": 0.0,
            "requires_tools": False,
            "requires_planning": False,
            "current_node": "gatekeeper",
        }

    last_message = messages[-1].content

    # Phase 3: Check for plan confirmation when there's a pending plan
    pending_plan = state.get("pending_plan")
    if pending_plan and _check_plan_confirmation(last_message):
        logger.info("gatekeeper_plan_confirmation", message=last_message[:50])
        return {
            "intent": "plan_confirmation",
            "complexity_score": 0.1,
            "requires_tools": False,
            "requires_planning": False,
            "current_node": "gatekeeper",
        }

    # Call LLM for classification
    client = get_openai_client()

    try:
        response, tokens = await client.invoke(
            system_prompt=GATEKEEPER_PROMPT,
            user_message=last_message,
        )

        # Parse JSON response
        # Handle markdown code blocks if present
        response_clean = response.strip()
        if response_clean.startswith("```"):
            # Extract JSON from code block
            lines = response_clean.split("\n")
            json_lines = [l for l in lines if not l.startswith("```")]
            response_clean = "\n".join(json_lines)

        result = json.loads(response_clean)

        logger.info(
            "gatekeeper_classified",
            intent=result.get("intent"),
            complexity=result.get("complexity_score"),
            requires_tools=result.get("requires_tools"),
        )

        return {
            "intent": result.get("intent", "simple_query"),
            "complexity_score": result.get("complexity_score", 0.5),
            "requires_tools": result.get("requires_tools", False),
            "requires_planning": result.get("requires_planning", False),
            "current_node": "gatekeeper",
            "tokens_used": state.get("tokens_used", 0) + tokens,
        }

    except json.JSONDecodeError as e:
        logger.warning("gatekeeper_json_parse_error", error=str(e))
        # Default to simple query on parse error
        return {
            "intent": "simple_query",
            "complexity_score": 0.3,
            "requires_tools": False,
            "requires_planning": False,
            "current_node": "gatekeeper",
            "error": f"Classification parse error: {e}",
        }
    except Exception as e:
        logger.error("gatekeeper_error", error=str(e))
        return {
            "intent": "simple_query",
            "complexity_score": 0.3,
            "requires_tools": False,
            "requires_planning": False,
            "current_node": "gatekeeper",
            "error": str(e),
        }
