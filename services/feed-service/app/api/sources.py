"""
Unified Source Management API Endpoints

This module contains endpoints for managing news sources:
- CRUD operations for Sources (master entity)
- CRUD operations for SourceFeeds (provider-specific feeds)
- Assessment trigger and history
- Bulk operations

Endpoints:
- /api/v1/sources/ - Source management
- /api/v1/source-feeds/ - SourceFeed management
"""
from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_async_db
from app.models import (
    Source,
    SourceFeed,
    SourceAssessmentHistory,
    SourceStatus,
    ScrapeStatus,
    PaywallType,
    ProviderType,
    CredibilityTier,
    AssessmentStatus,
)
from app.schemas import (
    # Source schemas
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
    SourceFilters,
    # SourceFeed schemas
    SourceFeedCreate,
    SourceFeedUpdate,
    SourceFeedResponse,
    SourceFeedWithSourceResponse,
    SourceFeedListResponse,
    SourceFeedFilters,
    # Assessment schemas
    SourceAssessmentTrigger,
    SourceAssessmentTriggerResponse,
    SourceAssessmentHistoryResponse,
    # Bulk operations
    BulkSourceCreate,
    BulkSourceCreateResponse,
    # Helper
    extract_domain,
)
from app.api.dependencies import get_current_user_id, get_optional_user_id

logger = logging.getLogger(__name__)

# =============================================================================
# Routers
# =============================================================================

sources_router = APIRouter(prefix="/api/v1/sources", tags=["sources"])
source_feeds_router = APIRouter(prefix="/api/v1/source-feeds", tags=["source-feeds"])


# =============================================================================
# Source CRUD Endpoints
# =============================================================================

@sources_router.get("", response_model=SourceListResponse)
async def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    status: Optional[SourceStatus] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    language: Optional[str] = None,
    credibility_tier: Optional[CredibilityTier] = None,
    organization_name: Optional[str] = None,
    has_assessment: Optional[bool] = None,
    scrape_status: Optional[ScrapeStatus] = None,
    search: Optional[str] = Query(None, description="Search in domain, name, organization"),
    include_feeds: bool = Query(False, description="Include feed details in response"),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> SourceListResponse:
    """
    List all sources with pagination and filtering.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    - **is_active**: Filter by active status
    - **status**: Filter by source status (active, inactive, blocked)
    - **category**: Filter by category
    - **country**: Filter by country code
    - **language**: Filter by language code
    - **credibility_tier**: Filter by credibility tier
    - **organization_name**: Filter by organization name
    - **has_assessment**: Filter by assessment status
    - **scrape_status**: Filter by scrape status
    - **search**: Search in domain, canonical_name, organization_name
    - **include_feeds**: Include feed details in response
    """
    query = select(Source)

    if include_feeds:
        query = query.options(selectinload(Source.feeds))

    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(Source.is_active == is_active)
    if status is not None:
        filters.append(Source.status == status.value)
    if category is not None:
        filters.append(Source.category == category)
    if country is not None:
        filters.append(Source.country == country)
    if language is not None:
        filters.append(Source.language == language)
    if credibility_tier is not None:
        filters.append(Source.credibility_tier == credibility_tier.value)
    if organization_name is not None:
        filters.append(Source.organization_name.ilike(f"%{organization_name}%"))
    if has_assessment is not None:
        if has_assessment:
            filters.append(Source.assessment_status == AssessmentStatus.COMPLETED.value)
        else:
            filters.append(or_(
                Source.assessment_status.is_(None),
                Source.assessment_status != AssessmentStatus.COMPLETED.value
            ))
    if scrape_status is not None:
        filters.append(Source.scrape_status == scrape_status.value)
    if search:
        search_filter = or_(
            Source.domain.ilike(f"%{search}%"),
            Source.canonical_name.ilike(f"%{search}%"),
            Source.organization_name.ilike(f"%{search}%"),
        )
        filters.append(search_filter)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Source)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Source.canonical_name).offset(skip).limit(limit)

    result = await db.execute(query)
    sources = result.scalars().all()

    # Build response
    items = [
        SourceResponse.from_orm_with_summary(source, include_feeds=include_feeds)
        for source in sources
    ]

    return SourceListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@sources_router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> SourceResponse:
    """
    Create a new source.

    The domain must be unique across all sources.
    """
    # Check if domain already exists
    existing = await db.execute(
        select(Source).where(Source.domain == source_data.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Source with domain '{source_data.domain}' already exists"
        )

    # Create source
    source = Source(
        domain=source_data.domain,
        canonical_name=source_data.canonical_name,
        organization_name=source_data.organization_name,
        description=source_data.description,
        homepage_url=source_data.homepage_url,
        logo_url=source_data.logo_url,
        category=source_data.category,
        country=source_data.country,
        language=source_data.language,
        scrape_method=source_data.scrape_method,
        paywall_type=source_data.paywall_type.value,
        rate_limit_per_minute=source_data.rate_limit_per_minute,
        requires_stealth=source_data.requires_stealth,
        requires_proxy=source_data.requires_proxy,
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    logger.info(f"Created source: {source.domain} (id={source.id})")

    return SourceResponse.from_orm_with_summary(source)


@sources_router.get("/by-domain/{domain}", response_model=SourceResponse)
async def get_source_by_domain(
    domain: str,
    include_feeds: bool = Query(True, description="Include feed details"),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> SourceResponse:
    """
    Get source by domain.

    Useful for looking up sources without knowing the ID.
    """
    # Normalize domain
    domain = domain.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]

    query = select(Source).where(Source.domain == domain)
    if include_feeds:
        query = query.options(selectinload(Source.feeds))

    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source with domain '{domain}' not found")

    return SourceResponse.from_orm_with_summary(source, include_feeds=include_feeds)


@sources_router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    include_feeds: bool = Query(True, description="Include feed details"),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> SourceResponse:
    """
    Get source by ID.
    """
    query = select(Source).where(Source.id == source_id)
    if include_feeds:
        query = query.options(selectinload(Source.feeds))

    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    return SourceResponse.from_orm_with_summary(source, include_feeds=include_feeds)


@sources_router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    update_data: SourceUpdate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> SourceResponse:
    """
    Update source (partial update).
    """
    result = await db.execute(
        select(Source).where(Source.id == source_id).options(selectinload(Source.feeds))
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(source, field):
            # Handle enum values
            if isinstance(value, (SourceStatus, ScrapeStatus, PaywallType)):
                value = value.value
            setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    logger.info(f"Updated source: {source.domain} (id={source.id})")

    return SourceResponse.from_orm_with_summary(source, include_feeds=True)


@sources_router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete source and all associated feeds.
    """
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    domain = source.domain
    await db.delete(source)
    await db.commit()

    logger.info(f"Deleted source: {domain} (id={source_id})")


@sources_router.get("/{source_id}/feeds", response_model=List[SourceFeedResponse])
async def get_source_feeds(
    source_id: UUID,
    is_active: Optional[bool] = None,
    provider_type: Optional[ProviderType] = None,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> List[SourceFeedResponse]:
    """
    Get all feeds for a source.
    """
    # Verify source exists
    source_result = await db.execute(select(Source).where(Source.id == source_id))
    source = source_result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    query = select(SourceFeed).where(SourceFeed.source_id == source_id)

    if is_active is not None:
        query = query.where(SourceFeed.is_active == is_active)
    if provider_type is not None:
        query = query.where(SourceFeed.provider_type == provider_type.value)

    result = await db.execute(query)
    feeds = result.scalars().all()

    return [
        SourceFeedResponse(
            id=f.id,
            source_id=f.source_id,
            provider_type=f.provider_type,
            provider_id=f.provider_id,
            channel_name=f.channel_name,
            feed_url=f.feed_url,
            fetch_interval=f.fetch_interval,
            enable_analysis=f.enable_analysis,
            is_active=f.is_active,
            health_score=f.health_score,
            consecutive_failures=f.consecutive_failures,
            last_fetched_at=f.last_fetched_at,
            last_error=f.last_error,
            etag=f.etag,
            last_modified=f.last_modified,
            total_items=f.total_items,
            items_last_24h=f.items_last_24h,
            discovered_at=f.discovered_at,
            created_at=f.created_at,
            updated_at=f.updated_at,
            source_domain=source.domain,
            source_name=source.canonical_name,
        )
        for f in feeds
    ]


# =============================================================================
# Assessment Endpoints
# =============================================================================

@sources_router.post("/{source_id}/assess", response_model=SourceAssessmentTriggerResponse)
async def trigger_source_assessment(
    source_id: UUID,
    trigger_data: SourceAssessmentTrigger = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> SourceAssessmentTriggerResponse:
    """
    Trigger source assessment via research service.

    This endpoint initiates a credibility assessment for the source.
    The assessment is performed asynchronously by the research service.
    """
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}")

    force = trigger_data.force if trigger_data else False

    # Check if already assessed recently (within 7 days) and not forcing
    if not force and source.assessment_status == AssessmentStatus.COMPLETED.value:
        from datetime import datetime, timedelta
        if source.assessment_date and source.assessment_date > datetime.now(source.assessment_date.tzinfo) - timedelta(days=7):
            return SourceAssessmentTriggerResponse(
                success=False,
                source_id=source.id,
                domain=source.domain,
                message="Source was assessed within the last 7 days. Use force=true to re-assess.",
                assessment_status=source.assessment_status,
            )

    # Update assessment status
    source.assessment_status = AssessmentStatus.IN_PROGRESS.value
    await db.commit()

    # TODO: Trigger actual assessment via research service
    # This would publish an event to RabbitMQ for the research service to pick up
    logger.info(f"Triggered assessment for source: {source.domain} (id={source_id})")

    return SourceAssessmentTriggerResponse(
        success=True,
        source_id=source.id,
        domain=source.domain,
        message="Assessment triggered. Results will be available once research service completes.",
        assessment_status=AssessmentStatus.IN_PROGRESS.value,
    )


@sources_router.get("/{source_id}/assessment-history", response_model=List[SourceAssessmentHistoryResponse])
async def get_source_assessment_history(
    source_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> List[SourceAssessmentHistoryResponse]:
    """
    Get assessment history for a source.
    """
    result = await db.execute(
        select(SourceAssessmentHistory)
        .where(SourceAssessmentHistory.source_id == source_id)
        .order_by(SourceAssessmentHistory.assessment_date.desc())
        .limit(limit)
    )
    history = result.scalars().all()

    return [SourceAssessmentHistoryResponse.model_validate(h) for h in history]


# =============================================================================
# SourceFeed CRUD Endpoints
# =============================================================================

@source_feeds_router.get("", response_model=SourceFeedListResponse)
async def list_source_feeds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_id: Optional[UUID] = None,
    provider_type: Optional[ProviderType] = None,
    is_active: Optional[bool] = None,
    health_score_min: Optional[int] = Query(None, ge=0, le=100),
    health_score_max: Optional[int] = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> SourceFeedListResponse:
    """
    List all source feeds with pagination and filtering.
    """
    query = select(SourceFeed).options(selectinload(SourceFeed.source))

    filters = []
    if source_id is not None:
        filters.append(SourceFeed.source_id == source_id)
    if provider_type is not None:
        filters.append(SourceFeed.provider_type == provider_type.value)
    if is_active is not None:
        filters.append(SourceFeed.is_active == is_active)
    if health_score_min is not None:
        filters.append(SourceFeed.health_score >= health_score_min)
    if health_score_max is not None:
        filters.append(SourceFeed.health_score <= health_score_max)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(SourceFeed)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(SourceFeed.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    feeds = result.scalars().all()

    items = [
        SourceFeedResponse(
            id=f.id,
            source_id=f.source_id,
            provider_type=f.provider_type,
            provider_id=f.provider_id,
            channel_name=f.channel_name,
            feed_url=f.feed_url,
            fetch_interval=f.fetch_interval,
            enable_analysis=f.enable_analysis,
            is_active=f.is_active,
            health_score=f.health_score,
            consecutive_failures=f.consecutive_failures,
            last_fetched_at=f.last_fetched_at,
            last_error=f.last_error,
            etag=f.etag,
            last_modified=f.last_modified,
            total_items=f.total_items,
            items_last_24h=f.items_last_24h,
            discovered_at=f.discovered_at,
            created_at=f.created_at,
            updated_at=f.updated_at,
            source_domain=f.source.domain if f.source else None,
            source_name=f.source.canonical_name if f.source else None,
        )
        for f in feeds
    ]

    return SourceFeedListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@source_feeds_router.post("", response_model=SourceFeedResponse, status_code=201)
async def create_source_feed(
    feed_data: SourceFeedCreate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> SourceFeedResponse:
    """
    Create a new source feed.

    You can provide either:
    - source_id: Link to existing source
    - domain: Auto-create source if not exists, or link to existing

    For RSS feeds, feed_url is required.
    """
    source = None

    # Resolve source
    if feed_data.source_id:
        result = await db.execute(select(Source).where(Source.id == feed_data.source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail=f"Source not found: {feed_data.source_id}")
    elif feed_data.domain:
        # Try to find existing source by domain
        result = await db.execute(select(Source).where(Source.domain == feed_data.domain))
        source = result.scalar_one_or_none()

        if not source:
            # Auto-create source from domain
            source = Source(
                domain=feed_data.domain,
                canonical_name=feed_data.domain,  # Will be updated later via assessment
            )
            db.add(source)
            await db.flush()  # Get ID without committing
            logger.info(f"Auto-created source for domain: {feed_data.domain}")
    elif feed_data.feed_url and feed_data.provider_type == ProviderType.RSS:
        # Extract domain from feed URL
        domain = extract_domain(feed_data.feed_url)
        result = await db.execute(select(Source).where(Source.domain == domain))
        source = result.scalar_one_or_none()

        if not source:
            source = Source(
                domain=domain,
                canonical_name=domain,
            )
            db.add(source)
            await db.flush()
            logger.info(f"Auto-created source from feed URL domain: {domain}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Either source_id, domain, or feed_url (for RSS) must be provided"
        )

    # Check for duplicate feed_url (RSS only)
    if feed_data.feed_url:
        existing = await db.execute(
            select(SourceFeed).where(SourceFeed.feed_url == feed_data.feed_url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Feed with URL '{feed_data.feed_url}' already exists"
            )

    # Create feed
    feed = SourceFeed(
        source_id=source.id,
        provider_type=feed_data.provider_type.value,
        provider_id=feed_data.provider_id,
        channel_name=feed_data.channel_name,
        feed_url=feed_data.feed_url,
        fetch_interval=feed_data.fetch_interval,
        enable_analysis=feed_data.enable_analysis,
    )

    db.add(feed)
    await db.commit()
    await db.refresh(feed)

    logger.info(f"Created source feed: {feed.feed_url or feed.provider_id} for source {source.domain}")

    return SourceFeedResponse(
        id=feed.id,
        source_id=feed.source_id,
        provider_type=feed.provider_type,
        provider_id=feed.provider_id,
        channel_name=feed.channel_name,
        feed_url=feed.feed_url,
        fetch_interval=feed.fetch_interval,
        enable_analysis=feed.enable_analysis,
        is_active=feed.is_active,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        last_fetched_at=feed.last_fetched_at,
        last_error=feed.last_error,
        etag=feed.etag,
        last_modified=feed.last_modified,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        discovered_at=feed.discovered_at,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        source_domain=source.domain,
        source_name=source.canonical_name,
    )


@source_feeds_router.get("/{feed_id}", response_model=SourceFeedWithSourceResponse)
async def get_source_feed(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
) -> SourceFeedWithSourceResponse:
    """
    Get source feed by ID with full source details.
    """
    result = await db.execute(
        select(SourceFeed)
        .where(SourceFeed.id == feed_id)
        .options(selectinload(SourceFeed.source))
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Source feed not found: {feed_id}")

    source_response = SourceResponse.from_orm_with_summary(feed.source) if feed.source else None

    return SourceFeedWithSourceResponse(
        id=feed.id,
        source_id=feed.source_id,
        provider_type=feed.provider_type,
        provider_id=feed.provider_id,
        channel_name=feed.channel_name,
        feed_url=feed.feed_url,
        fetch_interval=feed.fetch_interval,
        enable_analysis=feed.enable_analysis,
        is_active=feed.is_active,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        last_fetched_at=feed.last_fetched_at,
        last_error=feed.last_error,
        etag=feed.etag,
        last_modified=feed.last_modified,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        discovered_at=feed.discovered_at,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        source_domain=feed.source.domain if feed.source else None,
        source_name=feed.source.canonical_name if feed.source else None,
        source=source_response,
    )


@source_feeds_router.patch("/{feed_id}", response_model=SourceFeedResponse)
async def update_source_feed(
    feed_id: UUID,
    update_data: SourceFeedUpdate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> SourceFeedResponse:
    """
    Update source feed (partial update).
    """
    result = await db.execute(
        select(SourceFeed)
        .where(SourceFeed.id == feed_id)
        .options(selectinload(SourceFeed.source))
    )
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Source feed not found: {feed_id}")

    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(feed, field):
            setattr(feed, field, value)

    await db.commit()
    await db.refresh(feed)

    logger.info(f"Updated source feed: {feed.id}")

    return SourceFeedResponse(
        id=feed.id,
        source_id=feed.source_id,
        provider_type=feed.provider_type,
        provider_id=feed.provider_id,
        channel_name=feed.channel_name,
        feed_url=feed.feed_url,
        fetch_interval=feed.fetch_interval,
        enable_analysis=feed.enable_analysis,
        is_active=feed.is_active,
        health_score=feed.health_score,
        consecutive_failures=feed.consecutive_failures,
        last_fetched_at=feed.last_fetched_at,
        last_error=feed.last_error,
        etag=feed.etag,
        last_modified=feed.last_modified,
        total_items=feed.total_items,
        items_last_24h=feed.items_last_24h,
        discovered_at=feed.discovered_at,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        source_domain=feed.source.domain if feed.source else None,
        source_name=feed.source.canonical_name if feed.source else None,
    )


@source_feeds_router.delete("/{feed_id}", status_code=204)
async def delete_source_feed(
    feed_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete source feed.

    Note: This only deletes the feed, not the parent source.
    """
    result = await db.execute(select(SourceFeed).where(SourceFeed.id == feed_id))
    feed = result.scalar_one_or_none()

    if not feed:
        raise HTTPException(status_code=404, detail=f"Source feed not found: {feed_id}")

    await db.delete(feed)
    await db.commit()

    logger.info(f"Deleted source feed: {feed_id}")


# =============================================================================
# Bulk Operations
# =============================================================================

@sources_router.post("/bulk", response_model=BulkSourceCreateResponse)
async def bulk_create_sources(
    bulk_data: BulkSourceCreate,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
) -> BulkSourceCreateResponse:
    """
    Bulk create sources from a list of domains.

    Skips domains that already exist.
    """
    created = 0
    skipped = 0
    failed = 0
    details = []

    for domain in bulk_data.domains:
        try:
            # Normalize domain
            domain = domain.lower().strip()
            if domain.startswith('www.'):
                domain = domain[4:]

            # Check if exists
            existing = await db.execute(select(Source).where(Source.domain == domain))
            if existing.scalar_one_or_none():
                skipped += 1
                details.append({"domain": domain, "status": "skipped", "reason": "already exists"})
                continue

            # Create source
            source = Source(
                domain=domain,
                canonical_name=domain,  # Will be updated via assessment
            )
            db.add(source)
            created += 1
            details.append({"domain": domain, "status": "created"})

        except Exception as e:
            failed += 1
            details.append({"domain": domain, "status": "failed", "error": str(e)})
            logger.error(f"Failed to create source for domain {domain}: {e}")

    await db.commit()

    return BulkSourceCreateResponse(
        created=created,
        skipped=skipped,
        failed=failed,
        details=details,
    )
