"""Entity Canonicalization Service - Main Application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.config import settings
from app.api.routes import canonicalization
from app.database.models import Base
from app.api.dependencies import engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # 🔧 PRELOAD SINGLETONS (prevent lazy loading during first request)
    # OpenAI Embeddings (cloud-native, no local model loading)
    # Prevents event loop blocking that causes health check failures
    from app.api.dependencies import (
        get_wikidata_client,
        get_embedding_service,
        get_fuzzy_matcher
    )

    logger.info("Preloading singleton dependencies...")
    wikidata_client = get_wikidata_client()
    logger.info("✓ Wikidata client initialized")

    embedding_service = get_embedding_service()
    logger.info("✓ Embedding service initialized (OpenAI cloud-native)")

    fuzzy_matcher = get_fuzzy_matcher()
    logger.info("✓ Fuzzy matcher initialized (RapidFuzz)")

    logger.info("All singletons preloaded - API ready for fast responses")

    logger.info(f"{settings.SERVICE_NAME} started successfully on port {settings.SERVICE_PORT}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    await engine.dispose()
    logger.info(f"{settings.SERVICE_NAME} stopped")


# Create FastAPI app
app = FastAPI(
    title="Entity Canonicalization Service",
    description="Entity canonicalization and alias management service",
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

# Include routers
app.include_router(canonicalization.router)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
