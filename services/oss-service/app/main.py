"""
OSS Service - FastAPI Application
Main entry point for the Ontology Suggestion System microservice.

Issue #2: Request/Response Validation Middleware
Issue #3: Rate Limiting on API endpoints
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import sys
import asyncio
import json
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from app.config import settings
from app.database import check_db_connection, neo4j_connection
from app.api import analysis
from app.core.rate_limiting import limiter
from app.core.middleware import RequestValidationMiddleware, ResponseFormattingMiddleware
from app.core.exceptions import (
    validation_exception_handler,
    pydantic_validation_exception_handler,
    json_decode_exception_handler,
    generic_exception_handler,
    connection_error_handler
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text"
    else '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def scheduled_analysis_job():
    """
    Background job that runs OSS analysis periodically.
    Called by APScheduler at configured intervals.
    """
    try:
        logger.info("Running scheduled OSS analysis cycle")
        result = await analysis.run_analysis_cycle(neo4j_connection)
        logger.info(
            f"Scheduled analysis completed: "
            f"{result.proposals_generated} proposals generated, "
            f"{result.proposals_submitted} proposals submitted"
        )
    except Exception as e:
        logger.error(f"Scheduled analysis failed: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    global scheduler

    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Check Neo4j connection (non-blocking)
    logger.info("Checking Neo4j connection...")
    try:
        if check_db_connection():
            logger.info("Neo4j connection successful")
        else:
            logger.warning("Neo4j connection check failed - service will retry on first request")
    except Exception as e:
        logger.warning(f"Neo4j connection check error: {e} - service will retry on first request")

    # Start background scheduler
    logger.info(f"Starting background scheduler with interval: {settings.ANALYSIS_INTERVAL_SECONDS}s")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_analysis_job,
        'interval',
        seconds=settings.ANALYSIS_INTERVAL_SECONDS,
        id='oss_analysis',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Background scheduler started")

    logger.info(f"{settings.APP_NAME} started successfully")
    logger.info(f"Proposals API: {settings.PROPOSALS_API_URL}")
    logger.info(f"Analysis interval: {settings.ANALYSIS_INTERVAL_SECONDS}s")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
    neo4j_connection.close()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    OSS (Ontology Suggestion System) Service for News MCP

    Analyzes the Neo4j knowledge graph to:
    - Detect recurring patterns that suggest new entity/relationship types
    - Identify data quality issues and inconsistencies
    - Generate ontology change proposals
    - Submit proposals to Ontology Proposals API for human review

    The OSS learns from the data to suggest improvements to the ontology.
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Issue #2: Add request validation middleware
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(ResponseFormattingMiddleware)

# Issue #3: Attach rate limiter to app state
app.state.limiter = limiter

# Add exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(json.JSONDecodeError, json_decode_exception_handler)
app.add_exception_handler(ConnectionError, connection_error_handler)

# Include routers
app.include_router(analysis.router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Health status information
    """
    neo4j_healthy = check_db_connection()

    return {
        "status": "healthy" if neo4j_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "neo4j": "connected" if neo4j_healthy else "disconnected",
        "proposals_api": settings.PROPOSALS_API_URL
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with service information.

    Returns:
        Service information
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "description": "Ontology Suggestion System - Learns from knowledge graph to suggest improvements"
    }


# Global exception handler (Issue #2: Uses standardized format)
app.add_exception_handler(Exception, generic_exception_handler)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
