"""Shared data models for MCP protocol."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolParameter(BaseModel):
    """Parameter definition for MCP tool."""

    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class MCPToolMetadata(BaseModel):
    """Metadata for MCP tool."""

    name: str
    description: str
    parameters: List[MCPToolParameter] = Field(default_factory=list)
    service: str  # Backend service name
    category: str  # Tool category (entity, analytics, market, etc.)
    latency: str  # Expected latency range


class MCPToolResult(BaseModel):
    """Result from MCP tool execution."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPHealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    uptime_seconds: float
    dependencies: Dict[str, str] = Field(default_factory=dict)
