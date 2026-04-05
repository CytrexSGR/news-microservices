"""MCP Protocol Data Models."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Literal


class MCPToolParameter(BaseModel):
    """MCP Tool Parameter Definition."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, boolean, array, object)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    enum: Optional[List[str]] = Field(default=None, description="Allowed values for enum types")
    items: Optional[Dict[str, Any]] = Field(default=None, description="Array item schema for array types")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Object properties for object types")


class MCPTool(BaseModel):
    """MCP Tool Definition."""

    name: str = Field(..., description="Tool name (e.g., 'analyze_article')")
    description: str = Field(..., description="Tool description for LLM")
    parameters: List[MCPToolParameter] = Field(default_factory=list, description="Tool parameters")

    # Metadata
    service: str = Field(..., description="Backend service providing this tool")
    cost: Optional[str] = Field(default=None, description="Estimated cost per call")
    latency: Optional[str] = Field(default=None, description="Expected latency")
    category: str = Field(..., description="Tool category (analysis, entity, intelligence, narrative)")


class MCPToolCall(BaseModel):
    """MCP Tool Call Arguments."""

    tool_name: str = Field(..., description="Name of tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPToolResult(BaseModel):
    """MCP Tool Call Result."""

    success: bool = Field(..., description="Whether tool call succeeded")
    data: Optional[Any] = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ToolsListResponse(BaseModel):
    """Response for /mcp/tools/list endpoint."""

    tools: List[MCPTool] = Field(..., description="Available MCP tools")
    server: str = Field(default="mcp-intelligence-server", description="MCP server name")
    version: str = Field(default="1.0.0", description="Server version")
    total_tools: int = Field(..., description="Total number of tools")


class ToolsCallRequest(BaseModel):
    """Request for /mcp/tools/call endpoint."""

    tool_name: str = Field(..., description="Name of tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolsCallResponse(BaseModel):
    """Response for /mcp/tools/call endpoint."""

    tool_name: str = Field(..., description="Called tool name")
    result: MCPToolResult = Field(..., description="Tool execution result")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
