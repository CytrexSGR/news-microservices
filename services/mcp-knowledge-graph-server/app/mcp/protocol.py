"""MCP protocol handler for Neo4j Knowledge Graph operations."""

import logging
from typing import Dict, Any, List

from ..clients import KnowledgeGraphClient
from ..models import MCPToolResult
from .tools import TOOL_REGISTRY, TOOL_FUNCTIONS

logger = logging.getLogger(__name__)


class MCPProtocol:
    """Handler for MCP protocol requests."""

    def __init__(self):
        self.knowledge_graph_client = KnowledgeGraphClient()
        logger.info(f"Initialized MCP Protocol with {len(TOOL_REGISTRY)} tools")

    async def close(self):
        """Close all HTTP clients."""
        await self.knowledge_graph_client.close()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": [p.model_dump() for p in tool.parameters],
                "service": tool.service,
                "category": tool.category,
                "latency": tool.latency,
            }
            for tool in TOOL_REGISTRY.values()
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute an MCP tool by name."""
        if tool_name not in TOOL_REGISTRY:
            return MCPToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found. Available tools: {list(TOOL_REGISTRY.keys())}",
                metadata={"tool": tool_name},
            )

        tool_metadata = TOOL_REGISTRY[tool_name]
        tool_func = TOOL_FUNCTIONS[tool_name]  # Get function from separate dict

        try:
            # Inject appropriate client based on service
            if tool_metadata.service == "knowledge-graph-service":
                result = await tool_func(self.knowledge_graph_client, **arguments)
            else:
                result = MCPToolResult(
                    success=False,
                    error=f"Unknown service: {tool_metadata.service}",
                    metadata={"tool": tool_name, "service": tool_metadata.service},
                )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {e}", exc_info=True)
            return MCPToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                metadata={"tool": tool_name, "error_type": type(e).__name__},
            )
