"""MCP Protocol handler for HTTP-based MCP server."""

import logging
import time
from typing import Any, Dict, List

from ..models import (
    MCPToolDefinition,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolResult,
)
from .tools import tool_registry

logger = logging.getLogger(__name__)


class MCPProtocolHandler:
    """Handles MCP protocol operations."""

    def __init__(self):
        self.registry = tool_registry

    async def initialize(self):
        """Initialize the protocol handler and clients."""
        await self.registry.initialize_clients()
        logger.info(
            f"MCP Protocol Handler initialized with {len(self.registry.tools)} tools"
        )

    async def shutdown(self):
        """Shutdown the protocol handler."""
        await self.registry.close_clients()
        logger.info("MCP Protocol Handler shutdown")

    def list_tools(self) -> List[MCPToolDefinition]:
        """List all available MCP tools."""
        return self.registry.list_tools()

    async def call_tool(
        self,
        request: MCPToolCallRequest,
    ) -> MCPToolCallResponse:
        """Execute an MCP tool call."""
        start_time = time.perf_counter()

        result = await self.registry.call_tool(
            name=request.tool_name,
            arguments=request.arguments,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return MCPToolCallResponse(
            tool_name=request.tool_name,
            result=result,
            execution_time_ms=elapsed_ms,
        )

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information for MCP protocol."""
        return {
            "name": "mcp-orchestration-server",
            "version": "1.0.0",
            "protocol_version": "0.1.0",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False,
            },
            "tool_count": len(self.registry.tools),
            "categories": list(
                set(tool.category for tool in self.registry.tools.values())
            ),
        }
