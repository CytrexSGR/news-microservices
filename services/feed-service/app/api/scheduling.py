"""
Feed Scheduling API Endpoints

Provides API endpoints for intelligent feed scheduling management,
allowing frontend visualization and manual optimization.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from datetime import datetime, timedelta, timezone

from app.db import get_async_db
from app.services.feed_scheduler import FeedScheduleOptimizer
from app.api.dependencies import get_current_user_id

router = APIRouter()


@router.get("/timeline")
async def get_schedule_timeline(
    hours: int = 24,
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Get feed schedule timeline for visualization.

    Returns feeds grouped by time slots for the next N hours.

    Args:
        hours: Number of hours to look ahead (default: 24, max: 168)
        db: Database session
        user_id: Current user ID

    Returns:
        Dictionary with timeline data and statistics
    """
    if hours < 1 or hours > 168:
        raise HTTPException(status_code=400, detail="hours must be between 1 and 168")

    optimizer = FeedScheduleOptimizer()

    # Get feeds
    from sqlalchemy import select, and_
    from app.models import Feed

    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=hours)

    result = await db.execute(
        select(Feed).where(
            and_(
                Feed.is_active == True,
                Feed.next_fetch_at.isnot(None),
                Feed.next_fetch_at >= now,
                Feed.next_fetch_at <= end_time
            )
        ).order_by(Feed.next_fetch_at)
    )
    feeds = result.scalars().all()

    # Group by 5-minute slots
    from collections import defaultdict
    timeline = defaultdict(list)

    for feed in feeds:
        # Round to 5-minute bucket
        bucket_time = feed.next_fetch_at.replace(second=0, microsecond=0)
        bucket_minutes = bucket_time.minute - (bucket_time.minute % 5)
        bucket_time = bucket_time.replace(minute=bucket_minutes)

        timeline[bucket_time.isoformat()].append({
            "id": str(feed.id),
            "name": feed.name,
            "fetch_interval": feed.fetch_interval,
            "next_fetch_at": feed.next_fetch_at.isoformat(),
            "priority": feed.scheduling_priority
        })

    # Calculate statistics
    max_concurrent = max([len(feeds) for feeds in timeline.values()]) if timeline else 0
    total_slots = len(timeline)
    avg_feeds_per_slot = sum([len(feeds) for feeds in timeline.values()]) / total_slots if total_slots > 0 else 0

    return {
        "start_time": now.isoformat(),
        "end_time": end_time.isoformat(),
        "hours": hours,
        "total_feeds": len(feeds),
        "total_slots": total_slots,
        "max_concurrent_feeds": max_concurrent,
        "avg_feeds_per_slot": round(avg_feeds_per_slot, 2),
        "timeline": dict(timeline)
    }


@router.get("/distribution")
async def get_schedule_distribution(
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Get current schedule distribution statistics.

    Returns:
        Distribution metrics and quality score
    """
    optimizer = FeedScheduleOptimizer()
    return await optimizer.get_distribution_stats(db)


@router.post("/optimize")
async def optimize_schedule(
    apply: bool = False,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> Dict:
    """
    Calculate and optionally apply schedule optimization.

    Args:
        apply: If True, apply changes to database. If False, return preview only.
        db: Database session
        user_id: Current user ID

    Returns:
        Optimization results and statistics
    """
    optimizer = FeedScheduleOptimizer()
    return await optimizer.calculate_optimal_distribution(db, apply_immediately=apply)


@router.get("/conflicts")
async def detect_scheduling_conflicts(
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Detect scheduling conflicts (clusters of feeds).

    Returns:
        Conflict analysis and rebalancing suggestions
    """
    optimizer = FeedScheduleOptimizer()
    return await optimizer.suggest_rebalancing(db)


@router.get("/stats")
async def get_scheduling_stats(
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Get comprehensive scheduling statistics.

    Returns:
        Overall scheduling health metrics
    """
    from sqlalchemy import select, and_, func
    from app.models import Feed

    # Get feed counts by interval
    result = await db.execute(
        select(
            Feed.fetch_interval,
            func.count(Feed.id).label('count')
        )
        .where(Feed.is_active == True)
        .group_by(Feed.fetch_interval)
        .order_by(Feed.fetch_interval)
    )
    interval_distribution = {row.fetch_interval: row.count for row in result}

    # Get optimizer stats
    optimizer = FeedScheduleOptimizer()
    distribution_stats = await optimizer.get_distribution_stats(db)
    clusters = await optimizer.detect_clustering(db)

    return {
        "interval_distribution": interval_distribution,
        "distribution_score": distribution_stats.get("distribution_score"),
        "max_concurrent_feeds": distribution_stats.get("max_concurrent_feeds"),
        "total_active_feeds": distribution_stats.get("total_active_feeds"),
        "clusters_detected": len(clusters),
        "max_cluster_size": max([len(c) for c in clusters]) if clusters else 0,
        "recommendation": distribution_stats.get("recommendation"),
        "health_status": (
            "excellent" if distribution_stats.get("distribution_score", 0) > 80 else
            "good" if distribution_stats.get("distribution_score", 0) > 60 else
            "fair" if distribution_stats.get("distribution_score", 0) > 40 else
            "poor"
        )
    }


@router.put("/feeds/{feed_id}/schedule")
async def reschedule_feed(
    feed_id: str,
    offset_minutes: int,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> Dict:
    """
    Manually reschedule a specific feed.

    Args:
        feed_id: Feed UUID
        offset_minutes: New offset in minutes (0 to fetch_interval)
        db: Database session
        user_id: Current user ID

    Returns:
        Updated feed schedule information
    """
    from sqlalchemy import select
    from app.models import Feed
    from uuid import UUID

    try:
        feed_uuid = UUID(feed_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid feed ID format")

    result = await db.execute(
        select(Feed).where(Feed.id == feed_uuid)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    if offset_minutes < 0 or offset_minutes > feed.fetch_interval:
        raise HTTPException(
            status_code=400,
            detail=f"offset_minutes must be between 0 and {feed.fetch_interval}"
        )

    # Update schedule
    feed.schedule_offset_minutes = offset_minutes

    # Recalculate next_fetch_at
    if feed.last_fetched_at:
        base_time = feed.last_fetched_at + timedelta(minutes=feed.fetch_interval)
    else:
        base_time = datetime.now(timezone.utc)

    feed.next_fetch_at = base_time + timedelta(minutes=offset_minutes)

    await db.commit()

    return {
        "feed_id": str(feed.id),
        "feed_name": feed.name,
        "fetch_interval": feed.fetch_interval,
        "schedule_offset_minutes": feed.schedule_offset_minutes,
        "next_fetch_at": feed.next_fetch_at.isoformat(),
        "message": "Feed schedule updated successfully"
    }
