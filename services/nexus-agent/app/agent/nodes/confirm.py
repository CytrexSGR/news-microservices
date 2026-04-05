"""Confirm Node - Handles plan confirmation flow."""

from typing import Dict, Any

from app.agent.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _format_plan_for_display(plan: dict) -> str:
    """Format execution plan as human-readable text."""
    if not plan:
        return "Kein Plan vorhanden."

    lines = [
        f"**Ziel:** {plan.get('goal', 'Unbekannt')}",
        f"**Komplexität:** {plan.get('complexity', 'medium')}",
        f"**Geschätzte Tool-Aufrufe:** {plan.get('estimated_tools', 0)}",
        "",
        "**Schritte:**",
    ]

    for step in plan.get("steps", []):
        deps = step.get("depends_on", [])
        dep_str = f" (nach Schritt {', '.join(map(str, deps))})" if deps else ""
        lines.append(
            f"{step['step_number']}. [{step['tool_name']}] {step['description']}{dep_str}"
        )

    lines.extend([
        "",
        "Bestätigen Sie mit 'ja' oder 'ok', ändern mit 'anpassen', abbrechen mit 'abbrechen'."
    ])

    return "\n".join(lines)


async def confirm_node(state: AgentState) -> Dict[str, Any]:
    """
    Handle plan confirmation or present plan to user.

    If there's a pending plan and user message is a confirmation,
    process the confirmation action.

    Returns updated state with:
    - final_response: Formatted plan for display or confirmation status
    - current_node: "confirm"
    - plan_confirmed: True if user confirmed
    """
    pending_plan = state.get("pending_plan")
    messages = state.get("messages", [])

    if not pending_plan:
        logger.warning("confirm_node_no_plan")
        return {
            "final_response": "Es liegt kein Plan zur Bestätigung vor.",
            "current_node": "confirm",
            "plan_confirmed": False,
        }

    # Check if this is a confirmation response
    if messages:
        last_message = messages[-1].content
        action = check_confirmation_response(last_message)

        if action == "confirm":
            logger.info("plan_confirmed", plan_goal=pending_plan.get("goal"))
            return {
                "plan_confirmed": True,
                "plan_cancelled": False,
                "current_node": "confirm",
                "current_step": 0,
                "step_results": [],
            }
        elif action == "cancel":
            logger.info("plan_cancelled", plan_goal=pending_plan.get("goal"))
            return {
                "final_response": "Plan wurde abgebrochen.",
                "plan_confirmed": False,
                "plan_cancelled": True,
                "pending_plan": None,
                "current_node": "confirm",
                "awaiting_confirmation": False,
            }
        elif action == "modify":
            # For now, just re-show the plan
            plan_display = _format_plan_for_display(pending_plan)
            return {
                "final_response": f"Bitte beschreiben Sie die gewünschten Änderungen.\n\nAktueller Plan:\n{plan_display}",
                "current_node": "confirm",
                "plan_confirmed": False,
                "awaiting_confirmation": True,
            }

    # First time showing plan - format for display
    plan_display = _format_plan_for_display(pending_plan)

    logger.info(
        "confirm_node_awaiting",
        plan_steps=len(pending_plan.get("steps", [])),
    )

    return {
        "final_response": f"Ich habe folgenden Plan erstellt:\n\n{plan_display}",
        "current_node": "confirm",
        "plan_confirmed": False,
        # Signal to API that we're awaiting confirmation
        "awaiting_confirmation": True,
    }


def check_confirmation_response(user_message: str) -> str:
    """
    Check user's response to determine confirmation action.

    Returns: "confirm" | "modify" | "cancel" | "unknown"
    """
    message_lower = user_message.lower().strip()

    confirm_keywords = ["ja", "ok", "yes", "bestätigen", "machen", "los", "ausführen"]
    cancel_keywords = ["nein", "abbrechen", "stop", "cancel", "nicht"]
    modify_keywords = ["anpassen", "ändern", "modify", "change", "anders"]

    for keyword in confirm_keywords:
        if keyword in message_lower:
            return "confirm"

    for keyword in cancel_keywords:
        if keyword in message_lower:
            return "cancel"

    for keyword in modify_keywords:
        if keyword in message_lower:
            return "modify"

    return "unknown"
