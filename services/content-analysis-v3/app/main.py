"""
Content-Analysis-V3 API Service

Cost-optimized 4-tier AI analysis pipeline:
- Tier 0: Fast triage (keep/discard)
- Tier 1: Foundation extraction (entities, relations, topics)
- Tier 2: Specialist analysis (5 specialized modules)
- Tier 3: Intelligence modules (planned)

Target: 96.7% cost reduction vs V2 ($0.0085 → $0.00028 per article)
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.database import init_db_pool, close_db_pool
from app.api import health_router, analysis_router
from app.messaging import get_event_publisher, close_event_publisher
from app.infrastructure.graph_client import V3GraphClient
from app.core.config import settings
from app.core import metrics  # noqa: F401 - import for side effects (register metrics)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for FastAPI application.

    Startup: Initialize database pool, event publisher, and graph client
    Shutdown: Close database pool, event publisher, and graph client
    """
    # Startup
    await init_db_pool()
    await get_event_publisher()  # Initialize RabbitMQ publisher

    # Initialize Graph Client (if Neo4j configured)
    graph_client = V3GraphClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )
    try:
        await graph_client.connect()
        app.state.graph_client = graph_client
    except Exception as e:
        print(f"[WARNING] Failed to connect to Neo4j: {e}")
        print("[WARNING] Graph integration will be skipped")
        app.state.graph_client = None

    yield

    # Shutdown
    if app.state.graph_client:
        await app.state.graph_client.disconnect()
    await close_event_publisher()
    await close_db_pool()


# Create FastAPI application
app = FastAPI(
    title="Content-Analysis-V3",
    description="Cost-optimized AI analysis pipeline with 4-tier progressive analysis",
    version="1.0.0-alpha",
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
app.include_router(
    health_router,
    tags=["health"]
)

app.include_router(
    analysis_router,
    prefix="/api/v1",
    tags=["analysis"]
)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "content-analysis-v3",
        "version": "1.0.0-alpha",
        "description": "Cost-optimized AI analysis pipeline (96.7% cost reduction)",
        "status": "active",
        "endpoints": {
            "health": {
                "basic": "/health",
                "detailed": "/health/detailed",
                "ready": "/health/ready",
                "live": "/health/live"
            },
            "analysis": {
                "analyze": "POST /api/v1/analyze",
                "status": "GET /api/v1/status/{article_id}",
                "results": "GET /api/v1/results/{article_id}",
                "tier0": "GET /api/v1/results/{article_id}/tier0",
                "tier1": "GET /api/v1/results/{article_id}/tier1",
                "tier2": "GET /api/v1/results/{article_id}/tier2"
            },
            "monitoring": {
                "metrics": "/metrics"
            },
            "docs": {
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        },
        "pipeline": {
            "tier0": {
                "name": "Triage",
                "purpose": "Fast keep/discard decision",
                "budget": {"tokens": 800, "cost_usd": 0.00005}
            },
            "tier1": {
                "name": "Foundation Extraction",
                "purpose": "Core entity/relation/topic extraction",
                "budget": {"tokens": 2000, "cost_usd": 0.0001}
            },
            "tier2": {
                "name": "Specialist Analysis",
                "purpose": "5 specialized modules with 2-stage prompting",
                "budget": {"tokens": 8000, "cost_usd": 0.0005},
                "specialists": [
                    "Topic Classifier",
                    "Entity Extractor",
                    "Financial Analyst",
                    "Geopolitical Analyst",
                    "Sentiment Analyzer"
                ]
            },
            "tier3": {
                "name": "Intelligence Modules",
                "purpose": "Event timelines, multi-doc reasoning (planned)",
                "budget": {"tokens": 3000, "cost_usd": 0.001},
                "status": "not_implemented"
            }
        },
        "cost_analysis": {
            "v2_cost_per_article": 0.0085,
            "v3_cost_per_article": 0.00028,
            "cost_reduction_percent": 96.7,
            "total_budget_per_article": 0.00065
        }
    }
