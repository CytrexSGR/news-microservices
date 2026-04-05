"""
Main FastAPI application for Feed Service
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import (
    feeds_router,
    items_router,
    operations_router,
    health_router,
    scraping_router,
    research_router,
    assessment_router,
    sources_router,
    source_feeds_router,
    duplicates_router,
    review_router,
)
from app.api.routes.admiralty_codes import router as admiralty_codes_router
from app.api.scheduling import router as scheduling_router
from app.api.crawl_sessions import router as crawl_sessions_router
from app.api.errors import register_exception_handlers
from app.db import init_async_db
from app.services.feed_scheduler import get_scheduler
from app.services.event_publisher import get_event_publisher, close_event_publisher
from app.workers.article_consumer import ArticleScrapedConsumer

# Import shared rate limiting
import sys
sys.path.insert(0, '/home/cytrex/news-microservices/services')
from common.rate_limiting import setup_rate_limiting

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text"
    else '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
)

logger = logging.getLogger(__name__)

# Check if shared contracts are available at startup
try:
    from shared.contracts import build_assessment_request
    SHARED_CONTRACTS_LOADED = True
except ImportError:
    SHARED_CONTRACTS_LOADED = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup:
    - Initialize database
    - Connect to RabbitMQ
    - Start RabbitMQ consumers
    - Start feed scheduler

    Shutdown:
    - Stop consumers
    - Stop scheduler
    - Close RabbitMQ connection
    """
    logger.info("Starting Feed Service...")

    # Database tables are created via Alembic migrations
    # No need to call init_async_db() - it causes startup delays and lock contention
    logger.info("Database connection ready (tables managed by migrations)")

    # Connect to RabbitMQ event publisher
    try:
        event_publisher = await get_event_publisher()
        logger.info("✓ Connected to RabbitMQ event publisher")
    except Exception as e:
        logger.warning(f"RabbitMQ event publisher not available: {e}")

    # Start article.scraped consumer
    article_consumer = None
    try:
        article_consumer = ArticleScrapedConsumer()
        # Start consumer in background task
        import asyncio
        app.state.article_consumer_task = asyncio.create_task(article_consumer.run())
        logger.info("✓ Started article.scraped consumer")
    except Exception as e:
        logger.error(f"Failed to start article.scraped consumer: {e}")

    # Start feed scheduler if enabled
    if settings.SCHEDULER_ENABLED:
        scheduler = get_scheduler()
        await scheduler.start()
        logger.info("Feed scheduler started")

    # Log contract availability (early warning against future drift)
    if SHARED_CONTRACTS_LOADED:
        logger.info("✓ Shared contracts loaded successfully - type-safe assessment requests enabled")
    else:
        logger.warning("⚠ Shared contracts NOT available - using fallback mode (degraded type safety)")

    logger.info(f"Feed Service started on port {settings.SERVICE_PORT}")

    yield

    # Shutdown
    logger.info("Shutting down Feed Service...")

    # Stop article consumer
    if hasattr(app.state, "article_consumer_task"):
        app.state.article_consumer_task.cancel()
        try:
            await app.state.article_consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped article.scraped consumer")

    # Stop scheduler
    if settings.SCHEDULER_ENABLED:
        scheduler = get_scheduler()
        await scheduler.stop()
        logger.info("Feed scheduler stopped")

    # Close RabbitMQ connection
    await close_event_publisher()
    logger.info("Disconnected from RabbitMQ")

    logger.info("Feed Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="RSS/Atom feed management and fetching microservice",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Configure rate limiting (Redis-backed)
setup_rate_limiting(app, settings.REDIS_URL)

# Register exception handlers (Task 406: Standardized error handling)
register_exception_handlers(app)

# Include routers
# IMPORTANT: Routers with specific paths must come BEFORE routers with {feed_id} parameters
# to avoid route conflicts (e.g., /items must match before /{feed_id})

# Feed items/articles (has /items path)
app.include_router(items_router)
# Feed operations (has /bulk-fetch path)
app.include_router(operations_router)
# Feed health & quality (has /quality-v2/overview path)
app.include_router(health_router)
# Scraping management
app.include_router(scraping_router)
# Research articles & analysis triggers
app.include_router(research_router)
# Core feed CRUD (has /{feed_id} catch-all pattern - must be last)
app.include_router(feeds_router)
# Source assessment
app.include_router(assessment_router, prefix="/api/v1/feeds", tags=["assessment"])
# Admiralty codes
app.include_router(admiralty_codes_router)
# Scheduling
app.include_router(scheduling_router, prefix="/api/v1/scheduling", tags=["scheduling"])
# Unified Source Management (new)
app.include_router(sources_router)
app.include_router(source_feeds_router)
# Duplicate review management (Epic 1.2)
app.include_router(duplicates_router)
# HITL publication review queue (Epic 2.3)
app.include_router(review_router)
# Crawl session tracking
app.include_router(crawl_sessions_router)


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from fastapi import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service status and basic information.
    """
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_scheduler_status()

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "scheduler": scheduler_status,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "documentation": "/docs",
        "health": "/health",
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