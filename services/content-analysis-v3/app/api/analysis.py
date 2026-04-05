"""
Analysis endpoints for Content-Analysis-V3 pipeline
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
import asyncpg
from datetime import datetime

from app.core.database import get_db_pool
from app.pipeline.tier0.triage import Tier0Triage
from app.pipeline.tier1.foundation import Tier1Foundation
from app.pipeline.tier2.orchestrator import Tier2Orchestrator
from app.models.schemas import TriageDecision, Tier1Results
from app.infrastructure.graph_client import V3GraphClient
from app.messaging import get_event_publisher
from fastapi import Request

# Import JWT authentication dependencies
from app.api.dependencies import get_authenticated_user, get_optional_authenticated_user, UserInfo

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeArticleRequest(BaseModel):
    """Request model for article analysis."""

    article_id: UUID = Field(..., description="Unique article identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    content: str = Field(..., min_length=10, description="Article content")
    run_tier2: bool = Field(default=True, description="Run Tier2 specialist analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Federal Reserve Raises Interest Rates",
                "url": "https://example.com/fed-rates",
                "content": "The Federal Reserve announced today...",
                "run_tier2": True
            }
        }


class AnalysisStatus(BaseModel):
    """Status of article analysis."""

    article_id: UUID
    status: str = Field(..., description="pending, tier0_complete, tier1_complete, tier2_complete, failed")
    tier0_complete: bool = False
    tier1_complete: bool = False
    tier2_complete: bool = False
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisResponse(BaseModel):
    """Response for analysis request."""

    article_id: UUID
    status: str
    message: str
    tier0_complete: bool = False
    tier1_complete: bool = False
    tier2_complete: bool = False


# ============================================================================
# Analysis Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_article(
    request: AnalyzeArticleRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: UserInfo = Depends(get_authenticated_user)
) -> AnalysisResponse:
    """
    Analyze an article through the V3 pipeline.

    Pipeline:
    1. Tier0: Triage (keep/discard decision)
    2. Tier1: Foundation extraction (entities, relations, topics)
    3. Tier2: Specialist analysis (5 specialized modules)

    Args:
        request: Article data and analysis configuration
        background_tasks: FastAPI background tasks
        db_pool: Database connection pool

    Returns:
        Analysis status and metadata
    """
    article_id = request.article_id

    # Check if article already analyzed
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM triage_decisions WHERE article_id = $1",
            article_id
        )

        if existing:
            return AnalysisResponse(
                article_id=article_id,
                status="already_analyzed",
                message="Article already analyzed",
                tier0_complete=True,
                tier1_complete=True,  # Assume complete if tier0 exists
                tier2_complete=True   # Assume complete if tier0 exists
            )

    # Run analysis in background
    graph_client = getattr(req.app.state, "graph_client", None)
    background_tasks.add_task(
        _run_analysis_pipeline,
        db_pool,
        graph_client,
        article_id,
        request.title,
        str(request.url),
        request.content,
        request.run_tier2
    )

    return AnalysisResponse(
        article_id=article_id,
        status="processing",
        message="Analysis started",
        tier0_complete=False,
        tier1_complete=False,
        tier2_complete=False
    )


@router.get("/status/{article_id}", response_model=AnalysisStatus)
async def get_analysis_status(
    article_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: Optional[UserInfo] = Depends(get_optional_authenticated_user)
) -> AnalysisStatus:
    """
    Get analysis status for an article.

    **DEPRECATED:** This endpoint uses legacy tables that no longer exist in V3.
    V3 data is stored in public.article_analysis table via event-driven architecture.

    TODO: Rewrite to query public.article_analysis table instead of legacy tables.

    Args:
        article_id: Article UUID
        db_pool: Database connection pool

    Returns:
        Current analysis status (mocked for now)
    """
    # TEMPORARY: Return mock response until endpoint is rewritten for unified table
    return AnalysisStatus(
        article_id=article_id,
        status="unknown",
        tier0_complete=False,
        tier1_complete=False,
        tier2_complete=False,
        created_at=datetime.utcnow(),
        completed_at=None
    )

    # LEGACY CODE (commented out - references non-existent tables):
    # async with db_pool.acquire() as conn:
    #     # Check Tier0
    #     tier0_result = await conn.fetchrow(
    #         "SELECT created_at FROM triage_decisions WHERE article_id = $1",
    #         article_id
    #     )
    #
    #     tier0_complete = tier0_result is not None
    #
    #     # Check Tier1
    #     tier1_result = await conn.fetchrow(
    #         "SELECT created_at FROM tier1_scores WHERE article_id = $1",
    #         article_id
    #     )
    #
    #     tier1_complete = tier1_result is not None
    #
    #     # Check Tier2
    #     tier2_result = await conn.fetchval(
    #         "SELECT COUNT(*) FROM tier2_specialist_results WHERE article_id = $1",
    #         article_id
    #     )
    #
    #     tier2_complete = tier2_result > 0
    #
    #     # Determine status
    #     if not tier0_complete:
    #         status = "pending"
    #         created_at = datetime.utcnow()
    #         completed_at = None
    #     elif not tier1_complete:
    #         status = "tier0_complete"
    #         created_at = tier0_result["created_at"]
    #         completed_at = None
    #     elif not tier2_complete:
    #         status = "tier1_complete"
    #         created_at = tier0_result["created_at"]
    #         completed_at = None
    #     else:
    #         status = "tier2_complete"
    #         created_at = tier0_result["created_at"]
    #         completed_at = tier1_result["created_at"]  # Use tier1 completion as proxy
    #
    #     return AnalysisStatus(
    #         article_id=article_id,
    #         status=status,
    #         tier0_complete=tier0_complete,
    #         tier1_complete=tier1_complete,
    #         tier2_complete=tier2_complete,
    #         created_at=created_at,
    #         completed_at=completed_at
    #     )


@router.get("/results/{article_id}")
async def get_analysis_results(
    article_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: UserInfo = Depends(get_authenticated_user)
) -> Dict[str, Any]:
    """
    Get complete analysis results for an article.

    Returns all tiers: Tier0, Tier1, Tier2
    Reads from unified article_analysis table (Phase 3.1)

    Args:
        article_id: Article UUID
        db_pool: Database connection pool

    Returns:
        Complete analysis results
    """
    results = {
        "article_id": str(article_id),
        "tier0": None,
        "tier1": None,
        "tier2": None
    }

    async with db_pool.acquire() as conn:
        # Get analysis from unified table (Phase 3.1)
        row = await conn.fetchrow(
            """
            SELECT
                triage_results,
                tier1_results,
                tier2_results,
                pipeline_version,
                success,
                created_at
            FROM article_analysis
            WHERE article_id = $1 AND pipeline_version = '3.0'
            """,
            article_id
        )

        if not row:
            raise HTTPException(status_code=404, detail="V3 analysis not found for this article")

        # Extract JSONB results
        results["tier0"] = row["triage_results"]
        results["tier1"] = row["tier1_results"]
        results["tier2"] = row["tier2_results"]
        results["pipeline_version"] = row["pipeline_version"]
        results["success"] = row["success"]
        results["created_at"] = row["created_at"].isoformat() if row["created_at"] else None

    return results


@router.get("/results/{article_id}/tier0")
async def get_tier0_results(
    article_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: UserInfo = Depends(get_authenticated_user)
) -> Dict[str, Any]:
    """Get Tier0 (triage) results only. Reads from unified article_analysis table (Phase 3.1)"""

    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT triage_results
            FROM article_analysis
            WHERE article_id = $1 AND pipeline_version = '3.0'
            """,
            article_id
        )

        if not result or result["triage_results"] is None:
            raise HTTPException(status_code=404, detail="Tier0 results not found")

        return result["triage_results"]


@router.get("/results/{article_id}/tier1")
async def get_tier1_results(
    article_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: UserInfo = Depends(get_authenticated_user)
) -> Dict[str, Any]:
    """Get Tier1 (foundation extraction) results only. Reads from unified article_analysis table (Phase 3.1)"""

    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT tier1_results
            FROM article_analysis
            WHERE article_id = $1 AND pipeline_version = '3.0'
            """,
            article_id
        )

        if not result or result["tier1_results"] is None:
            raise HTTPException(status_code=404, detail="Tier1 results not found")

        return result["tier1_results"]


@router.get("/results/{article_id}/tier2")
async def get_tier2_results(
    article_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: UserInfo = Depends(get_authenticated_user)
) -> Dict[str, Any]:
    """Get Tier2 (specialist analysis) results only. Reads from unified article_analysis table (Phase 3.1)"""

    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT tier2_results
            FROM article_analysis
            WHERE article_id = $1 AND pipeline_version = '3.0'
            """,
            article_id
        )

        if not result or result["tier2_results"] is None:
            raise HTTPException(status_code=404, detail="Tier2 results not found")

        return result["tier2_results"]


# ============================================================================
# Background Tasks
# ============================================================================

async def _run_analysis_pipeline(
    db_pool: asyncpg.Pool,
    graph_client: Optional[V3GraphClient],
    article_id: UUID,
    title: str,
    url: str,
    content: str,
    run_tier2: bool = True
):
    """
    Run complete analysis pipeline in background.

    This function executes:
    1. Tier0: Triage
    2. Tier1: Foundation Extraction (if Tier0 says keep)
    3. Tier2: Specialist Analysis (if run_tier2=True)
    4. Graph Publishing (if graph_client available)
    5. Event Publishing (analysis.v3.completed or analysis.v3.failed)
    """
    event_publisher = await get_event_publisher()
    tier0_data = None
    tier1_data = None
    tier2_data = None

    try:
        # Tier0: Triage
        tier0 = Tier0Triage(db_pool)
        triage_decision = await tier0.execute(
            article_id=article_id,
            title=title,
            url=url,
            content=content
        )

        tier0_data = {
            "priority_score": triage_decision.PriorityScore,
            "category": triage_decision.category,
            "keep": triage_decision.keep,
            "tokens_used": triage_decision.tokens_used,
            "cost_usd": triage_decision.cost_usd
        }

        # Publish Tier0 to graph (create Article node)
        if graph_client:
            try:
                await graph_client.create_article_node(
                    article_id=str(article_id),
                    tier0_data={
                        "PriorityScore": triage_decision.PriorityScore,
                        "category": triage_decision.category,
                        "keep": triage_decision.keep,
                        "tokens_used": triage_decision.tokens_used,
                        "cost_usd": triage_decision.cost_usd
                    },
                    article_metadata={
                        "title": title,
                        "published_at": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                print(f"[WARNING] Failed to publish Tier0 to graph: {e}")

        # If discarded, publish completion event and stop
        if not triage_decision.keep:
            if event_publisher.is_connected():
                await event_publisher.publish_event(
                    event_type="analysis.v3.completed",
                    payload={
                        "article_id": str(article_id),
                        "success": True,
                        "pipeline_version": "3.0",
                        "discarded": True,
                        "tier0": tier0_data,
                        "metrics": {
                            "total_tokens": tier0_data["tokens_used"],
                            "total_cost_usd": tier0_data["cost_usd"]
                        }
                    }
                )
            return

        # Tier1: Foundation Extraction
        tier1 = Tier1Foundation(db_pool)
        tier1_results = await tier1.execute(
            article_id=article_id,
            title=title,
            url=url,
            content=content
        )

        tier1_data = {
            "entities_count": len(tier1_results.entities),
            "relations_count": len(tier1_results.relations),
            "topics_count": len(tier1_results.topics),
            "tokens_used": tier1_results.tokens_used,
            "cost_usd": tier1_results.cost_usd
        }

        # Publish Tier1 to graph (entities, relations, topics)
        if graph_client:
            try:
                await graph_client.publish_tier1(
                    article_id=str(article_id),
                    tier1_data={
                        "entities": [
                            {
                                "name": e.name,
                                "type": e.entity_type,
                                "relevance": getattr(e, "relevance", 0.0)
                            }
                            for e in tier1_results.entities
                        ],
                        "relations": [
                            {
                                "source": r.source_entity,
                                "target": r.target_entity,
                                "type": r.relation_type,
                                "confidence": getattr(r, "confidence", 0.0)
                            }
                            for r in tier1_results.relations
                        ],
                        "topics": [t.topic for t in tier1_results.topics]
                    }
                )
            except Exception as e:
                print(f"[WARNING] Failed to publish Tier1 to graph: {e}")

        # Tier2: Specialist Analysis (optional)
        if run_tier2:
            tier2 = Tier2Orchestrator(db_pool)
            tier2_results = await tier2.analyze_article(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results
            )

            if tier2_results:
                tier2_data = {
                    "specialists_executed": getattr(tier2_results, "specialists_executed", 0),
                    "total_tokens": getattr(tier2_results, "total_tokens", 0),
                    "total_cost_usd": getattr(tier2_results, "total_cost_usd", 0.0)
                }

                # Publish Tier2 to graph (specialist findings)
                if graph_client and tier2_results:
                    try:
                        # TODO: Extract specialist data from tier2_results
                        # This depends on tier2_results structure
                        # For now, skip graph publishing for Tier2
                        pass
                    except Exception as e:
                        print(f"[WARNING] Failed to publish Tier2 to graph: {e}")

        # Publish completion event
        total_tokens = tier0_data["tokens_used"] + tier1_data.get("tokens_used", 0) + (tier2_data.get("total_tokens", 0) if tier2_data else 0)
        total_cost = tier0_data["cost_usd"] + tier1_data.get("cost_usd", 0.0) + (tier2_data.get("total_cost_usd", 0.0) if tier2_data else 0.0)

        if event_publisher.is_connected():
            await event_publisher.publish_event(
                event_type="analysis.v3.completed",
                payload={
                    "article_id": str(article_id),
                    "success": True,
                    "pipeline_version": "3.0",
                    "discarded": False,
                    "tier0": tier0_data,
                    "tier1": tier1_data if tier1_data else None,
                    "tier2": tier2_data if tier2_data else None,
                    "metrics": {
                        "total_tokens": total_tokens,
                        "total_cost_usd": total_cost
                    }
                }
            )

    except Exception as e:
        # Log error (would use proper logging in production)
        print(f"[ERROR] Analysis pipeline failed for {article_id}: {e}")

        # Publish failure event
        event_publisher = await get_event_publisher()
        if event_publisher.is_connected():
            await event_publisher.publish_event(
                event_type="analysis.v3.failed",
                payload={
                    "article_id": str(article_id),
                    "success": False,
                    "pipeline_version": "3.0",
                    "error": str(e),
                    "tier0": tier0_data if tier0_data else None,
                    "tier1": tier1_data if tier1_data else None,
                    "tier2": tier2_data if tier2_data else None
                }
            )
