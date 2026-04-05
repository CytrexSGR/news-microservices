"""Synthesizer Node - Combines step results into final output."""

import json
from typing import Dict, Any

from app.agent.state import AgentState
from app.llm.openai_client import get_openai_client
from app.llm.prompts import SYNTHESIZER_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)


def _format_step_results(step_results: list) -> str:
    """Format step results for the synthesizer prompt."""
    formatted = []
    for result in step_results:
        if result.get("tool_name") == "synthesize":
            continue  # Skip the synthesize placeholder

        status = "Erfolgreich" if result.get("success") else "Fehlgeschlagen"
        data_preview = json.dumps(result.get("data", {}), ensure_ascii=False, indent=2)
        if len(data_preview) > 1000:
            data_preview = data_preview[:1000] + "\n... (gekürzt)"

        formatted.append(
            f"### Schritt {result['step_number']}: {result['tool_name']}\n"
            f"Status: {status}\n"
            f"Dauer: {result.get('execution_time_ms', 0)}ms\n"
            f"Ergebnis:\n```json\n{data_preview}\n```"
        )

    return "\n\n".join(formatted)


async def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesize all step results into a final response.

    Uses LLM to create a coherent summary from all tool results.

    Returns updated state with:
    - synthesized_result: Structured synthesis
    - final_response: Human-readable summary
    """
    pending_plan = state.get("pending_plan")
    step_results = state.get("step_results", [])

    if not pending_plan or not step_results:
        return {
            "final_response": "Keine Ergebnisse zum Zusammenfassen.",
            "current_node": "synthesizer",
            "error": "No results to synthesize",
        }

    goal = pending_plan.get("goal", "Unbekanntes Ziel")
    formatted_results = _format_step_results(step_results)

    # Format prompt
    formatted_prompt = SYNTHESIZER_PROMPT.replace("{goal}", goal).replace(
        "{step_results}", formatted_results
    )

    client = get_openai_client()

    try:
        response, tokens = await client.invoke(
            system_prompt=formatted_prompt,
            user_message="Erstelle die Synthese der Ergebnisse.",
        )

        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            json_lines = [l for l in lines if not l.startswith("```")]
            response_clean = "\n".join(json_lines)

        synthesis = json.loads(response_clean)

        # Calculate total execution time
        total_time_ms = sum(r.get("execution_time_ms", 0) for r in step_results)
        successful_steps = sum(1 for r in step_results if r.get("success"))

        # Build synthesized result
        synthesized_result = {
            "summary": synthesis.get("summary", ""),
            "data": synthesis.get("data", {}),
            "sources": synthesis.get("sources", []),
            "confidence": synthesis.get("confidence", 0.5),
            "tool_calls": len(step_results) - 1,  # Exclude synthesize step
            "successful_steps": successful_steps,
            "execution_time_ms": total_time_ms,
        }

        logger.info(
            "synthesizer_complete",
            confidence=synthesized_result["confidence"],
            tool_calls=synthesized_result["tool_calls"],
            time_ms=total_time_ms,
        )

        return {
            "synthesized_result": synthesized_result,
            "final_response": synthesis.get("summary", "Synthese konnte nicht erstellt werden."),
            "confidence": synthesis.get("confidence", 0.5),
            "current_node": "synthesizer",
            "tokens_used": state.get("tokens_used", 0) + tokens,
        }

    except json.JSONDecodeError as e:
        logger.warning("synthesizer_json_parse_error", error=str(e))

        # Fallback: Create basic summary
        successful_tools = [r["tool_name"] for r in step_results if r.get("success")]
        fallback_summary = (
            f"Analyse für '{goal}' abgeschlossen.\n\n"
            f"Ausgeführte Tools: {', '.join(successful_tools)}\n"
            f"Details in den strukturierten Daten."
        )

        return {
            "synthesized_result": {
                "summary": fallback_summary,
                "data": {"raw_results": step_results},
                "sources": successful_tools,
                "confidence": 0.4,
            },
            "final_response": fallback_summary,
            "confidence": 0.4,
            "current_node": "synthesizer",
            "error": f"Synthesis parse error: {e}",
        }
    except Exception as e:
        logger.error("synthesizer_error", error=str(e))
        return {
            "final_response": f"Fehler bei der Synthese: {e}",
            "current_node": "synthesizer",
            "error": str(e),
        }
