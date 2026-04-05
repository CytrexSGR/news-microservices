"""
Main FastAPI application for Search Service
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import get_redis_client, close_redis_client
from app.api import api_router
from app.events.consumer import get_consumer, close_consumer

# Import shared rate limiting
import sys
sys.path.insert(0, '/home/cytrex/news-microservices/services')
from common.rate_limiting import setup_rate_limiting

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    if settings.LOG_FORMAT == "json"
    else '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup:
    - Initialize database
    - Connect to Redis
    - Start RabbitMQ event consumer
    - Start Celery workers (if enabled)

    Shutdown:
    - Close RabbitMQ consumer
    - Close Redis connection
    """
    logger.info("Starting Search Service...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis
    redis_client = await get_redis_client()
    await redis_client.ping()
    logger.info("Connected to Redis")

    # Start RabbitMQ consumer in background
    consumer = get_consumer()
    consumer_task = asyncio.create_task(consumer.start_consuming())
    logger.info("RabbitMQ event consumer started")

    logger.info(f"Search Service started on port {settings.SERVICE_PORT}")

    yield

    # Shutdown
    logger.info("Shutting down Search Service...")

    # Close RabbitMQ consumer
    await close_consumer()
    logger.info("RabbitMQ consumer closed")

    # Close Redis connection
    await close_redis_client()
    logger.info("Disconnected from Redis")

    logger.info("Search Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Full-text search microservice with PostgreSQL and advanced query capabilities",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Configure rate limiting (Redis-backed)
setup_rate_limiting(app, settings.REDIS_URL)

# Include API router
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service status and configuration.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "indexing": {
            "enabled": settings.INDEXING_ENABLED,
            "interval": settings.INDEXING_INTERVAL,
        },
        "search": {
            "fuzzy_enabled": settings.ENABLE_FUZZY_SEARCH,
            "max_results": settings.MAX_SEARCH_RESULTS,
        },
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "documentation": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found: {request.url.path}",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
