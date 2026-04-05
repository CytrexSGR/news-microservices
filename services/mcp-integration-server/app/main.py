"""MCP Integration Server - Main FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .config import settings
from .models import ToolsListResponse, ToolsCallRequest, ToolsCallResponse
from .clients import FMPClient, ResearchClient, NotificationClient
from .mcp import MCPProtocolHandler
from .cache import cache_manager
from .metrics import TOOL_CALLS, TOOL_DURATION

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global clients (initialized in lifespan)
fmp_client: FMPClient = None
research_client: ResearchClient = None
notification_client: NotificationClient = None
mcp_handler: MCPProtocolHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global fmp_client, research_client, notification_client, mcp_handler

    logger.info("Starting MCP Integration Server...")

    # Initialize Redis cache
    await cache_manager.connect()

    # Initialize HTTP clients
    fmp_client = FMPClient()
    research_client = ResearchClient()
    notification_client = NotificationClient()

    # Initialize MCP handler
    mcp_handler = MCPProtocolHandler(
        fmp_client=fmp_client,
        research_client=research_client,
        notification_client=notification_client,
    )

    logger.info("MCP Integration Server started successfully")

    yield

    # Cleanup
    logger.info("Shutting down MCP Integration Server...")
    await fmp_client.close()
    await research_client.close()
    await notification_client.close()
    await cache_manager.close()
    logger.info("MCP Integration Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="MCP Integration Server",
    description="Model Context Protocol gateway for Integration Services (FMP, Research, Notification)",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-integration-server",
        "version": "1.0.0",
    }


# ============================================================================
# MCP Protocol Endpoints
# ============================================================================

@app.get("/mcp/tools/list", response_model=ToolsListResponse)
async def list_tools() -> ToolsListResponse:
    """
    List all available MCP tools.

    Returns tool definitions for LLM discovery.
    """
    try:
        return await mcp_handler.list_tools()
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@app.post("/mcp/tools/call", response_model=ToolsCallResponse)
async def call_tool(request: ToolsCallRequest) -> ToolsCallResponse:
    """
    Call MCP tool with given arguments.

    Args:
        request: Tool call request with tool_name and arguments

    Returns:
        Tool execution result
    """
    tool_name = request.tool_name

    try:
        with TOOL_DURATION.labels(tool_name=tool_name).time():
            response = await mcp_handler.call_tool(request)

        # Record metrics
        status = "success" if response.result.success else "error"
        TOOL_CALLS.labels(tool_name=tool_name, status=status).inc()

        return response

    except Exception as e:
        logger.error(f"Failed to call tool {tool_name}: {e}")
        TOOL_CALLS.labels(tool_name=tool_name, status="error").inc()
        raise HTTPException(
            status_code=500, detail=f"Failed to call tool {tool_name}: {str(e)}"
        )


# ============================================================================
# Metrics Endpoint
# ============================================================================

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "MCP Integration Server",
        "version": "1.0.0",
        "description": "Model Context Protocol gateway for Integration Services",
        "endpoints": {
            "health": "/health",
            "tools_list": "/mcp/tools/list",
            "tools_call": "/mcp/tools/call",
            "metrics": "/metrics",
            "docs": "/docs",
        },
        "backend_services": {
            "fmp-service": settings.fmp_service_url,
            "research-service": settings.research_service_url,
            "notification-service": settings.notification_service_url,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9005,
        reload=True,
        log_level=settings.log_level.lower(),
    )
