"""
Feed API endpoints - Core CRUD operations

This module contains the core feed management endpoints:
- List feeds
- Create feed
- Get feed
- Update feed
- Delete feed
- Feed stats

Other endpoints have been split into separate modules for maintainability:
- items.py: Feed item endpoints
- operations.py: Fetch operations (trigger, bulk-fetch, reset-error)
- health.py: Health & quality endpoints
- scraping.py: Scraping management
- research.py: Research article & analysis trigger endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Header
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import Feed, FeedItem, FeedHealth, FeedStatus
from app.schemas import (
    FeedCreate,
    FeedUpdate,
    FeedResponse,
)
from app.services.feed_fetcher import FeedFetcher
from app.services.event_publisher import get_event_publisher
from app.services.admiralty_code import AdmiraltyCodeService
from app.api.dependencies import get_current_user_id, get_optional_user_id

# Import caching utilities
try:
    from shared.cache import cached, cache_invalidate
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    import logging
    logging.warning("shared.cache not available - caching disabled")

    def cached(ttl: int = 300, key_prefix: str = None):
        def decorator(func):
            return func
        return decorator

    async def cache_invalidate(pattern: str):
        pass


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["feeds"])


# =============================================================================
# Helper Functions
# =============================================================================

def _build_assessment_data(feed: Feed) -> dict:
    """Helper to build assessment data from feed model."""
    if feed.assessment_status:
        return {
            "assessment_status": feed.assessment_status,
            "assessment_date": feed.assessment_date,
            "credibility_tier": feed.credibility_tier,
            "reputation_score": feed.reputation_score,
            "founded_year": feed.founded_year,
            "organization_type": feed.organization_type,
            "political_bias": feed.political_bias,
            "editorial_standards": feed.editorial_standards,
            "trust_ratings": feed.trust_ratings,
            "recommendation": feed.recommendation,
            "assessment_summary": feed.assessment_summary,
            "quality_score": feed.quality_score,
        }
    return None


async def _build_admiralty_code(
    feed: Feed,
    admiralty_service: AdmiraltyCodeService
) -> Optional[dict]:
    """
    Helper to build Admiralty Code data for a feed.

    Args:
        feed: Feed model instance
        admiralty_service: AdmiraltyCodeService instance

    Returns:
        Dict with code, label, and color, or None if quality_score is None
    """
    if feed.quality_score is not None:
        return await admiralty_service.get_admiralty_code(feed.quality_score)
    return None


async def fetch_feed_task(feed_id: UUID) -> None:
    """
    Background task to fetch a feed.
    """
    fetcher = FeedFetcher()
    await fetcher.fetch_feed(feed_id)


# =============================================================================
# Feed CRUD Endpoints
# =============================================================================

@router.get("", response_model=List[FeedResponse])
@cached(ttl=300, key_prefix="feeds:list")
async def list_feeds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    status: Optional[FeedStatus] = None,
    category: Optional[str] = None,
    health_score_min: Optional[int] = Query(None, ge=0, le=100),
    health_score_max: Optional[int] = Query(None, ge=0, le=100),
    feed_type: Optional[str] = Query(None, description="Filter by feed type (rss, web)"),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> List[FeedResponse]:
    """
    List all feeds with pagination and filtering.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    - **is_active**: Filter by active status
    - **status**: Filter by feed status (ACTIVE, PAUSED, ERROR, INACTIVE)
    - **category**: Filter by category name
    - **health_score_min**: Minimum health score (0-100)
    - **health_score_max**: Maximum health score (0-100)
    """
    query = select(Feed)

    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(Feed.is_active == is_active)
    if status is not None:
        filters.append(Feed.status == status.value)
    if health_score_min is not None:
        filters.append(Feed.health_score >= health_score_min)
    if health_score_max is not None:
        filters.append(Feed.health_score <= health_score_max)
    if category:
        filters.append(Feed.category == category)
    if feed_type:
        filters.append(Feed.feed_type == feed_type)

    if filters:
        query = query.where(and_(*filters))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    feeds = result.scalars().all()

    # Create Admiralty Code service
    admiralty_service = AdmiraltyCodeService(db)

    # Convert to response schema
    feed_responses = []
    for feed in feeds:
        admiralty_code = await _build_admiralty_code(feed, admiralty_service)

        feed_dict = {
            "id": feed.id,
            "name": feed.name,
            "url": str(feed.url),
            "description": feed.description,
            "feed_type": feed.feed_type,
            "fetch_interval": feed.fetch_interval,
            "is_active": feed.is_active,
            "status": feed.status,
            "last_fetched_at": feed.last_fetched_at,
            "health_score": feed.health_score,
            "consecutive_failures": feed.consecutive_failures,
            "quality_score": feed.quality_score,
            "admiralty_code": admiralty_code,
            "total_items": feed.total_items,
            "items_last_24h": feed.items_last_24h,
            "scrape_full_content": feed.scrape_full_content,
            "scrape_method": feed.scrape_method,
            "enable_categorization": feed.enable_categorization,
            "enable_finance_sentiment": feed.enable_finance_sentiment,
            "enable_geopolitical_sentiment": feed.enable_geopolitical_sentiment,
            "enable_osint_analysis": feed.enable_osint_analysis,
            "enable_summary": feed.enable_summary,
            "enable_entity_extraction": feed.enable_entity_extraction,
            "enable_topic_classification": feed.enable_topic_classification,
            "enable_analysis_v2": feed.enable_analysis_v2,
            "created_at": feed.created_at,
            "updated_at": feed.updated_at,
            "category": feed.category,
            "assessment": _build_assessment_data(feed),
        }
        feed_responses.append(FeedResponse(**feed_dict))

    return feed_responses


@router.post("", response_model=FeedResponse, status_code=201)
async def create_feed(
    feed_data: FeedCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> FeedResponse:
    """
    Create a new feed.

    The feed will be automatically fetched after creation.
    """
    # Check if feed URL already exists
    existing = await db.execute(select(Feed).where(Feed.url == str(feed_data.url)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feed with this URL already exists")

    logger.info(f"Creating feed with threshold={feed_data.scrape_failure_threshold}")

    # Create new feed
    feed = Feed(
        url=str(feed_data.url),
        feed_type=feed_data.feed_type,
        name=feed_data.name,
        description=feed_data.description,
        category=feed_data.category,
        fetch_interval=feed_data.fetch_interval,
        scrape_full_content=feed_data.scrape_full_content,
        scrape_method=feed_data.scrape_method,
        scrape_failure_threshold=feed_data.scrape_failure_threshold,
        enable_categorization=feed_data.enable_categorization,
        enable_finance_sentiment=feed_data.enable_finance_sentiment,
        enable_geopolitical_sentiment=feed_data.enable_geopolitical_sentiment,
        enable_osint_analysis=feed_data.enable_osint_analysis,
        enable_summary=feed_data.enable_summary,
        enable_entity_extraction=feed_data.enable_entity_extraction,
        enable_topic_classification=feed_data.enable_topic_classification,
        is_active=True,
        status=FeedStatus.ACTIVE.value,
        # Source Assessment fields (if provided)
        credibility_tier=feed_data.credibility_tier,
        reputation_score=feed_data.reputation_score,
        founded_year=feed_data.founded_year,
        organization_type=feed_data.organization_type,
        political_bias=feed_data.political_bias,
        editorial_standards=feed_data.editorial_standards,
        trust_ratings=feed_data.trust_ratings,
        recommendation=feed_data.recommendation,
        assessment_summary=feed_data.assessment_summary,
        assessment_status="completed" if feed_data.assessment_summary else None,
        assessment_date=datetime.utcnow() if feed_data.assessment_summary else None,
    )

    db.add(feed)
    await db.flush()

    # Create initial health record
    health = FeedHealth(
        feed_id=feed.id,
        health_score=100,
        is_healthy=True,
        success_rate=1.0,
        uptime_24h=1.0,
        uptime_7d=1.0,
        uptime_30d=1.0,
    )
    db.add(health)

    await db.commit()
    await db.refresh(feed)

    # Publish event (non-blocking, ignore failures)
    try:
        event_publisher = await get_event_publisher()
        await event_publisher.publish_event(
            "feed.created",
            {"feed_id": feed.id, "url": feed.url, "name": feed.name}
        )
    except Exception as e:
        logger.warning(f"Failed to publish feed.created event: {e}")

    # Schedule initial fetch in background
    background_tasks.add_task(fetch_feed_task, feed.id)

    # Invalidate feed list cache
    await cache_invalidate("feeds:list:*")
    await cache_invalidate("items:all:*")

    # Load categories for response
    await db.refresh(feed, attribute_names=["categories"])

    return FeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        description=feed.description,
        feed_type=feed.feed_type,
        fetch_interval=feed.fetch_interval,
        is_active=feed.is_active,
        status=FeedStatus(feed.status),
        last_fetched_at=feed.last_fetched_at,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        scrape_full_content=feed.scrape_full_content,
        scrape_method=feed.scrape_method,
        scrape_failure_count=feed.scrape_failure_count,
        scrape_failure_threshold=feed.scrape_failure_threshold,
        scrape_last_failure_at=feed.scrape_last_failure_at,
        scrape_disabled_reason=feed.scrape_disabled_reason,
        enable_categorization=feed.enable_categorization,
        enable_finance_sentiment=feed.enable_finance_sentiment,
        enable_geopolitical_sentiment=feed.enable_geopolitical_sentiment,
        enable_osint_analysis=feed.enable_osint_analysis,
        enable_summary=feed.enable_summary,
        enable_entity_extraction=feed.enable_entity_extraction,
        enable_topic_classification=feed.enable_topic_classification,
        enable_analysis_v2=feed.enable_analysis_v2,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        category=feed.category,
        assessment=_build_assessment_data(feed),
    )


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get feed service statistics.

    Returns:
        Statistics about feeds and articles
    """
    # Count active feeds
    active_feeds_result = await db.execute(
        select(func.count(Feed.id)).where(Feed.is_active == True)
    )
    active_feeds = active_feeds_result.scalar() or 0

    # Count total articles
    total_articles_result = await db.execute(
        select(func.count(FeedItem.id))
    )
    total_articles = total_articles_result.scalar() or 0

    # Count articles today (optimized with date range)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = today_start + timedelta(days=1)

    articles_today_result = await db.execute(
        select(func.count(FeedItem.id)).where(
            and_(
                FeedItem.created_at >= today_start,
                FeedItem.created_at < today_end
            )
        )
    )
    articles_today = articles_today_result.scalar() or 0

    # Articles per day (last 7 days)
    articles_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        count_result = await db.execute(
            select(func.count(FeedItem.id)).where(
                and_(
                    FeedItem.created_at >= day_start,
                    FeedItem.created_at < day_end
                )
            )
        )
        count = count_result.scalar() or 0
        articles_by_day.append({
            "date": day.isoformat(),
            "count": count
        })

    # Top sources (top 5 feeds by article count)
    top_sources_result = await db.execute(
        select(
            Feed.name,
            func.count(FeedItem.id).label('count')
        )
        .join(FeedItem, Feed.id == FeedItem.feed_id)
        .group_by(Feed.id, Feed.name)
        .order_by(desc('count'))
        .limit(5)
    )
    top_sources = [
        {"source": row[0], "count": row[1]}
        for row in top_sources_result.all()
    ]

    return {
        "active_feeds": active_feeds,
        "total_articles": total_articles,
        "articles_today": articles_today,
        "articles_by_day": articles_by_day,
        "top_sources": top_sources
    }


@router.get("/{feed_id}", response_model=FeedResponse)
async def get_feed(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> FeedResponse:
    """
    Get a single feed by ID (UUID).
    """
    result = await db.execute(
        select(Feed).where(Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Calculate Admiralty Code
    admiralty_service = AdmiraltyCodeService(db)
    admiralty_code = await _build_admiralty_code(feed, admiralty_service)

    return FeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        description=feed.description,
        feed_type=feed.feed_type,
        fetch_interval=feed.fetch_interval,
        is_active=feed.is_active,
        status=FeedStatus(feed.status),
        last_fetched_at=feed.last_fetched_at,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        quality_score=feed.quality_score,
        admiralty_code=admiralty_code,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        scrape_full_content=feed.scrape_full_content,
        scrape_method=feed.scrape_method,
        scrape_failure_count=feed.scrape_failure_count,
        scrape_failure_threshold=feed.scrape_failure_threshold,
        scrape_last_failure_at=feed.scrape_last_failure_at,
        scrape_disabled_reason=feed.scrape_disabled_reason,
        enable_categorization=feed.enable_categorization,
        enable_finance_sentiment=feed.enable_finance_sentiment,
        enable_geopolitical_sentiment=feed.enable_geopolitical_sentiment,
        enable_osint_analysis=feed.enable_osint_analysis,
        enable_summary=feed.enable_summary,
        enable_entity_extraction=feed.enable_entity_extraction,
        enable_topic_classification=feed.enable_topic_classification,
        enable_analysis_v2=feed.enable_analysis_v2,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        category=feed.category,
        assessment=_build_assessment_data(feed),
    )


@router.put("/{feed_id}", response_model=FeedResponse)
async def update_feed(
    feed_id: UUID,
    feed_update: FeedUpdate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> FeedResponse:
    """
    Update a feed.

    Note: The feed URL cannot be changed after creation.
    """
    result = await db.execute(
        select(Feed).where(Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Update fields if provided
    update_data = feed_update.model_dump(exclude_unset=True)

    # Handle manual scraping disable: set reason to "manual" when user explicitly disables scraping
    if "scrape_full_content" in update_data and update_data["scrape_full_content"] is False:
        if "scrape_disabled_reason" not in update_data and feed.scrape_disabled_reason != "auto_threshold":
            update_data["scrape_disabled_reason"] = "manual"
    # Re-enable scraping: clear disabled reason
    elif "scrape_full_content" in update_data and update_data["scrape_full_content"] is True:
        if "scrape_disabled_reason" not in update_data:
            update_data["scrape_disabled_reason"] = None

    for field, value in update_data.items():
        setattr(feed, field, value)

    feed.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(feed)

    # Publish event
    event_publisher = await get_event_publisher()
    await event_publisher.publish_event(
        "feed.updated",
        {"feed_id": feed.id, "updated_fields": list(update_data.keys())}
    )

    # Invalidate caches
    await cache_invalidate("feeds:list:*")
    await cache_invalidate(f"feed:items:{feed_id}:*")
    await cache_invalidate("items:all:*")

    return FeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        description=feed.description,
        feed_type=feed.feed_type,
        fetch_interval=feed.fetch_interval,
        is_active=feed.is_active,
        status=FeedStatus(feed.status),
        last_fetched_at=feed.last_fetched_at,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        scrape_full_content=feed.scrape_full_content,
        scrape_method=feed.scrape_method,
        scrape_failure_count=feed.scrape_failure_count,
        scrape_failure_threshold=feed.scrape_failure_threshold,
        scrape_last_failure_at=feed.scrape_last_failure_at,
        scrape_disabled_reason=feed.scrape_disabled_reason,
        enable_categorization=feed.enable_categorization,
        enable_finance_sentiment=feed.enable_finance_sentiment,
        enable_geopolitical_sentiment=feed.enable_geopolitical_sentiment,
        enable_osint_analysis=feed.enable_osint_analysis,
        enable_summary=feed.enable_summary,
        enable_entity_extraction=feed.enable_entity_extraction,
        enable_topic_classification=feed.enable_topic_classification,
        enable_analysis_v2=feed.enable_analysis_v2,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        category=feed.category,
        assessment=_build_assessment_data(feed),
    )


@router.patch("/{feed_id}", response_model=FeedResponse)
async def patch_feed(
    feed_id: UUID,
    feed_update: FeedUpdate,
    db: AsyncSession = Depends(get_async_db),
    x_service_name: Optional[str] = Header(None, alias="X-Service-Name"),
) -> FeedResponse:
    """
    Partially update a feed (PATCH).

    Used by internal services (scraping-service) for failure tracking.
    Accepts X-Service-Name header for service-to-service authentication.
    """
    result = await db.execute(
        select(Feed).where(Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Update fields if provided
    update_data = feed_update.model_dump(exclude_unset=True)

    # Handle manual scraping disable: set reason to "manual" when user explicitly disables scraping
    if "scrape_full_content" in update_data and update_data["scrape_full_content"] is False:
        if "scrape_disabled_reason" not in update_data and feed.scrape_disabled_reason != "auto_threshold":
            update_data["scrape_disabled_reason"] = "manual"
    # Re-enable scraping: clear disabled reason
    elif "scrape_full_content" in update_data and update_data["scrape_full_content"] is True:
        if "scrape_disabled_reason" not in update_data:
            update_data["scrape_disabled_reason"] = None

    for field, value in update_data.items():
        setattr(feed, field, value)

    feed.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(feed)

    # Log service-to-service updates
    if x_service_name:
        logger.info(f"Feed {feed_id} updated by {x_service_name}: {list(update_data.keys())}")

    # Publish event
    event_publisher = await get_event_publisher()
    await event_publisher.publish_event(
        "feed.updated",
        {"feed_id": feed.id, "updated_fields": list(update_data.keys()), "source": x_service_name or "api"}
    )

    # Invalidate caches
    await cache_invalidate("feeds:list:*")
    await cache_invalidate(f"feed:items:{feed_id}:*")
    await cache_invalidate("items:all:*")

    return FeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        description=feed.description,
        feed_type=feed.feed_type,
        fetch_interval=feed.fetch_interval,
        is_active=feed.is_active,
        status=FeedStatus(feed.status),
        last_fetched_at=feed.last_fetched_at,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        scrape_full_content=feed.scrape_full_content,
        scrape_method=feed.scrape_method,
        scrape_failure_count=feed.scrape_failure_count,
        scrape_failure_threshold=feed.scrape_failure_threshold,
        scrape_last_failure_at=feed.scrape_last_failure_at,
        scrape_disabled_reason=feed.scrape_disabled_reason,
        enable_categorization=feed.enable_categorization,
        enable_finance_sentiment=feed.enable_finance_sentiment,
        enable_geopolitical_sentiment=feed.enable_geopolitical_sentiment,
        enable_osint_analysis=feed.enable_osint_analysis,
        enable_summary=feed.enable_summary,
        enable_entity_extraction=feed.enable_entity_extraction,
        enable_topic_classification=feed.enable_topic_classification,
        enable_analysis_v2=feed.enable_analysis_v2,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        category=feed.category,
        assessment=_build_assessment_data(feed),
    )


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> None:
    """
    Delete a feed and all associated data.
    """
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Delete feed (cascades to related tables)
    await db.delete(feed)
    await db.commit()

    # Publish event
    event_publisher = await get_event_publisher()
    await event_publisher.publish_event(
        "feed.deleted",
        {"feed_id": feed_id, "url": feed.url}
    )

    # Invalidate all caches for this feed
    await cache_invalidate("feeds:list:*")
    await cache_invalidate(f"feed:items:{feed_id}:*")
    await cache_invalidate("items:all:*")
