"""
Crawl Sessions API endpoints.

Provides CRUD operations for web crawl session tracking.
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import CrawlSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crawl-sessions", tags=["crawl-sessions"])


@router.get("/{session_id}")
async def get_crawl_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific crawl session by ID."""
    result = await db.execute(
        select(CrawlSession).where(CrawlSession.id == session_id)
    )
    session_obj = result.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Crawl session not found")

    return _session_to_dict(session_obj)


@router.get("")
async def list_crawl_sessions(
    status: Optional[str] = Query(None, description="Filter by status (active, completed, failed)"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    """List crawl sessions with optional status filter."""
    query = select(CrawlSession)

    if status:
        query = query.where(CrawlSession.status == status)

    query = query.order_by(desc(CrawlSession.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [_session_to_dict(s) for s in sessions]


def _session_to_dict(session: CrawlSession) -> dict:
    """Convert CrawlSession ORM object to dict."""
    return {
        "id": str(session.id),
        "feed_id": str(session.feed_id) if session.feed_id else None,
        "seed_url": session.seed_url,
        "topic": session.topic,
        "status": session.status,
        "pages_scraped": session.pages_scraped,
        "visited_urls": session.visited_urls,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "metadata": session.metadata_,
    }
