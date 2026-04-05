"""Intelligence MCP Client - proxies tool calls to mcp-intelligence-server."""

import logging
from typing import Any, Dict, List

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class IntelligenceClient(BaseClient):
    """Client for mcp-intelligence-server (Port 9001).

    Proxies MCP tool calls to the intelligence gateway which has access to:
    - content-analysis-v3
    - entity-canonicalization
    - intelligence-service
    - narrative-service
    """

    def __init__(self):
        super().__init__(
            service_name="mcp-intelligence-server",
            base_url=settings.intelligence_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Proxy tool call to mcp-intelligence-server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result from intelligence server
        """
        return await self.request(
            method="POST",
            path="/mcp/tools/call",
            json={
                "tool_name": tool_name,
                "arguments": arguments or {},
            },
        )

    async def list_tools(self) -> Dict[str, Any]:
        """Get available tools from intelligence server."""
        return await self.request(
            method="GET",
            path="/mcp/tools/list",
        )
