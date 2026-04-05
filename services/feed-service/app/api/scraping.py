"""
Scraping Management API endpoints

Handles scraping configuration and failure management for feeds.
Split from feeds.py for better maintainability.
"""
from datetime import datetime
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import Feed
from app.api.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["scraping"])


@router.get("/{feed_id}/threshold")
async def get_scraping_threshold(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get feed-specific scraping failure threshold.

    Used by Scraping Service to determine when to auto-disable scraping.
    """
    result = await db.execute(
        select(Feed).where(Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    return {
        "scrape_failure_threshold": feed.scrape_failure_threshold,
        "feed_id": str(feed_id)
    }


@router.post("/{feed_id}/scraping/reset")
async def reset_scraping_failures(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Reset scraping failure counter and re-enable scraping.

    This endpoint:
    - Resets failure_count to 0
    - Clears last_failure_at timestamp
    - Clears disabled_reason
    - Optionally re-enables scrape_full_content
    """
    result = await db.execute(
        select(Feed).where(Feed.id == feed_id)
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    # Reset failure tracking
    feed.scrape_failure_count = 0
    feed.scrape_last_failure_at = None
    feed.scrape_disabled_reason = None

    # Re-enable scraping if it was auto-disabled
    if not feed.scrape_full_content:
        feed.scrape_full_content = True
        logger.info(f"Re-enabled scraping for feed {feed_id} after manual reset")

    feed.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(feed)

    # TODO: Publish event to Scraping Service to clear Redis counter

    return {
        "message": "Scraping failures reset successfully",
        "feed_id": str(feed_id),
        "scrape_failure_count": feed.scrape_failure_count,
        "scrape_full_content": feed.scrape_full_content
    }
