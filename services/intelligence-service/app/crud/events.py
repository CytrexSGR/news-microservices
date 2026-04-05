"""
CRUD operations for Intelligence Events
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from app.models.event import IntelligenceEvent
from app.models.cluster import IntelligenceCluster


async def create_event(
    db: AsyncSession,
    title: str,
    source: str,
    published_at: datetime,
    description: Optional[str] = None,
    source_url: Optional[str] = None,
    **kwargs
) -> IntelligenceEvent:
    """Create a new intelligence event"""
    event = IntelligenceEvent(
        title=title,
        description=description,
        source=source,
        source_url=source_url,
        published_at=published_at,
        **kwargs
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> Optional[IntelligenceEvent]:
    """Get event by ID"""
    result = await db.execute(
        select(IntelligenceEvent)
        .options(selectinload(IntelligenceEvent.cluster))
        .where(IntelligenceEvent.id == event_id)
    )
    return result.scalar_one_or_none()


async def get_events(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    cluster_id: Optional[uuid.UUID] = None,
    source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[IntelligenceEvent]:
    """Get events with optional filters"""
    query = select(IntelligenceEvent).options(selectinload(IntelligenceEvent.cluster))

    filters = []
    if cluster_id:
        filters.append(IntelligenceEvent.cluster_id == cluster_id)
    if source:
        filters.append(IntelligenceEvent.source == source)
    if start_date:
        filters.append(IntelligenceEvent.published_at >= start_date)
    if end_date:
        filters.append(IntelligenceEvent.published_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(desc(IntelligenceEvent.published_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def update_event(
    db: AsyncSession,
    event_id: uuid.UUID,
    **kwargs
) -> Optional[IntelligenceEvent]:
    """Update an event"""
    event = await get_event(db, event_id)
    if not event:
        return None

    for key, value in kwargs.items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event_id: uuid.UUID) -> bool:
    """Delete an event"""
    event = await get_event(db, event_id)
    if not event:
        return False

    await db.delete(event)
    await db.commit()
    return True


async def assign_to_cluster(
    db: AsyncSession,
    event_id: uuid.UUID,
    cluster_id: uuid.UUID
) -> Optional[IntelligenceEvent]:
    """Assign event to a cluster"""
    return await update_event(db, event_id, cluster_id=cluster_id)


async def find_duplicate_events(
    db: AsyncSession,
    title: str,
    published_at: datetime,
    time_window_hours: int = 24
) -> List[IntelligenceEvent]:
    """
    Find potential duplicate events based on title similarity and temporal proximity
    """
    time_threshold = published_at - timedelta(hours=time_window_hours)

    result = await db.execute(
        select(IntelligenceEvent)
        .where(
            and_(
                IntelligenceEvent.published_at >= time_threshold,
                IntelligenceEvent.published_at <= published_at,
                # PostgreSQL similarity check (requires pg_trgm extension)
                # For now, we do simple LIKE match - can be improved
                or_(
                    IntelligenceEvent.title.ilike(f"%{title[:30]}%"),
                    IntelligenceEvent.title.ilike(f"%{title[-30:]}%")
                )
            )
        )
    )
    return result.scalars().all()
