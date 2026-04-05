"""
Knowledge Graph Service - Main Application

FastAPI application providing graph query and ingestion APIs.

Post-Incident #18: Includes rate limiting to prevent API abuse.
"""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limiting import limiter
from app.services.neo4j_service import neo4j_service
from app.consumers.relationships_consumer import relationships_consumer
from app.consumers.market_consumer import get_market_consumer, close_market_consumer
from app.consumers.finance_intelligence_consumer import get_finance_intelligence_consumer, close_finance_intelligence_consumer
from app.consumers.narrative_consumer import narrative_consumer
from app.services.fmp_integration.market_sync_service import MarketSyncService
from app.api.routes import health, graph, analytics, enrichment, pathfinding, search, articles, admin_query, history, quality, findings, markets, narratives
from app.core.metrics import kg_health_status, kg_uptime_seconds
from app.database.models import Base
from app.api.dependencies import engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Track service start time for uptime metric
SERVICE_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Connect to Neo4j
    - Shutdown: Close Neo4j connection
    """
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    try:
        # Create PostgreSQL tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ PostgreSQL tables created/verified")

        # Connect to Neo4j
        await neo4j_service.connect()
        logger.info("✓ Neo4j connected")
        kg_health_status.labels(component='neo4j').set(1)

        # Connect to RabbitMQ and start consuming
        await relationships_consumer.connect()
        await relationships_consumer.start_consuming()
        logger.info("✓ RabbitMQ relationships consumer started")

        # Start market data consumer
        market_sync_service = MarketSyncService()
        market_consumer = await get_market_consumer(market_sync_service)
        await market_consumer.start_consuming()
        logger.info("✓ RabbitMQ market consumer started")

        # Start finance intelligence consumer
        finance_consumer = await get_finance_intelligence_consumer()
        await finance_consumer.start_consuming()
        logger.info("✓ RabbitMQ finance intelligence consumer started")

        # Start narrative frame consumer
        await narrative_consumer.connect()
        await narrative_consumer.start_consuming()
        logger.info("✓ RabbitMQ narrative frame consumer started")

        kg_health_status.labels(component='rabbitmq').set(1)
        kg_health_status.labels(component='consumer').set(1)

        # Mark overall service as healthy
        kg_health_status.labels(component='overall').set(1)

    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        kg_health_status.labels(component='overall').set(0)
        raise

    logger.info(f"✓ {settings.SERVICE_NAME} started on port {settings.SERVICE_PORT}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")

    try:
        await relationships_consumer.disconnect()
        logger.info("✓ RabbitMQ relationships consumer disconnected")

        await close_market_consumer()
        logger.info("✓ RabbitMQ market consumer disconnected")

        await close_finance_intelligence_consumer()
        logger.info("✓ RabbitMQ finance intelligence consumer disconnected")

        await narrative_consumer.disconnect()
        logger.info("✓ RabbitMQ narrative consumer disconnected")

        await neo4j_service.disconnect()
        logger.info("✓ Neo4j disconnected")

    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}", exc_info=True)

    logger.info(f"✓ {settings.SERVICE_NAME} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Knowledge Graph Service",
    description="Graph database for entity relationships and connections",
    version="1.0.0",
    lifespan=lifespan
)

# Attach rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(graph.router, tags=["Graph"])
app.include_router(findings.router, tags=["Findings"])  # NEW: Symbolic findings ingestion
app.include_router(markets.router, tags=["Markets"])  # NEW: Market data integration
app.include_router(search.router, tags=["Search"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(enrichment.router, tags=["Enrichment"])
app.include_router(pathfinding.router, tags=["Pathfinding"])
app.include_router(articles.router, tags=["Articles"])
app.include_router(admin_query.router, tags=["Admin"])
app.include_router(history.router, tags=["History"])
app.include_router(quality.router, tags=["Quality"])
app.include_router(narratives.router, tags=["Narratives"])  # NEW: Narrative framing analysis

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    # Update uptime metric
    uptime = time.time() - SERVICE_START_TIME
    kg_uptime_seconds.set(uptime)

    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": "1.0.0",
        "uptime_seconds": int(uptime)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
