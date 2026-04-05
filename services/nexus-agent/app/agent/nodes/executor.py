"""Executor Node - Executes plan steps iteratively."""

import time
from typing import Dict, Any, List

from app.agent.state import AgentState, StepResult
from app.tools import get_tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute the next step in the confirmed plan.

    Executes steps sequentially, respecting dependencies.
    Stores results and updates execution status.

    Returns updated state with:
    - step_results: Updated with new result
    - current_step: Incremented
    - execution_status: Current status
    """
    pending_plan = state.get("pending_plan")
    if not pending_plan:
        return {
            "execution_status": "failed",
            "current_node": "executor",
            "error": "No plan to execute",
        }

    steps = pending_plan.get("steps", [])
    current_step = state.get("current_step", 0)
    step_results: List[StepResult] = list(state.get("step_results", []))

    # Find next step to execute
    if current_step >= len(steps):
        logger.info("executor_all_steps_complete", total_steps=len(steps))
        return {
            "execution_status": "completed",
            "current_node": "executor",
        }

    step = steps[current_step]
    step_number = step["step_number"]
    tool_name = step["tool_name"]
    tool_args = step.get("tool_args", {})

    # Check dependencies
    depends_on = step.get("depends_on", [])
    for dep in depends_on:
        dep_result = next(
            (r for r in step_results if r["step_number"] == dep),
            None
        )
        if not dep_result or not dep_result.get("success"):
            logger.warning(
                "executor_dependency_not_met",
                step=step_number,
                dependency=dep,
            )
            # Skip this step if dependency failed
            step_results.append({
                "step_number": step_number,
                "tool_name": tool_name,
                "success": False,
                "data": None,
                "error": f"Dependency step {dep} not completed",
                "execution_time_ms": 0,
            })
            return {
                "step_results": step_results,
                "current_step": current_step + 1,
                "execution_status": "running",
                "current_node": "executor",
            }

    # Special case: synthesize step (no tool execution)
    if tool_name == "synthesize":
        logger.info("executor_synthesize_step", step=step_number)
        step_results.append({
            "step_number": step_number,
            "tool_name": "synthesize",
            "success": True,
            "data": {"action": "synthesize"},
            "error": None,
            "execution_time_ms": 0,
        })
        return {
            "step_results": step_results,
            "current_step": current_step + 1,
            "execution_status": "completed",
            "current_node": "executor",
        }

    # Execute tool
    registry = get_tool_registry()
    tool = registry.get(tool_name)

    if not tool:
        logger.error("executor_tool_not_found", tool_name=tool_name)
        step_results.append({
            "step_number": step_number,
            "tool_name": tool_name,
            "success": False,
            "data": None,
            "error": f"Tool '{tool_name}' not found",
            "execution_time_ms": 0,
        })
        return {
            "step_results": step_results,
            "current_step": current_step + 1,
            "execution_status": "running",
            "current_node": "executor",
        }

    start_time = time.time()

    try:
        logger.info(
            "executor_running_tool",
            step=step_number,
            tool=tool_name,
            args=tool_args,
        )

        result = await tool.execute(**tool_args)
        execution_time_ms = int((time.time() - start_time) * 1000)

        step_results.append({
            "step_number": step_number,
            "tool_name": tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time_ms": execution_time_ms,
        })

        logger.info(
            "executor_step_complete",
            step=step_number,
            tool=tool_name,
            success=result.success,
            time_ms=execution_time_ms,
        )

    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "executor_step_error",
            step=step_number,
            tool=tool_name,
            error=str(e),
        )
        step_results.append({
            "step_number": step_number,
            "tool_name": tool_name,
            "success": False,
            "data": None,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        })

    # Check if all steps complete
    next_step = current_step + 1
    status = "completed" if next_step >= len(steps) else "running"

    return {
        "step_results": step_results,
        "current_step": next_step,
        "execution_status": status,
        "current_node": "executor",
    }
