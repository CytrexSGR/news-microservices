"""MCP Tool Registry and Decorator."""

import time
import logging
from typing import Dict, Any, Callable, Awaitable
from functools import wraps

from ...models import MCPTool, MCPToolParameter, MCPToolResult

logger = logging.getLogger(__name__)

# Global tool registry
tool_registry: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
    parameters: list,
    service: str,
    category: str,
    cost: str = None,
    latency: str = None,
):
    """
    Decorator to register MCP tool.

    Args:
        name: Tool name
        description: Tool description for LLM
        parameters: List of MCPToolParameter dicts
        service: Backend service providing tool
        category: Tool category
        cost: Estimated cost per call
        latency: Expected latency
    """

    def decorator(func: Callable[..., Awaitable[MCPToolResult]]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> MCPToolResult:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Tool {name} executed successfully",
                    extra={
                        "tool": name,
                        "execution_time_ms": execution_time,
                        "success": result.success,
                    },
                )
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Tool {name} execution failed: {e}",
                    extra={
                        "tool": name,
                        "execution_time_ms": execution_time,
                        "error": str(e),
                    },
                )
                return MCPToolResult(
                    success=False,
                    error=str(e),
                    metadata={"execution_time_ms": execution_time},
                )

        # Register tool metadata
        tool_registry[name] = {
            "definition": MCPTool(
                name=name,
                description=description,
                parameters=[MCPToolParameter(**p) for p in parameters],
                service=service,
                cost=cost,
                latency=latency,
                category=category,
            ),
            "handler": wrapper,
        }

        return wrapper

    return decorator
