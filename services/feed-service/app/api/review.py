# File: services/feed-service/app/api/review.py
"""
Review Queue API Endpoints

HITL (Human-in-the-Loop) review workflow for AI-generated publications.
Supports risk-based review queue, approve/reject decisions, and audit trail.

Epic 2.3 Task 2.3.3: Review Queue API
Epic 2.3 Task 2.3.5: Risk Scoring Integration
Epic 2.3 Task 2.3.6: n8n Webhook for Review Alerts

Endpoints:
- POST /submit - Submit content for risk scoring and review
- GET /queue - List pending items (paginated)
- GET /queue/{item_id} - Get single item
- POST /queue/{item_id}/decision - Submit review decision
- GET /stats - Queue statistics
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.api.dependencies import get_current_user_id
from app.repositories.review_repository import ReviewRepository
from app.services.risk_scorer import get_risk_scorer
from app.services.alert_webhook import get_alert_webhook, should_send_alert
from app.schemas.review import (
    ReviewItemResponse,
    ReviewQueueListResponse,
    ReviewDecisionRequest,
    ReviewStatsResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewStatus,
    RiskLevel,
    ReviewDashboardResponse,
    DashboardStatsResponse,
    DashboardRecentItemResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/review", tags=["review"])


# =============================================================================
# POST /submit - Submit content for risk scoring and review
# =============================================================================


@router.post("/submit", response_model=ReviewSubmitResponse, status_code=201)
async def submit_for_review(
    request: ReviewSubmitRequest,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewSubmitResponse:
    """
    Submit content for risk scoring and review.

    Analyzes the content_preview for risky patterns using RiskScorer:
    - Legal language (lawsuit, litigation, settlement)
    - Allegations (accused, alleged, fraud)
    - Financial data (earnings, revenue, profit)
    - Investment advice (buy, sell, target price)
    - Unverified claims (reportedly, sources say)

    Based on the calculated risk score:
    - **score < 0.3**: Auto-approved (low risk)
    - **score >= 0.3**: Added to review queue (pending human review)
    - **score >= 0.7**: Triggers n8n webhook notification (if configured)

    Parameters:
    - **target_type**: Content type (sitrep, summary, alert)
    - **target_id**: UUID of the target content
    - **content_preview**: Text content to analyze for risk (max 5000 chars)
    - **metadata**: Optional additional metadata

    Returns:
    - Created review item with risk_score, risk_factors, and status

    Example:
    ```json
    {
        "target_type": "sitrep",
        "target_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_preview": "Breaking: Lawsuit filed alleging fraud...",
        "metadata": {"ai_generated": true, "source": "sitrep-service"}
    }
    ```
    """
    # Calculate risk score using RiskScorer
    scorer = get_risk_scorer()
    risk_result = scorer.calculate(request.content_preview)

    logger.info(
        f"Risk scoring for {request.target_type}/{request.target_id}: "
        f"score={risk_result.risk_score}, level={risk_result.level}, "
        f"flags={risk_result.flags}"
    )

    # Submit to review queue with risk-based routing
    repo = ReviewRepository(db)
    item = await repo.submit_for_review(
        target_type=request.target_type,
        target_id=request.target_id,
        risk_score=risk_result.risk_score,
        risk_factors=risk_result.flags,
        content_preview=request.content_preview,
        metadata=request.metadata,
        threshold=0.3,
    )

    # Determine risk level
    if risk_result.risk_score < 0.3:
        risk_level = RiskLevel.LOW
    elif risk_result.risk_score < 0.7:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.HIGH

    # Task 2.3.6: Send n8n webhook notification for HIGH risk items
    # Fire-and-forget: create task but don't await it (non-blocking)
    if should_send_alert(risk_result.risk_score):
        asyncio.create_task(
            _send_high_risk_alert(
                item_id=str(item.id),
                risk_score=risk_result.risk_score,
                risk_level=risk_level.value,
                flags=risk_result.flags,
                content_preview=item.content[:500] if item.content else "",
            )
        )
        logger.info(
            f"Scheduled high-risk alert webhook for item {item.id} "
            f"(risk_score={risk_result.risk_score})"
        )

    return ReviewSubmitResponse(
        id=item.id,
        target_type=item.target,
        target_id=str(item.article_id),
        risk_score=item.risk_score,
        risk_level=risk_level,
        risk_factors=risk_result.flags,
        status=ReviewStatus(item.status),
        content_preview=item.content[:500] if item.content else None,
        created_at=item.created_at,
    )


async def _send_high_risk_alert(
    item_id: str,
    risk_score: float,
    risk_level: str,
    flags: list,
    content_preview: str,
) -> None:
    """
    Background task to send high-risk item alert via webhook.

    Handles failures gracefully - logs errors but doesn't raise exceptions.
    """
    try:
        webhook = get_alert_webhook()
        success = await webhook.send_high_risk_alert(
            item_id=item_id,
            risk_score=risk_score,
            risk_level=risk_level,
            flags=flags,
            content_preview=content_preview,
        )
        if not success:
            logger.debug(
                f"High-risk alert not sent for item {item_id} "
                "(webhook disabled or failed)"
            )
    except Exception as e:
        # Log but don't raise - this is a background task
        logger.error(f"Error sending high-risk alert for item {item_id}: {e}")


# =============================================================================
# GET /queue - List pending review items
# =============================================================================


@router.get("/queue", response_model=ReviewQueueListResponse)
async def list_pending_reviews(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    min_risk_score: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Filter by minimum risk score"
    ),
    target_type: Optional[str] = Query(
        None, description="Filter by target type (sitrep, summary, alert)"
    ),
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewQueueListResponse:
    """
    Get pending review items with pagination.

    Returns items sorted by risk score (highest first).

    Parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **min_risk_score**: Filter items with risk >= this score
    - **target_type**: Filter by target type (sitrep, summary, alert)

    Returns:
    - Paginated list of pending review items
    - Total count and high-risk count
    - Pagination metadata
    """
    repo = ReviewRepository(db)

    result = await repo.list_pending(
        page=page,
        page_size=page_size,
        min_risk_score=min_risk_score,
        target_type=target_type,
    )

    return result


# =============================================================================
# GET /queue/{item_id} - Get single review item
# =============================================================================


@router.get("/queue/{item_id}", response_model=ReviewItemResponse)
async def get_review_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewItemResponse:
    """
    Get a specific review item by ID.

    Parameters:
    - **item_id**: UUID of the review item

    Returns:
    - Review item details including risk_level calculated from risk_score

    Raises:
    - 404: Review item not found
    """
    repo = ReviewRepository(db)
    item = await repo.get_item(item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Review item not found: {item_id}",
        )

    return item


# =============================================================================
# POST /queue/{item_id}/decision - Submit review decision
# =============================================================================


@router.post("/queue/{item_id}/decision", response_model=ReviewItemResponse)
async def submit_review_decision(
    item_id: UUID,
    decision: ReviewDecisionRequest,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewItemResponse:
    """
    Submit a review decision for an item.

    Decisions:
    - **approve**: Approve for publication
    - **reject**: Reject (requires rejection_reason)
    - **approve_with_edits**: Approve with modifications (include edited_content)
    - **escalate**: Escalate for further review (keeps pending status)

    Parameters:
    - **item_id**: UUID of the review item
    - **decision**: Decision type and optional notes

    Returns:
    - Updated review item with new status

    Raises:
    - 404: Review item not found
    - 400: Item already reviewed
    - 422: Validation error (e.g., missing rejection_reason)
    """
    repo = ReviewRepository(db)

    # Check item exists
    existing = await repo.get_item(item_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Review item not found: {item_id}",
        )

    # Check item is still pending
    if existing.status.value != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Item already reviewed (status: {existing.status.value})",
        )

    # Update decision
    updated = await repo.update_decision(
        item_id=item_id,
        decision=decision,
        reviewer_id=user_id,
    )

    if updated is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update review decision",
        )

    logger.info(
        f"Review decision submitted: item={item_id}, "
        f"decision={decision.decision}, reviewer={user_id}"
    )

    return updated


# =============================================================================
# GET /stats - Queue statistics
# =============================================================================


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewStatsResponse:
    """
    Get review queue statistics.

    Returns:
    - Total pending items
    - Items reviewed today
    - Auto-approved count
    - Rejected count
    - Risk distribution (low/medium/high counts)
    """
    repo = ReviewRepository(db)
    stats = await repo.get_stats()

    return stats


# =============================================================================
# GET /dashboard - Review Queue Dashboard Overview
# Epic 2.3 Task 2.3.7: Create Review Queue Dashboard Endpoint
# =============================================================================


@router.get("/dashboard", response_model=ReviewDashboardResponse)
async def get_review_dashboard(
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> ReviewDashboardResponse:
    """
    Get review queue dashboard overview data.

    Returns comprehensive dashboard data for the Review Queue overview page:
    - **stats**: Summary statistics (pending count, high-risk count, reviewed today)
    - **recent_items**: Recent pending items sorted by risk score (highest first)
    - **risk_distribution**: Count of pending items by risk level (low/medium/high)

    The recent_items list is limited to 5 items and sorted by risk_score descending
    to highlight items that need immediate attention.

    Example Response:
    ```json
    {
        "stats": {
            "total_pending": 15,
            "high_risk_count": 3,
            "reviewed_today": 7,
            "auto_approved_count": 42
        },
        "recent_items": [
            {
                "id": "...",
                "target_type": "sitrep",
                "risk_score": 0.85,
                "risk_level": "high",
                "created_at": "2026-01-22T10:30:00Z"
            }
        ],
        "risk_distribution": {
            "low": 5,
            "medium": 7,
            "high": 3
        }
    }
    ```
    """
    repo = ReviewRepository(db)
    dashboard_data = await repo.get_dashboard_data()

    # Convert recent_items to DashboardRecentItemResponse format
    recent_items = [
        DashboardRecentItemResponse(
            id=item.id,
            target_type=item.target_type,
            risk_score=item.risk_score,
            risk_level=item.risk_level,
            created_at=item.created_at,
        )
        for item in dashboard_data["recent_items"]
    ]

    return ReviewDashboardResponse(
        stats=DashboardStatsResponse(**dashboard_data["stats"]),
        recent_items=recent_items,
        risk_distribution=dashboard_data["risk_distribution"],
    )
