"""
Narrative Intelligence API Gateway
Unified endpoint for all narrative analysis features
"""
import os
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="Narrative Intelligence Gateway",
    description="Unified API for narrative frame analysis, tension monitoring, and entity tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend service URLs
KNOWLEDGE_GRAPH_URL = os.getenv("KNOWLEDGE_GRAPH_URL", "http://knowledge-graph-service:8111")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://notification-service:8105")

# HTTP client with connection pooling
http_client = httpx.AsyncClient(timeout=30.0)


# === Response Models ===

class NarrativeStats(BaseModel):
    total_narrative_frames: int
    tension_stats: dict
    frame_distribution: dict
    entities_with_narrative_data: int


class FrameDistribution(BaseModel):
    frame_type: str
    count: int
    percentage: float
    avg_tension: float


class EntityFraming(BaseModel):
    entity_name: str
    entity_type: Optional[str]
    narrative_count: int
    avg_tension: float
    max_tension: float
    frames: List[dict]


class HighTensionNarrative(BaseModel):
    tension: float
    frame_type: str
    entities: List[str]
    article_ids: Optional[List[str]] = []


class CooccurrencePattern(BaseModel):
    entity_a: str
    entity_b: str
    shared_count: int
    avg_tension: float


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    services: dict


# === Health Check ===

@app.get("/health", response_model=HealthStatus, tags=["System"])
async def health_check():
    """Check gateway and backend service health"""
    services = {}

    # Check knowledge-graph-service
    try:
        resp = await http_client.get(f"{KNOWLEDGE_GRAPH_URL}/health")
        services["knowledge-graph"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception:
        services["knowledge-graph"] = "unreachable"

    return {
        "status": "healthy" if all(s == "healthy" for s in services.values()) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }


# === Core Narrative Endpoints ===

@app.get("/api/v1/narratives/stats", tags=["Narratives"])
async def get_narrative_stats():
    """Get overall narrative statistics"""
    try:
        resp = await http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/stats")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@app.get("/api/v1/narratives/distribution", tags=["Narratives"])
async def get_frame_distribution():
    """Get frame type distribution with tension metrics"""
    try:
        resp = await http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/distribution")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@app.get("/api/v1/narratives/high-tension", tags=["Narratives"])
async def get_high_tension_narratives(
    min_tension: float = Query(0.7, ge=0.0, le=1.0, description="Minimum tension threshold"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Get narratives above tension threshold"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/high-tension",
            params={"min_tension": min_tension, "limit": limit}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@app.get("/api/v1/narratives/top-entities", tags=["Entities"])
async def get_top_entities(
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Get most mentioned entities in narratives"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/top-entities",
            params={"limit": limit}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


# === Entity-Specific Endpoints ===

@app.get("/api/v1/entity/{entity_name}", tags=["Entities"])
async def get_entity_narratives(
    entity_name: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get all narratives mentioning an entity"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/frames/{entity_name}",
            params={"limit": limit}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@app.get("/api/v1/entity/{entity_name}/framing", tags=["Entities"])
async def get_entity_framing(entity_name: str):
    """Get framing analysis for a specific entity"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/entity-framing/{entity_name}"
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@app.get("/api/v1/entity/{entity_name}/history", tags=["Entities"])
async def get_entity_tension_history(
    entity_name: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get historical tension data for an entity"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/entity/{entity_name}/history",
            params={"days": days}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


# === Co-occurrence Analysis ===

@app.get("/api/v1/cooccurrence", tags=["Analysis"])
async def get_entity_cooccurrence(
    min_shared: int = Query(3, ge=1, description="Minimum shared narratives"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get entity co-occurrence patterns"""
    try:
        resp = await http_client.get(
            f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/cooccurrence",
            params={"min_shared": min_shared, "limit": limit}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


# === Dashboard Data Aggregation ===

@app.get("/api/v1/dashboard/overview", tags=["Dashboard"])
async def get_dashboard_overview():
    """Aggregated data for dashboard overview"""
    try:
        # Parallel requests for dashboard data
        stats_req = http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/stats")
        frames_req = http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/distribution")
        entities_req = http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/top-entities?limit=10")
        tension_req = http_client.get(f"{KNOWLEDGE_GRAPH_URL}/api/v1/graph/narratives/high-tension?min_tension=0.8&limit=5")

        stats_resp, frames_resp, entities_resp, tension_resp = await asyncio.gather(
            stats_req, frames_req, entities_req, tension_req,
            return_exceptions=True
        )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats_resp.json() if not isinstance(stats_resp, Exception) else None,
            "frame_distribution": frames_resp.json() if not isinstance(frames_resp, Exception) else None,
            "top_entities": entities_resp.json() if not isinstance(entities_resp, Exception) else None,
            "high_tension": tension_resp.json() if not isinstance(tension_resp, Exception) else None
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


# === Webhook Registration ===

class WebhookSubscription(BaseModel):
    url: str
    events: List[str]  # e.g., ["high_tension", "frame_shift", "new_entity"]
    secret: Optional[str] = None


@app.post("/api/v1/webhooks/subscribe", tags=["Webhooks"])
async def subscribe_webhook(subscription: WebhookSubscription):
    """Register a webhook for narrative events"""
    # Store in database (ni_webhook_subscriptions table)
    # This is a placeholder - actual implementation would use PostgreSQL
    return {
        "id": "webhook-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "url": subscription.url,
        "events": subscription.events,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/webhooks", tags=["Webhooks"])
async def list_webhooks():
    """List all webhook subscriptions"""
    # Placeholder - would query ni_webhook_subscriptions
    return {"webhooks": [], "count": 0}


@app.delete("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def unsubscribe_webhook(webhook_id: str):
    """Remove a webhook subscription"""
    return {"id": webhook_id, "status": "deleted"}


# === Import asyncio for parallel requests ===
import asyncio


# === Startup/Shutdown ===

@app.on_event("startup")
async def startup():
    """Initialize connections"""
    pass


@app.on_event("shutdown")
async def shutdown():
    """Cleanup connections"""
    await http_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8114)
