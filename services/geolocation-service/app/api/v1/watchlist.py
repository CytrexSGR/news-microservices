"""Watchlist API endpoints for entity/country tracking and alerts.

Provides:
- GET/POST/DELETE /geo/watchlist     - Manage watchlist items
- GET /geo/watchlist/alerts          - Get alerts for watchlist
- POST /geo/watchlist/alerts/read    - Mark alerts as read
- GET /geo/watchlist/stats           - Alert statistics
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.security import (
    WatchlistItem,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemType,
    SecurityAlert,
    AlertList,
    AlertStats,
    ThreatLevel,
)

router = APIRouter(prefix="/geo/watchlist", tags=["watchlist"])

# Hardcoded user_id for now (single-user system)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_threat_level(priority_score: int) -> ThreatLevel:
    """Convert priority score to threat level."""
    if priority_score >= 9:
        return ThreatLevel.CRITICAL
    elif priority_score >= 7:
        return ThreatLevel.HIGH
    elif priority_score >= 5:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


# =============================================================================
# Watchlist CRUD
# =============================================================================

@router.get("", response_model=List[WatchlistItem])
async def get_watchlist(
    item_type: Optional[str] = Query(None, description="Filter by type: entity, country, keyword, region"),
    db: AsyncSession = Depends(get_db),
):
    """Get all watchlist items with match counts."""
    type_filter = "AND item_type = :item_type" if item_type else ""

    query = text(f"""
        WITH match_counts AS (
            SELECT
                w.id,
                COUNT(DISTINCT a.id) FILTER (WHERE a.created_at >= NOW() - INTERVAL '24 hours') as count_24h,
                COUNT(DISTINCT a.id) FILTER (WHERE a.created_at >= NOW() - INTERVAL '7 days') as count_7d,
                MAX(a.created_at) as last_match
            FROM security_watchlist w
            LEFT JOIN security_alerts a ON w.id = a.watchlist_id
            WHERE w.user_id = :user_id
            GROUP BY w.id
        )
        SELECT
            w.*,
            COALESCE(m.count_24h, 0) as match_count_24h,
            COALESCE(m.count_7d, 0) as match_count_7d,
            m.last_match as last_match_at
        FROM security_watchlist w
        LEFT JOIN match_counts m ON w.id = m.id
        WHERE w.user_id = :user_id
        {type_filter}
        ORDER BY w.priority DESC, w.created_at DESC
    """)

    params = {"user_id": DEFAULT_USER_ID}
    if item_type:
        params["item_type"] = item_type

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        WatchlistItem(
            id=r.id,
            user_id=r.user_id,
            item_type=r.item_type,
            item_value=r.item_value,
            display_name=r.display_name,
            notes=r.notes,
            priority=r.priority,
            notify_on_new=r.notify_on_new,
            notify_threshold=r.notify_threshold,
            created_at=r.created_at,
            updated_at=r.updated_at,
            match_count_24h=r.match_count_24h,
            match_count_7d=r.match_count_7d,
            last_match_at=r.last_match_at,
        )
        for r in rows
    ]


@router.post("", response_model=WatchlistItem)
async def add_watchlist_item(
    item: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add item to watchlist."""
    query = text("""
        INSERT INTO security_watchlist (user_id, item_type, item_value, display_name, notes, priority, notify_on_new, notify_threshold)
        VALUES (:user_id, :item_type, :item_value, :display_name, :notes, :priority, :notify_on_new, :notify_threshold)
        ON CONFLICT (user_id, item_type, item_value) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            notes = EXCLUDED.notes,
            priority = EXCLUDED.priority,
            notify_on_new = EXCLUDED.notify_on_new,
            notify_threshold = EXCLUDED.notify_threshold
        RETURNING *
    """)

    result = await db.execute(query, {
        "user_id": DEFAULT_USER_ID,
        "item_type": item.item_type.value,
        "item_value": item.item_value,
        "display_name": item.display_name or item.item_value,
        "notes": item.notes,
        "priority": item.priority,
        "notify_on_new": item.notify_on_new,
        "notify_threshold": item.notify_threshold,
    })
    await db.commit()
    r = result.fetchone()

    return WatchlistItem(
        id=r.id,
        user_id=r.user_id,
        item_type=r.item_type,
        item_value=r.item_value,
        display_name=r.display_name,
        notes=r.notes,
        priority=r.priority,
        notify_on_new=r.notify_on_new,
        notify_threshold=r.notify_threshold,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.delete("/{item_id}")
async def remove_watchlist_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove item from watchlist."""
    query = text("""
        DELETE FROM security_watchlist
        WHERE id = :item_id AND user_id = :user_id
        RETURNING id
    """)
    result = await db.execute(query, {"item_id": str(item_id), "user_id": DEFAULT_USER_ID})
    await db.commit()

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    return {"status": "deleted", "id": str(item_id)}


# =============================================================================
# Alerts
# =============================================================================

@router.get("/alerts", response_model=AlertList)
async def get_alerts(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts for user's watchlist items."""
    offset = (page - 1) * per_page
    unread_filter = "AND a.is_read = false" if unread_only else ""

    # Count total and unread
    count_query = text(f"""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE NOT a.is_read) as unread
        FROM security_alerts a
        JOIN security_watchlist w ON a.watchlist_id = w.id
        WHERE w.user_id = :user_id
    """)
    count_result = await db.execute(count_query, {"user_id": DEFAULT_USER_ID})
    counts = count_result.fetchone()

    # Get alerts
    query = text(f"""
        SELECT a.*
        FROM security_alerts a
        JOIN security_watchlist w ON a.watchlist_id = w.id
        WHERE w.user_id = :user_id
        {unread_filter}
        ORDER BY a.created_at DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, {
        "user_id": DEFAULT_USER_ID,
        "limit": per_page,
        "offset": offset,
    })

    alerts = [
        SecurityAlert(
            id=r.id,
            watchlist_id=r.watchlist_id,
            article_id=r.article_id,
            title=r.title,
            priority_score=r.priority_score,
            threat_level=get_threat_level(r.priority_score),
            country_code=r.country_code,
            matched_value=r.matched_value,
            is_read=r.is_read,
            created_at=r.created_at,
        )
        for r in result.fetchall()
    ]

    return AlertList(
        alerts=alerts,
        total=counts.total or 0,
        unread_count=counts.unread or 0,
        page=page,
        per_page=per_page,
    )


@router.post("/alerts/read")
async def mark_alerts_read(
    alert_ids: List[UUID] = Body(..., description="List of alert IDs to mark as read"),
    db: AsyncSession = Depends(get_db),
):
    """Mark alerts as read."""
    if not alert_ids:
        return {"updated": 0}

    query = text("""
        UPDATE security_alerts a
        SET is_read = true
        FROM security_watchlist w
        WHERE a.watchlist_id = w.id
          AND w.user_id = :user_id
          AND a.id = ANY(:alert_ids)
    """)

    result = await db.execute(query, {
        "user_id": DEFAULT_USER_ID,
        "alert_ids": [str(aid) for aid in alert_ids],
    })
    await db.commit()

    return {"updated": result.rowcount}


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics for notification badge."""
    query = text("""
        SELECT
            COUNT(*) FILTER (WHERE NOT a.is_read) as total_unread,
            COUNT(*) FILTER (WHERE NOT a.is_read AND a.priority_score >= 9) as critical_unread,
            COUNT(*) FILTER (WHERE NOT a.is_read AND a.priority_score >= 7 AND a.priority_score < 9) as high_unread,
            MAX(a.created_at) FILTER (WHERE NOT a.is_read) as last_alert_at
        FROM security_alerts a
        JOIN security_watchlist w ON a.watchlist_id = w.id
        WHERE w.user_id = :user_id
    """)

    result = await db.execute(query, {"user_id": DEFAULT_USER_ID})
    r = result.fetchone()

    return AlertStats(
        total_unread=r.total_unread or 0,
        critical_unread=r.critical_unread or 0,
        high_unread=r.high_unread or 0,
        last_alert_at=r.last_alert_at,
    )
