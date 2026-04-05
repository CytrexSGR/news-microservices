"""MCP Core Server - FastAPI Application.

Provides MCP (Model Context Protocol) gateway for:
- Auth Service (8100): Authentication, JWT tokens, API keys
- Analytics Service (8107): Metrics, monitoring, dashboards, reports
"""

import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .config import settings
from .cache import cache_manager
from .mcp import MCPProtocolHandler, tool_registry
from .models import (
    MCPToolDefinition,
    MCPToolCallRequest,
    MCPToolCallResponse,
)
from .metrics import SERVER_INFO
import app.web_source_tools  # noqa: F401 — registers web source MCP tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# MCP Protocol Handler
mcp_handler = MCPProtocolHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.server_name} v{settings.server_version}")

    # Set server info metric
    SERVER_INFO.info({
        "name": settings.server_name,
        "version": settings.server_version,
    })

    # Initialize cache
    await cache_manager.connect()

    # Initialize MCP handler
    await mcp_handler.initialize()

    logger.info(
        f"MCP Core Server ready with {len(tool_registry.tools)} tools"
    )

    yield

    # Shutdown
    logger.info("Shutting down MCP Core Server...")
    await mcp_handler.shutdown()
    await cache_manager.close()


# Create FastAPI app
app = FastAPI(
    title="MCP Core Server",
    description="MCP Gateway for Auth and Analytics Services",
    version=settings.server_version,
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

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# =============================================================================
# Health & Info Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.server_name,
        "version": settings.server_version,
    }


@app.get("/")
async def root():
    """Root endpoint with server info."""
    return mcp_handler.get_server_info()


# =============================================================================
# MCP Protocol Endpoints
# =============================================================================

@app.get("/mcp/tools", response_model=List[MCPToolDefinition])
async def list_tools():
    """List all available MCP tools."""
    return mcp_handler.list_tools()


@app.post("/mcp/tools/call", response_model=MCPToolCallResponse)
async def call_tool(request: MCPToolCallRequest):
    """Call an MCP tool."""
    try:
        return await mcp_handler.call_tool(request)
    except Exception as e:
        logger.error(f"Tool call failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/tools/{tool_name}", response_model=MCPToolDefinition)
async def get_tool(tool_name: str):
    """Get tool definition by name."""
    tools = {t.name: t for t in mcp_handler.list_tools()}
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tools[tool_name]


# =============================================================================
# API Info Endpoints
# =============================================================================

@app.get("/api/v1/info")
async def get_info():
    """Get detailed server information."""
    tools = mcp_handler.list_tools()
    categories = {}
    for tool in tools:
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool.name)

    return {
        "server": settings.server_name,
        "version": settings.server_version,
        "backend_services": {
            "auth": settings.auth_service_url,
            "analytics": settings.analytics_service_url,
        },
        "tool_count": len(tools),
        "tools_by_category": categories,
    }
