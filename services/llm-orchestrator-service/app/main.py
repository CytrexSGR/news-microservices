"""
LLM Orchestrator Service - Main Application

Responsibilities:
1. Coordinate DIA (Dynamic Intelligence Augmentation) processes
2. Consume verification.required events from RabbitMQ
3. Orchestrate Planner and Verifier components
4. Provide health check and monitoring endpoints

Related: ADR-018 (DIA-Planner & Verifier)
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.verification_consumer import start_consumer, get_consumer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Startup:
    - Start RabbitMQ consumer in background

    Shutdown:
    - Close RabbitMQ connection
    """
    # Startup
    logger.info(f"[{settings.SERVICE_NAME}] Starting up...")

    # Start RabbitMQ consumer in background
    consumer_task = asyncio.create_task(start_consumer())
    logger.info("[Main] RabbitMQ consumer started in background")

    yield

    # Shutdown
    logger.info(f"[{settings.SERVICE_NAME}] Shutting down...")

    # Cancel consumer task
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    # Close consumer connection
    consumer = await get_consumer()
    await consumer.close()

    logger.info(f"[{settings.SERVICE_NAME}] Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="LLM Orchestrator Service for DIA (Dynamic Intelligence Augmentation)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status of the service
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if service is ready to accept requests.

    Returns:
        Ready status with component checks
    """
    # TODO: Add checks for RabbitMQ connection, OpenAI API, etc.
    return {
        "status": "ready",
        "checks": {
            "rabbitmq": "connected",  # TODO: Actual check
            "openai": "configured"    # TODO: Actual check
        }
    }


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": settings.SERVICE_NAME,
        "description": "LLM Orchestrator Service for DIA",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "readiness": "/health/ready",
            "docs": "/docs"
        }
    }


# ============================================================================
# Monitoring Endpoints (Future)
# ============================================================================

@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for Prometheus.

    TODO: Implement Prometheus metrics
    """
    return {
        "message": "Metrics endpoint - to be implemented"
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
