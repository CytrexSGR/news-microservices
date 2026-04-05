"""MCP Protocol Handler."""

import logging
import time
from typing import Dict, Any

from ..models import ToolsListResponse, ToolsCallRequest, ToolsCallResponse, MCPToolResult
from ..clients import (
    AnalyticsClient,
    PredictionClient,
    ExecutionClient,
)
from .tools import tool_registry

logger = logging.getLogger(__name__)


class MCPProtocolHandler:
    """Handler for MCP Protocol endpoints."""

    def __init__(
        self,
        analytics_client: AnalyticsClient,
        prediction_client: PredictionClient,
        execution_client: ExecutionClient,
    ):
        self.analytics_client = analytics_client
        self.prediction_client = prediction_client
        self.execution_client = execution_client

    async def list_tools(self) -> ToolsListResponse:
        """
        List all available MCP tools.

        Returns:
            ToolsListResponse with tool definitions
        """
        tools = [tool_data["definition"] for tool_data in tool_registry.values()]

        return ToolsListResponse(
            tools=tools,
            server="mcp-analytics-server",
            version="1.0.0",
            total_tools=len(tools),
        )

    async def call_tool(self, request: ToolsCallRequest) -> ToolsCallResponse:
        """
        Call MCP tool with given arguments.

        Args:
            request: Tool call request with tool_name and arguments

        Returns:
            ToolsCallResponse with execution result

        Raises:
            ValueError: If tool not found
        """
        tool_name = request.tool_name
        arguments = request.arguments

        # Validate tool exists
        if tool_name not in tool_registry:
            logger.error(f"Tool not found: {tool_name}")
            return ToolsCallResponse(
                tool_name=tool_name,
                result=MCPToolResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found. Available tools: {list(tool_registry.keys())}",
                ),
            )

        # Get tool handler
        tool_data = tool_registry[tool_name]
        handler = tool_data["handler"]

        # Inject appropriate client based on service
        # NOTE: Analytics service tools REQUIRE client injection (unlike search-server)
        service = tool_data["definition"].service
        if service == "analytics-service":
            arguments["client"] = self.analytics_client
        elif service == "prediction-service":
            arguments["client"] = self.prediction_client
        elif service == "execution-service":
            arguments["client"] = self.execution_client

        # Execute tool
        start_time = time.time()
        try:
            result = await handler(**arguments)
            execution_time = (time.time() - start_time) * 1000

            return ToolsCallResponse(
                tool_name=tool_name,
                result=result,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"Tool execution failed: {tool_name}",
                extra={"tool": tool_name, "error": str(e), "arguments": arguments},
            )

            return ToolsCallResponse(
                tool_name=tool_name,
                result=MCPToolResult(
                    success=False,
                    error=f"Tool execution failed: {str(e)}",
                    metadata={"execution_time_ms": execution_time},
                ),
                execution_time_ms=execution_time,
            )
