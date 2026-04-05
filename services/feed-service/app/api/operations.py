"""
Feed Operations API endpoints

Handles feed fetch operations, bulk fetch, and error reset functionality.
Split from feeds.py for better maintainability.
"""
from datetime import datetime, timedelta
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import Feed, FeedStatus
from app.schemas import BulkFetchRequest, BulkFetchResponse
from app.services.feed_fetcher import FeedFetcher
from app.services.event_publisher import get_event_publisher
from app.api.dependencies import get_current_user_id

# Import caching utilities
try:
    from shared.cache import cache_invalidate
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False

    async def cache_invalidate(pattern: str):
        pass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["operations"])


async def fetch_feed_task(feed_id: UUID) -> None:
    """
    Background task to fetch a feed.
    """
    fetcher = FeedFetcher()
    await fetcher.fetch_feed(feed_id)


@router.post("/{feed_id}/fetch", response_model=dict)
async def trigger_feed_fetch(
    feed_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Manually trigger a fetch for a specific feed.

    The fetch will be performed asynchronously in the background.

    Smart Auto-Reset: If feed is in ERROR status, automatically resets it
    to ACTIVE before triggering fetch. This allows users to retry failed feeds
    without needing to manually reset the error first.
    """
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    if not feed.is_active:
        raise HTTPException(status_code=400, detail="Feed is not active")

    # SMART AUTO-RESET: If feed is in ERROR status, reset to ACTIVE
    auto_reset = False
    if feed.status == FeedStatus.ERROR.value:
        feed.status = FeedStatus.ACTIVE.value
        feed.consecutive_failures = 0
        feed.last_error_message = None
        feed.last_error_at = None
        # Give small health boost on retry
        feed.health_score = min(100, feed.health_score + 10)
        await db.commit()
        auto_reset = True

    # Schedule fetch in background
    background_tasks.add_task(fetch_feed_task, feed_id)

    message = f"Fetch triggered for feed {feed_id}"
    if auto_reset:
        message += " (error status auto-reset to ACTIVE)"

    return {
        "success": True,
        "message": message,
        "feed_id": feed_id,
        "auto_reset": auto_reset,
    }


@router.post("/{feed_id}/reset-error", response_model=dict)
async def reset_feed_error(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Reset a feed's ERROR status back to ACTIVE.

    This endpoint allows users to manually clear error states and retry
    failed feeds without triggering an immediate fetch.

    Use cases:
    - Feed had temporary network issue (HTTP 522, timeouts)
    - Source server was down but is now back online
    - Want to clear error before changing feed URL
    - Manual recovery after investigating the error

    After reset, the feed will be included in scheduled fetches again.
    """
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Check if feed is actually in ERROR status
    if feed.status != FeedStatus.ERROR.value:
        return {
            "success": False,
            "message": f"Feed is not in ERROR status (current: {feed.status})",
            "feed_id": feed_id,
            "current_status": feed.status,
        }

    # Store old error info for response
    old_error = feed.last_error_message
    old_error_time = feed.last_error_at

    # Reset to ACTIVE state
    feed.status = FeedStatus.ACTIVE.value
    feed.consecutive_failures = 0
    feed.last_error_message = None
    feed.last_error_at = None

    # Give health score boost (but not full recovery)
    # This rewards retry attempts while keeping some "memory" of issues
    feed.health_score = min(100, feed.health_score + 20)

    await db.commit()

    # Invalidate cache
    await cache_invalidate("feeds:list:*")
    await cache_invalidate(f"feed:{feed_id}:*")

    # Publish event for monitoring
    publisher = await get_event_publisher()
    await publisher.publish_event(
        "feed.error_reset",
        {
            "feed_id": str(feed_id),
            "feed_name": feed.name,
            "previous_error": old_error,
            "reset_by_user": user_id,
        }
    )

    return {
        "success": True,
        "message": f"Feed error status reset to ACTIVE",
        "feed_id": feed_id,
        "previous_status": "ERROR",
        "new_status": "ACTIVE",
        "previous_error": old_error,
        "error_occurred_at": old_error_time.isoformat() if old_error_time else None,
        "health_score": feed.health_score,
    }


@router.post("/bulk-fetch", response_model=BulkFetchResponse)
async def bulk_fetch_feeds(
    request: BulkFetchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
) -> BulkFetchResponse:
    """
    Trigger fetch for multiple feeds or all active feeds.

    If no feed_ids are provided, all active feeds will be fetched.
    Fetches are performed asynchronously in the background.
    """
    if request.feed_ids:
        # Fetch specific feeds
        result = await db.execute(
            select(Feed).where(
                and_(
                    Feed.id.in_(request.feed_ids),
                    or_(Feed.is_active == True, request.force == True)
                )
            )
        )
        feeds = result.scalars().all()
    else:
        # Fetch all active feeds
        query = select(Feed).where(Feed.is_active == True)

        # If not forcing, only fetch feeds that haven't been fetched recently
        if not request.force:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            query = query.where(
                or_(
                    Feed.last_fetched_at == None,
                    Feed.last_fetched_at < one_hour_ago
                )
            )

        result = await db.execute(query)
        feeds = result.scalars().all()

    # Schedule all fetches
    for feed in feeds:
        background_tasks.add_task(fetch_feed_task, feed.id)

    return BulkFetchResponse(
        total_feeds=len(feeds),
        successful_fetches=0,  # Will be updated by background tasks
        failed_fetches=0,
        total_new_items=0,
        details=[
            {"feed_id": feed.id, "feed_name": feed.name, "status": "scheduled"}
            for feed in feeds
        ]
    )
