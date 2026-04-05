# services/clustering-service/app/api/v1/bursts.py
"""API endpoints for burst detection management."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.models.burst_alert import BurstAlert

logger = logging.getLogger(__name__)

router = APIRouter()


# Valid categories (aligned with Tier-0 Triage Agent)
VALID_CATEGORIES = [
    "conflict", "finance", "politics", "humanitarian",
    "security", "technology", "other", "crypto",
]


# Schemas
class BurstAlertResponse(BaseModel):
    """Response schema for a burst alert."""
    id: UUID
    cluster_id: UUID
    severity: str
    velocity: int
    window_minutes: int
    alert_sent: bool
    alert_sent_at: Optional[datetime] = None
    detected_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    # New fields for category-based filtering
    title: Optional[str] = None
    category: Optional[str] = None
    tension_score: Optional[float] = None
    growth_rate: Optional[float] = None
    top_entities: Optional[list] = None
    # Article time range
    first_article_at: Optional[datetime] = None
    last_article_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BurstListResponse(BaseModel):
    """Paginated burst alerts response."""
    items: List[BurstAlertResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class BurstStatsResponse(BaseModel):
    """Burst detection statistics."""
    total_bursts_24h: int
    total_bursts_7d: int
    by_severity: dict
    avg_velocity: float


class ClusterBurstHistoryResponse(BaseModel):
    """Burst history for a specific cluster."""
    cluster_id: UUID
    alerts: List[BurstAlertResponse]
    total: int


class AcknowledgeResponse(BaseModel):
    """Response after acknowledging a burst."""
    id: UUID
    acknowledged: bool
    acknowledged_at: datetime
    acknowledged_by: str


# Endpoints
@router.get("", response_model=BurstListResponse)
async def list_bursts(
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(
        None,
        description="Filter by category (conflict, finance, politics, humanitarian, security, technology, other, crypto)",
    ),
    deduplicate: bool = Query(
        True,
        description="If true, show only latest alert per cluster (default: true)",
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List recent burst alerts with pagination.

    Returns burst alerts detected within the specified time window.
    Supports filtering by severity and category.
    When deduplicate=true (default), only the latest alert per cluster is returned.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Validate category if provided
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{category}'. Valid: {', '.join(VALID_CATEGORIES)}",
        )

    if deduplicate:
        # Use DISTINCT ON to get only the latest alert per cluster
        # PostgreSQL-specific: DISTINCT ON with ORDER BY
        from sqlalchemy import text

        # Build WHERE clause conditions
        conditions = ["detected_at >= :cutoff"]
        params = {"cutoff": cutoff, "limit": limit, "offset": offset}

        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if category:
            conditions.append("category = :category")
            params["category"] = category

        where_clause = " AND ".join(conditions)

        # Count unique clusters
        count_sql = text(f"""
            SELECT COUNT(DISTINCT cluster_id)
            FROM burst_alerts
            WHERE {where_clause}
        """)
        total_result = await db.execute(count_sql, params)
        total = total_result.scalar() or 0

        # Get latest alert per cluster using DISTINCT ON
        query_sql = text(f"""
            SELECT DISTINCT ON (cluster_id) *
            FROM burst_alerts
            WHERE {where_clause}
            ORDER BY cluster_id, detected_at DESC
        """)

        # Wrap for final ordering and pagination
        final_sql = text(f"""
            SELECT * FROM (
                SELECT DISTINCT ON (cluster_id) *
                FROM burst_alerts
                WHERE {where_clause}
                ORDER BY cluster_id, detected_at DESC
            ) sub
            ORDER BY detected_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(final_sql, params)
        rows = result.mappings().all()

        # Convert to BurstAlert instances for response
        alerts = [BurstAlertResponse(**dict(row)) for row in rows]
    else:
        # Original behavior: return all alerts
        query = select(BurstAlert).where(BurstAlert.detected_at >= cutoff)

        if severity:
            query = query.where(BurstAlert.severity == severity)

        if category:
            query = query.where(BurstAlert.category == category)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(BurstAlert.detected_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        db_alerts = result.scalars().all()
        alerts = [BurstAlertResponse.model_validate(a) for a in db_alerts]

    return BurstListResponse(
        items=alerts,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(alerts) < total,
    )


@router.get("/active", response_model=BurstListResponse)
async def list_active_bursts(
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(
        None,
        description="Filter by category (conflict, finance, politics, humanitarian, security, technology, other, crypto)",
    ),
    deduplicate: bool = Query(
        True,
        description="If true, show only latest alert per cluster (default: true)",
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List currently active (unacknowledged) burst alerts.

    Returns recent burst detections that haven't been acknowledged yet.
    Supports filtering by severity and category.
    When deduplicate=true (default), only the latest alert per cluster is returned.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Validate category if provided
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{category}'. Valid: {', '.join(VALID_CATEGORIES)}",
        )

    if deduplicate:
        from sqlalchemy import text

        # Build WHERE clause conditions (active = not acknowledged)
        conditions = ["detected_at >= :cutoff", "acknowledged = false"]
        params = {"cutoff": cutoff, "limit": limit, "offset": offset}

        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if category:
            conditions.append("category = :category")
            params["category"] = category

        where_clause = " AND ".join(conditions)

        # Count unique clusters
        count_sql = text(f"""
            SELECT COUNT(DISTINCT cluster_id)
            FROM burst_alerts
            WHERE {where_clause}
        """)
        total_result = await db.execute(count_sql, params)
        total = total_result.scalar() or 0

        # Get latest alert per cluster using DISTINCT ON
        final_sql = text(f"""
            SELECT * FROM (
                SELECT DISTINCT ON (cluster_id) *
                FROM burst_alerts
                WHERE {where_clause}
                ORDER BY cluster_id, detected_at DESC
            ) sub
            ORDER BY detected_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(final_sql, params)
        rows = result.mappings().all()
        alerts = [BurstAlertResponse(**dict(row)) for row in rows]
    else:
        # Original behavior: return all alerts
        query = (
            select(BurstAlert)
            .where(BurstAlert.detected_at >= cutoff)
            .where(BurstAlert.acknowledged == False)  # noqa: E712
        )

        if severity:
            query = query.where(BurstAlert.severity == severity)

        if category:
            query = query.where(BurstAlert.category == category)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(BurstAlert.detected_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        db_alerts = result.scalars().all()
        alerts = [BurstAlertResponse.model_validate(a) for a in db_alerts]

    return BurstListResponse(
        items=alerts,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(alerts) < total,
    )


@router.get("/stats", response_model=BurstStatsResponse)
async def get_burst_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get burst detection statistics.

    Returns aggregate statistics for burst detection activity.
    """
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    # Count 24h
    result_24h = await db.execute(
        select(func.count()).select_from(BurstAlert)
        .where(BurstAlert.detected_at >= cutoff_24h)
    )
    total_24h = result_24h.scalar() or 0

    # Count 7d
    result_7d = await db.execute(
        select(func.count()).select_from(BurstAlert)
        .where(BurstAlert.detected_at >= cutoff_7d)
    )
    total_7d = result_7d.scalar() or 0

    # By severity (last 7d)
    by_severity = {}
    for sev in ["low", "medium", "high", "critical"]:
        result = await db.execute(
            select(func.count()).select_from(BurstAlert)
            .where(BurstAlert.detected_at >= cutoff_7d)
            .where(BurstAlert.severity == sev)
        )
        by_severity[sev] = result.scalar() or 0

    # Average velocity
    result_avg = await db.execute(
        select(func.avg(BurstAlert.velocity))
        .where(BurstAlert.detected_at >= cutoff_7d)
    )
    avg_velocity = result_avg.scalar() or 0.0

    return BurstStatsResponse(
        total_bursts_24h=total_24h,
        total_bursts_7d=total_7d,
        by_severity=by_severity,
        avg_velocity=float(avg_velocity),
    )


@router.get("/{burst_id}", response_model=BurstAlertResponse)
async def get_burst(
    burst_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get details of a specific burst alert.

    Args:
        burst_id: UUID of the burst alert
    """
    alert = await db.get(BurstAlert, burst_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Burst alert not found")

    return BurstAlertResponse.model_validate(alert)


@router.post("/{burst_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_burst(
    burst_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Acknowledge a burst alert.

    Marks the burst as acknowledged so it no longer appears in active bursts.
    """
    alert = await db.get(BurstAlert, burst_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Burst alert not found")

    if alert.acknowledged:
        raise HTTPException(
            status_code=400,
            detail="Burst already acknowledged"
        )

    now = datetime.now(timezone.utc)
    alert.acknowledged = True
    alert.acknowledged_at = now
    alert.acknowledged_by = user_id

    await db.commit()
    await db.refresh(alert)

    logger.info(f"Burst {burst_id} acknowledged by user {user_id}")

    return AcknowledgeResponse(
        id=alert.id,
        acknowledged=alert.acknowledged,
        acknowledged_at=now,
        acknowledged_by=user_id,
    )


@router.get("/cluster/{cluster_id}", response_model=ClusterBurstHistoryResponse)
async def get_cluster_burst_history(
    cluster_id: UUID,
    hours: int = Query(168, ge=1, le=720, description="Look back hours"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get burst history for a specific cluster.

    Returns all burst alerts for the specified cluster within the time window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(BurstAlert)
        .where(BurstAlert.cluster_id == cluster_id)
        .where(BurstAlert.detected_at >= cutoff)
        .order_by(BurstAlert.detected_at.desc())
    )

    result = await db.execute(query)
    alerts = result.scalars().all()

    return ClusterBurstHistoryResponse(
        cluster_id=cluster_id,
        alerts=[BurstAlertResponse.model_validate(a) for a in alerts],
        total=len(alerts),
    )
