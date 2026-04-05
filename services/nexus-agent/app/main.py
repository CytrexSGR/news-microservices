"""NEXUS Agent - FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.endpoints import health_router, chat_router, memory_router

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(
        "nexus_agent_starting",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        port=settings.SERVICE_PORT,
    )

    # Phase 2: Initialize tools on startup
    from app.tools import register_all_tools
    registry = register_all_tools()
    logger.info(
        "tools_registered",
        tool_count=len(registry.list_tools()),
        tools=registry.list_tools(),
    )

    # Initialize agent on startup
    from app.agent.nexus import get_nexus_agent
    get_nexus_agent()

    yield

    logger.info("nexus_agent_shutting_down")


app = FastAPI(
    title="NEXUS Agent",
    description="AI Co-Pilot for News Microservices Platform",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "operational",
        "docs": "/docs",
    }
