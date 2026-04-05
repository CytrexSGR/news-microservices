"""Tools Executor Node - Execute selected tools."""

import asyncio
from typing import List, Dict, Any

from app.agent.state import AgentState, ToolCall, ToolResultState
from app.tools import get_tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


async def tools_executor_node(state: AgentState) -> dict:
    """
    Execute the tools requested by the brain node.

    Takes tool_calls from state, executes them in parallel,
    and returns tool_results.
    """
    tool_calls: List[ToolCall] = state.get("tool_calls", [])

    if not tool_calls:
        logger.info("tools_executor_no_calls")
        return {
            "tool_results": [],
            "tools_executed": True,
            "current_node": "tools",
        }

    registry = get_tool_registry()
    results: List[ToolResultState] = []

    # Execute tools in parallel for efficiency
    async def execute_tool(tool_call: ToolCall) -> ToolResultState:
        tool_name = tool_call.get("tool_name", "")
        arguments = tool_call.get("arguments", {})

        logger.info(
            "tool_executing",
            tool=tool_name,
            args=list(arguments.keys()),
        )

        result = await registry.execute(tool_name, **arguments)

        return {
            "tool_name": result.tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
        }

    # Run all tool executions in parallel
    try:
        tasks = [execute_tool(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks)

        # Log summary
        successful = sum(1 for r in results if r["success"])
        logger.info(
            "tools_execution_complete",
            total=len(results),
            successful=successful,
            failed=len(results) - successful,
        )

    except Exception as e:
        logger.error("tools_execution_error", error=str(e))
        return {
            "tool_results": [],
            "tools_executed": True,
            "current_node": "tools",
            "error": f"Tool execution error: {str(e)}",
        }

    return {
        "tool_results": list(results),
        "tools_executed": True,
        "current_node": "tools",
    }


def format_tool_results_for_llm(results: List[ToolResultState]) -> str:
    """Format tool results into a readable string for the LLM."""
    if not results:
        return "No tool results available."

    output_parts = ["## Tool Execution Results\n"]

    for result in results:
        tool_name = result.get("tool_name", "unknown")
        success = result.get("success", False)
        data = result.get("data")
        error = result.get("error")
        exec_time = result.get("execution_time_ms", 0)

        output_parts.append(f"### {tool_name}")
        output_parts.append(f"- **Status**: {'Success' if success else 'Failed'}")
        output_parts.append(f"- **Execution Time**: {exec_time}ms")

        if success and data:
            output_parts.append(f"- **Data**:")
            # Format data nicely
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        output_parts.append(f"  - {key}: {len(value)} items")
                        # Show first few items for lists
                        for item in value[:3]:
                            if isinstance(item, dict):
                                summary = _summarize_dict(item)
                                output_parts.append(f"    - {summary}")
                            else:
                                output_parts.append(f"    - {item}")
                        if len(value) > 3:
                            output_parts.append(f"    - ... and {len(value) - 3} more")
                    else:
                        output_parts.append(f"  - {key}: {value}")
            else:
                output_parts.append(f"  {data}")
        elif error:
            output_parts.append(f"- **Error**: {error}")

        output_parts.append("")  # Empty line between results

    return "\n".join(output_parts)


def _summarize_dict(d: Dict[str, Any], max_fields: int = 3) -> str:
    """Create a brief summary of a dictionary."""
    if not d:
        return "{}"

    # Prioritize certain fields
    priority_fields = ["title", "name", "id", "content", "summary"]
    fields = []

    for field in priority_fields:
        if field in d:
            value = d[field]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            fields.append(f"{field}={repr(value)}")
            if len(fields) >= max_fields:
                break

    # Add other fields if we haven't reached max
    for key, value in d.items():
        if key not in priority_fields and len(fields) < max_fields:
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            fields.append(f"{key}={repr(value)}")

    return ", ".join(fields)
