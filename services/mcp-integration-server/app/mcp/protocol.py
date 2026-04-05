"""MCP Protocol Handler."""

import logging
import time
from typing import Dict, Any

from ..models import ToolsListResponse, ToolsCallRequest, ToolsCallResponse, MCPToolResult
from ..clients import FMPClient, ResearchClient, NotificationClient
from .tools import tool_registry

logger = logging.getLogger(__name__)


class MCPProtocolHandler:
    """Handler for MCP Protocol endpoints."""

    def __init__(
        self,
        fmp_client: FMPClient,
        research_client: ResearchClient,
        notification_client: NotificationClient,
    ):
        self.fmp_client = fmp_client
        self.research_client = research_client
        self.notification_client = notification_client

    async def list_tools(self) -> ToolsListResponse:
        """
        List all available MCP tools.

        Returns:
            ToolsListResponse with tool definitions
        """
        tools = [tool_data["definition"] for tool_data in tool_registry.values()]

        return ToolsListResponse(
            tools=tools,
            server="mcp-integration-server",
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
        arguments = request.arguments.copy()

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
        # NOTE: Integration service tools REQUIRE client injection (unlike search-server)
        service = tool_data["definition"].service
        if service == "fmp-service":
            arguments["client"] = self.fmp_client
        elif service == "research-service":
            arguments["client"] = self.research_client
        elif service == "notification-service":
            arguments["client"] = self.notification_client

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
