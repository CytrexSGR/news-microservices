"""MCP protocol models for tool definitions and results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    """Definition of an MCP tool."""

    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Tool description for LLM")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for tool inputs"
    )
    category: str = Field(default="general", description="Tool category")


class MCPToolResult(BaseModel):
    """Result from an MCP tool execution."""

    success: bool = Field(..., description="Whether the tool executed successfully")
    data: Optional[Any] = Field(None, description="Tool output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the execution"
    )


class MCPToolCallRequest(BaseModel):
    """Request to call an MCP tool."""

    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Tool arguments"
    )


class MCPToolCallResponse(BaseModel):
    """Response from an MCP tool call."""

    tool_name: str = Field(..., description="Name of the tool that was called")
    result: MCPToolResult = Field(..., description="Tool execution result")
    execution_time_ms: Optional[float] = Field(
        None, description="Execution time in milliseconds"
    )
