"""FastAPI application for MCP Knowledge Graph Server."""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .mcp.protocol import MCPProtocol
from .models import MCPHealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global state
protocol_handler: MCPProtocol = None
startup_time: float = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global protocol_handler, startup_time

    # Startup
    startup_time = time.time()
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")

    protocol_handler = MCPProtocol()
    logger.info(f"Registered {len(protocol_handler.knowledge_graph_client.__class__.__dict__)} client methods")

    yield

    # Shutdown
    logger.info("Shutting down MCP Knowledge Graph Server")
    await protocol_handler.close()


# Create FastAPI app
app = FastAPI(
    title="MCP Knowledge Graph Server",
    description="Model Context Protocol server exposing Neo4j Knowledge Graph operations",
    version=settings.service_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ToolExecutionRequest(BaseModel):
    """Request to execute an MCP tool."""

    tool_name: str
    arguments: Dict[str, Any] = {}


# ==================== Health Endpoints ====================


@app.get("/health", response_model=MCPHealthResponse)
async def health_check():
    """Health check endpoint."""
    return MCPHealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        uptime_seconds=time.time() - startup_time,
        dependencies={
            "knowledge-graph-service": "connected",
        },
    )


# ==================== MCP Endpoints ====================


@app.get("/mcp/tools/list")
async def list_tools() -> List[Dict[str, Any]]:
    """List all available MCP tools."""
    try:
        tools = await protocol_handler.list_tools()
        return tools
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/execute")
async def execute_tool(request: ToolExecutionRequest) -> Dict[str, Any]:
    """Execute an MCP tool."""
    try:
        result = await protocol_handler.execute_tool(
            tool_name=request.tool_name,
            arguments=request.arguments,
        )
        return result.model_dump()
    except Exception as e:
        logger.error(f"Failed to execute tool '{request.tool_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/call")
async def call_tool(request: ToolExecutionRequest) -> Dict[str, Any]:
    """Execute an MCP tool (alias for /execute for MCP protocol compatibility)."""
    return await execute_tool(request)


@app.get("/mcp/info")
async def mcp_info() -> Dict[str, Any]:
    """Get MCP server information."""
    tools = await protocol_handler.list_tools()
    return {
        "server": settings.service_name,
        "version": settings.service_version,
        "mcp_version": "2025-06-18",
        "total_tools": len(tools),
        "tools_by_category": _count_tools_by_category(tools),
        "services": ["knowledge-graph-service"],
    }


def _count_tools_by_category(tools: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count tools by category."""
    counts = {}
    for tool in tools:
        category = tool.get("category", "unknown")
        counts[category] = counts.get(category, 0) + 1
    return counts


# ==================== Debug Endpoints ====================


@app.get("/debug/circuit-breakers")
async def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get circuit breaker status for all services."""
    return {
        "knowledge_graph": protocol_handler.knowledge_graph_client.client.get_metrics(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
