"""
Feed Item API endpoints

Handles all operations related to feed items (articles).
Split from feeds.py for better maintainability.

Epic 0.4: Added article update endpoints with NewsML-G2 version tracking.
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, Table, Column, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.db import get_async_db
from app.models import Feed, FeedItem
from app.schemas import (
    FeedItemResponse,
    FeedItemWithFeedResponse,
    FeedItemUpdate,
    # Epic 0.4: Article Update schemas
    ArticleUpdateRequest,
    ArticleVersionResponse,
)
from app.services.analysis_loader import load_analysis_data, load_analysis_data_batch
from app.api.dependencies import get_optional_user_id, get_current_user_id
from app.services.article_update_service import ArticleUpdateService

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

# Define article_analysis table for JSONB filtering
metadata = MetaData(schema="public")
article_analysis_table = Table(
    'article_analysis',
    metadata,
    Column('article_id', PGUUID(as_uuid=True), primary_key=True),
    Column('triage_results', JSONB),
    Column('tier1_results', JSONB),
    Column('tier2_results', JSONB),
    Column('tier3_results', JSONB),
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feeds", tags=["items"])


@router.get("/items", response_model=List[FeedItemWithFeedResponse])
async def list_all_feed_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    feed_ids: Optional[str] = Query(None, description="Comma-separated feed UUIDs"),
    source_type: Optional[str] = Query(None, description="Filter by source type (rss, perplexity_research)"),
    date_from: Optional[datetime] = Query(None, description="Filter items published after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter items published before this date"),
    has_content: Optional[bool] = Query(None, description="Filter by scraped content availability"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive, negative, neutral, mixed)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query("created_at", pattern="^(published_at|created_at|relevance_score)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> List[FeedItemWithFeedResponse]:
    """
    Get all feed items across all feeds (or filtered feeds).

    This endpoint is designed for the Articles section in the frontend,
    providing a unified view of articles from multiple feeds with filtering,
    sorting, and pagination.

    Parameters:
    - **skip**: Number of items to skip (pagination offset)
    - **limit**: Maximum number of items to return (max: 100)
    - **feed_ids**: Comma-separated list of feed UUIDs to filter by
    - **source_type**: Filter by source type (rss, perplexity_research)
    - **date_from**: Only return items published after this date (ISO 8601)
    - **date_to**: Only return items published before this date (ISO 8601)
    - **has_content**: Filter by scraped content availability (true/false)
    - **sentiment**: Filter by sentiment (positive, negative, neutral, mixed)
    - **category**: Filter by category
    - **sort_by**: Sort field (created_at, published_at, or relevance_score; default: created_at)
    - **order**: Sort order (asc or desc)
    """
    # Build query with join to get feed name
    if sentiment or category:
        query = (
            select(FeedItem, Feed.name.label("feed_name"))
            .outerjoin(Feed, FeedItem.feed_id == Feed.id)
            .outerjoin(
                article_analysis_table,
                FeedItem.id == article_analysis_table.c.article_id
            )
        )
    else:
        query = (
            select(FeedItem, Feed.name.label("feed_name"))
            .outerjoin(Feed, FeedItem.feed_id == Feed.id)
        )

    # Apply filters
    filters = []

    if feed_ids:
        try:
            feed_id_list = [UUID(fid.strip()) for fid in feed_ids.split(",")]
            filters.append(FeedItem.feed_id.in_(feed_id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feed_id format")

    if source_type:
        filters.append(FeedItem.source_type == source_type)

    if date_from:
        filters.append(FeedItem.published_at >= date_from)

    if date_to:
        filters.append(FeedItem.published_at <= date_to)

    if has_content is not None:
        if has_content:
            filters.append(FeedItem.content.isnot(None))
            filters.append(FeedItem.content != "")
        else:
            filters.append(or_(FeedItem.content.is_(None), FeedItem.content == ""))

    if sentiment:
        sentiment_upper = sentiment.upper()
        filters.append(
            and_(
                article_analysis_table.c.tier2_results['SENTIMENT_ANALYST'].isnot(None),
                article_analysis_table.c.tier2_results['SENTIMENT_ANALYST']['overall_sentiment'].astext == sentiment_upper
            )
        )

    if category:
        category_normalized = category.upper().replace(" ", "_")
        filters.append(
            article_analysis_table.c.triage_results['category'].astext == category_normalized
        )

    if filters:
        query = query.where(and_(*filters))

    # Apply sorting
    if sort_by == "relevance_score":
        # Sort by relevance_score with NULL values handled appropriately
        if order == "desc":
            # DESC: NULL values last (articles without scores at the end)
            query = query.order_by(FeedItem.relevance_score.desc().nullslast())
        else:
            # ASC: NULL values first
            query = query.order_by(FeedItem.relevance_score.asc().nullsfirst())
    elif sort_by == "published_at":
        sort_field = FeedItem.published_at
        if order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
    else:
        # Default: created_at
        sort_field = FeedItem.created_at
        if order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Batch load analysis data
    item_ids = [item.id for item, _ in rows]
    analysis_batch = await load_analysis_data_batch(db, item_ids)

    # Batch load research articles
    research_query = (
        select(FeedItem)
        .where(FeedItem.parent_article_id.in_(item_ids))
        .order_by(FeedItem.created_at.desc())
    )
    research_result = await db.execute(research_query)
    research_items = research_result.scalars().all()

    research_by_parent: dict = {}
    for research in research_items:
        parent_id = research.parent_article_id
        if parent_id not in research_by_parent:
            research_by_parent[parent_id] = []
        research_by_parent[parent_id].append(research)

    # Build response
    response_items = []
    for item, feed_name in rows:
        analysis_data = analysis_batch.get(item.id, {})
        pipeline_exec = analysis_data.get("pipeline_execution")
        v3_analysis = analysis_data.get("v3_analysis")

        item_research = research_by_parent.get(item.id, [])
        research_responses = None
        if item_research:
            research_responses = [
                FeedItemResponse(
                    id=r.id,
                    feed_id=r.feed_id,
                    title=r.title,
                    link=r.link,
                    description=r.description,
                    content=r.content,
                    author=r.author,
                    published_at=r.published_at,
                    guid=r.guid,
                    content_hash=r.content_hash or "",
                    scraped_at=r.scraped_at,
                    scrape_status=r.scrape_status,
                    scrape_word_count=r.scrape_word_count,
                    created_at=r.created_at,
                    source_type=r.source_type,
                    source_metadata=r.source_metadata,
                    parent_article_id=r.parent_article_id,
                )
                for r in item_research
            ]

        response_items.append(
            FeedItemWithFeedResponse(
                id=item.id,
                feed_id=item.feed_id,
                title=item.title,
                link=item.link,
                description=item.description,
                content=item.content,
                author=item.author,
                published_at=item.published_at,
                guid=item.guid,
                content_hash=item.content_hash,
                scraped_at=item.scraped_at,
                scrape_status=item.scrape_status,
                scrape_word_count=item.scrape_word_count,
                created_at=item.created_at,
                source_type=item.source_type or "rss",
                source_metadata=item.source_metadata,
                parent_article_id=item.parent_article_id,
                research_articles=research_responses,
                pipeline_execution=pipeline_exec,
                v3_analysis=v3_analysis,
                feed_name=feed_name or item.source_type or "Unknown",
            )
        )

        if len(response_items) >= limit:
            break

    return response_items


@router.get("/{feed_id}/items", response_model=List[FeedItemResponse])
@cached(ttl=180, key_prefix="feed:items")
async def get_feed_items(
    feed_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> List[FeedItemResponse]:
    """
    Get items for a specific feed.

    - **skip**: Number of items to skip
    - **limit**: Maximum number of items to return
    - **since**: Only return items published after this date
    """
    feed_exists = await db.execute(select(Feed.id).where(Feed.id == feed_id))
    if not feed_exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    query = select(FeedItem).where(FeedItem.feed_id == feed_id)

    if since:
        query = query.where(FeedItem.published_at >= since)

    query = query.order_by(FeedItem.published_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    response_items = []
    for item in items:
        analysis_data = await load_analysis_data(db, item.id)

        response_items.append(
            FeedItemResponse(
                id=item.id,
                feed_id=item.feed_id,
                title=item.title,
                link=item.link,
                description=item.description,
                content=item.content,
                author=item.author,
                published_at=item.published_at,
                guid=item.guid,
                content_hash=item.content_hash,
                scraped_at=item.scraped_at,
                scrape_status=item.scrape_status,
                scrape_word_count=item.scrape_word_count,
                created_at=item.created_at,
                pipeline_execution=analysis_data.get("pipeline_execution"),
                v3_analysis=analysis_data.get("v3_analysis"),
            )
        )

    return response_items


@router.get("/items/{item_id}", response_model=FeedItemResponse)
async def get_feed_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> FeedItemResponse:
    """
    Get a specific feed item by ID.

    - **item_id**: UUID of the feed item
    """
    result = await db.execute(
        select(FeedItem).where(FeedItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail=f"Feed item {item_id} not found")

    analysis_data = await load_analysis_data(db, item.id)

    return FeedItemResponse(
        id=item.id,
        feed_id=item.feed_id,
        title=item.title,
        link=item.link,
        description=item.description,
        content=item.content,
        author=item.author,
        published_at=item.published_at,
        guid=item.guid,
        content_hash=item.content_hash,
        scraped_at=item.scraped_at,
        scrape_status=item.scrape_status,
        scrape_word_count=item.scrape_word_count,
        created_at=item.created_at,
        source_type=item.source_type,
        source_metadata=item.source_metadata,
        parent_article_id=item.parent_article_id,
        pipeline_execution=analysis_data.get("pipeline_execution"),
        v3_analysis=analysis_data.get("v3_analysis"),
    )


@router.patch("/{feed_id}/items/{item_id}", response_model=FeedItemResponse)
async def update_feed_item(
    feed_id: UUID,
    item_id: UUID,
    item_update: FeedItemUpdate,
    db: AsyncSession = Depends(get_async_db),
) -> FeedItemResponse:
    """
    Update a feed item (used by scraping service to store scraped content).

    Note: This endpoint does NOT require authentication for service-to-service calls.
    """
    feed_exists = await db.execute(select(Feed.id).where(Feed.id == feed_id))
    if not feed_exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Feed {feed_id} not found")

    result = await db.execute(
        select(FeedItem).where(
            and_(FeedItem.id == item_id, FeedItem.feed_id == feed_id)
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail=f"Feed item {item_id} not found")

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    if "content" in update_data and item.scraped_at is None:
        item.scraped_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)

    return FeedItemResponse(
        id=item.id,
        feed_id=item.feed_id,
        title=item.title,
        link=item.link,
        description=item.description,
        content=item.content,
        author=item.author,
        published_at=item.published_at,
        guid=item.guid,
        content_hash=item.content_hash,
        scraped_at=item.scraped_at,
        scrape_status=item.scrape_status,
        scrape_word_count=item.scrape_word_count,
        created_at=item.created_at,
    )


# ========== Epic 0.4: Article Update Endpoints ==========


@router.put("/items/{item_id}", response_model=FeedItemResponse)
async def update_item(
    item_id: UUID,
    update_request: ArticleUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: str = Depends(get_current_user_id),
):
    """
    Update an article with NewsML-G2 compliant version tracking.

    Epic 0.4: Supports three types of changes:

    - **update**: Standard content update (increments version)
    - **correction**: Content correction with reason (increments version)
    - **withdrawal**: Marks article as canceled (sets pub_status='canceled')

    Version history is preserved - each update creates a snapshot of the
    previous version in the article_versions table.

    Returns the updated article with new version number and timestamp.
    """
    service = ArticleUpdateService(db)

    try:
        updated = await service.update_article(
            article_id=item_id,
            title=update_request.title,
            content=update_request.content,
            description=update_request.description,
            change_type=update_request.change_type,
            change_reason=update_request.change_reason,
        )
        await db.commit()
        await db.refresh(updated)

        # Publish article.updated event
        try:
            from app.services.event_publisher import get_event_publisher
            publisher = await get_event_publisher()
            await publisher.publish_event(
                "article.updated",
                {
                    "item_id": str(updated.id),
                    "version": updated.version,
                    "pub_status": updated.pub_status,
                    "change_type": update_request.change_type,
                    "simhash_fingerprint": updated.simhash_fingerprint,
                }
            )
        except Exception as e:
            # Log but don't fail the request if event publishing fails
            logger.warning(f"Failed to publish article.updated event: {e}")

        # Load analysis data for response
        analysis_data = await load_analysis_data(db, updated.id)

        return FeedItemResponse(
            id=updated.id,
            feed_id=updated.feed_id,
            title=updated.title,
            link=updated.link,
            description=updated.description,
            content=updated.content,
            author=updated.author,
            published_at=updated.published_at,
            guid=updated.guid,
            content_hash=updated.content_hash or "",
            scraped_at=updated.scraped_at,
            scrape_status=updated.scrape_status,
            scrape_word_count=updated.scrape_word_count,
            created_at=updated.created_at,
            source_type=updated.source_type,
            source_metadata=updated.source_metadata,
            parent_article_id=updated.parent_article_id,
            pipeline_execution=analysis_data.get("pipeline_execution"),
            v3_analysis=analysis_data.get("v3_analysis"),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/items/{item_id}/versions", response_model=List[ArticleVersionResponse])
async def get_item_versions(
    item_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: str = Depends(get_current_user_id),
):
    """
    Get version history for an article.

    Epic 0.4: Returns list of version snapshots for the article,
    ordered by version number (newest first).

    Each version record includes:
    - **version**: Version number at time of snapshot
    - **pub_status**: Publication status at that version
    - **title**: Title at that version
    - **content_hash**: Hash of content at that version
    - **change_type**: Type of change that created the next version
    - **change_reason**: Reason for the change (if provided)
    - **created_at**: When the version snapshot was created
    """
    # First check if article exists
    result = await db.execute(
        select(FeedItem).where(FeedItem.id == item_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail=f"Article {item_id} not found")

    service = ArticleUpdateService(db)
    versions = await service.get_version_history(item_id)

    return [ArticleVersionResponse.model_validate(v) for v in versions]
