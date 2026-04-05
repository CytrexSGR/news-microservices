"""
Feed Health & Quality API endpoints

Handles health monitoring and quality scoring for feeds.
Split from feeds.py for better maintainability.
"""
from typing import Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import Feed, FeedItem, FeedHealth
from app.schemas import (
    FeedHealthResponse,
    FeedQualityResponse,
    FeedQualityV2Response,
)
from app.services.feed_quality import FeedQualityScorer
from app.services.feed_quality_v2 import FeedQualityScorerV2

# Import caching utilities
try:
    from shared.cache import cached
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False

    def cached(ttl: int = 300, key_prefix: str = None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["health"])


@router.get("/{feed_id}/health", response_model=FeedHealthResponse)
async def get_feed_health(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> FeedHealthResponse:
    """
    Get health metrics for a specific feed.

    Returns detailed health information including uptime, success rate,
    and performance metrics.
    """
    result = await db.execute(
        select(FeedHealth).where(FeedHealth.feed_id == feed_id)
    )
    health = result.scalar_one_or_none()

    if not health:
        # Check if feed exists
        feed_exists = await db.execute(select(Feed.id).where(Feed.id == feed_id))
        if not feed_exists.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

        # Return default health if no health record exists yet
        return FeedHealthResponse(
            feed_id=feed_id,
            health_score=100,
            consecutive_failures=0,
            is_healthy=True,
            avg_response_time_ms=None,
            success_rate=1.0,
            uptime_24h=1.0,
            uptime_7d=1.0,
            uptime_30d=1.0,
            last_success_at=None,
            last_failure_at=None,
        )

    return FeedHealthResponse(
        feed_id=health.feed_id,
        health_score=health.health_score,
        consecutive_failures=health.consecutive_failures,
        is_healthy=health.is_healthy,
        avg_response_time_ms=health.avg_response_time_ms,
        success_rate=health.success_rate,
        uptime_24h=health.uptime_24h,
        uptime_7d=health.uptime_7d,
        uptime_30d=health.uptime_30d,
        last_success_at=health.last_success_at,
        last_failure_at=health.last_failure_at,
    )


@router.get("/{feed_id}/quality", response_model=FeedQualityResponse)
async def get_feed_quality(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> FeedQualityResponse:
    """
    Get quality score and metrics for a specific feed (legacy/basic version).

    Quality score is calculated based on:
    - Content freshness
    - Publishing consistency
    - Content quality
    - Feed reliability

    **Note:** For comprehensive analysis including article quality from content-analysis-v2,
    use /api/v1/feeds/{feed_id}/quality-v2 instead.
    """
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    quality_scorer = FeedQualityScorer()
    quality_data = await quality_scorer.calculate_quality_score(db, feed_id)

    return FeedQualityResponse(**quality_data)


@router.get("/quality-v2/overview")
@cached(ttl=300, key_prefix="feeds:quality_v2:overview")
async def get_feeds_quality_overview(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get quality overview for all active feeds.

    Returns a list of feeds with key quality metrics:
    - Feed name and ID
    - Quality score and Admiralty code
    - Total articles and last 24h count
    - Confidence level
    - Trend direction

    Optimized for table display with sorting capabilities.
    """
    # Get all active feeds
    result = await db.execute(
        select(Feed)
        .where(Feed.is_active == True)
        .order_by(Feed.name)
    )
    feeds = result.scalars().all()

    if not feeds:
        return []

    overview_data = []
    quality_scorer = FeedQualityScorerV2()

    for feed in feeds:
        try:
            quality_data = await quality_scorer.calculate_comprehensive_quality(
                session=db,
                feed_id=feed.id,
                days=30
            )

            cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

            total_result = await db.execute(
                select(func.count(FeedItem.id))
                .where(FeedItem.feed_id == feed.id)
            )
            total_articles = total_result.scalar() or 0

            recent_result = await db.execute(
                select(func.count(FeedItem.id))
                .where(
                    FeedItem.feed_id == feed.id,
                    FeedItem.created_at >= cutoff_24h
                )
            )
            articles_24h = recent_result.scalar() or 0

            overview_data.append({
                "feed_id": str(feed.id),
                "feed_name": feed.name,
                "quality_score": quality_data.get("quality_score"),
                "admiralty_code": quality_data.get("admiralty_code", {}).get("code"),
                "admiralty_label": quality_data.get("admiralty_code", {}).get("label"),
                "admiralty_color": quality_data.get("admiralty_code", {}).get("color"),
                "confidence": quality_data.get("confidence"),
                "trend": quality_data.get("trend"),
                "trend_direction": quality_data.get("trend_direction"),
                "total_articles": total_articles,
                "articles_24h": articles_24h,
                "articles_analyzed": quality_data.get("data_stats", {}).get("articles_analyzed", 0),
                "coverage_percentage": quality_data.get("data_stats", {}).get("coverage_percentage", 0),
            })

        except Exception as e:
            logger.error(f"Failed to calculate quality overview for feed {feed.id}: {e}")
            overview_data.append({
                "feed_id": str(feed.id),
                "feed_name": feed.name,
                "quality_score": None,
                "admiralty_code": None,
                "admiralty_label": "Error",
                "admiralty_color": "gray",
                "confidence": None,
                "trend": None,
                "trend_direction": None,
                "total_articles": 0,
                "articles_24h": 0,
                "articles_analyzed": 0,
                "coverage_percentage": 0,
            })

    return overview_data


@router.get("/{feed_id}/quality-v2", response_model=FeedQualityV2Response)
@cached(ttl=300, key_prefix="feed:quality_v2")
async def get_feed_quality_v2(
    feed_id: UUID,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_db),
) -> FeedQualityV2Response:
    """
    Get comprehensive quality score and metrics for a specific feed (V2).

    **Enhanced Quality Analysis** combining:
    1. **Article Quality (50%)** - Aggregated from content-analysis-v2
    2. **Source Credibility (20%)** - Research service assessment
    3. **Operational Reliability (20%)** - Feed health metrics
    4. **Freshness & Consistency (10%)** - Publishing patterns

    **Features:**
    - Admiralty Code rating (A-F)
    - Confidence scoring based on data completeness
    - Trend detection (improving/stable/declining)
    - Actionable recommendations

    **Parameters:**
    - `days`: Analysis time window (7-90 days, default: 30)
    """
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    try:
        quality_scorer = FeedQualityScorerV2()
        quality_data = await quality_scorer.calculate_comprehensive_quality(
            session=db,
            feed_id=feed_id,
            days=days
        )

        return FeedQualityV2Response(**quality_data)

    except Exception as e:
        logger.error(f"Failed to calculate quality V2 for feed {feed_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate quality score: {str(e)}"
        )
