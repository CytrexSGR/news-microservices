"""API endpoints for news operations."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.schemas import (
    NewsRequest,
    NewsResponse,
    NewsArticle,
    Pagination,
    SourcesRequest,
    SourcesResponse,
    SourceInfo,
    UsageStats
)
from app.clients.mediastack_client import (
    get_mediastack_client,
    MediaStackClient,
    MediaStackError
)
from app.services.usage_tracker import get_usage_tracker, UsageTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


def get_client() -> MediaStackClient:
    """Dependency for MediaStack client."""
    return get_mediastack_client()


def get_tracker() -> UsageTracker:
    """Dependency for usage tracker."""
    return get_usage_tracker()


@router.get("/live", response_model=NewsResponse)
async def get_live_news(
    keywords: Optional[str] = Query(None, description="Search keywords"),
    sources: Optional[str] = Query(None, description="Filter by sources"),
    categories: Optional[str] = Query(None, description="Filter by categories"),
    countries: Optional[str] = Query(None, description="Filter by countries"),
    languages: Optional[str] = Query(None, description="Filter by languages"),
    sort: Optional[str] = Query("published_desc", description="Sort order: published_desc, published_asc, popularity"),
    limit: int = Query(25, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    client: MediaStackClient = Depends(get_client),
    tracker: UsageTracker = Depends(get_tracker)
) -> NewsResponse:
    """
    Fetch live news articles from MediaStack API.

    This endpoint is available on the free plan.
    Rate limit: 10,000 calls/month.
    """
    # Check rate limit
    if not await tracker.can_make_request():
        usage = await tracker.get_usage_stats()
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Monthly rate limit exceeded",
                "usage": usage
            }
        )

    try:
        # Fetch from MediaStack
        result = await client.fetch_live_news(
            keywords=keywords,
            sources=sources,
            categories=categories,
            countries=countries,
            languages=languages,
            sort=sort,
            limit=limit,
            offset=offset
        )

        # Record API call
        await tracker.record_request()

        # Transform to response schema
        articles = [
            NewsArticle(**article) for article in result.get("data", [])
        ]

        pagination_data = result.get("pagination", {})
        pagination = Pagination(
            limit=pagination_data.get("limit", limit),
            offset=pagination_data.get("offset", offset),
            count=pagination_data.get("count", len(articles)),
            total=pagination_data.get("total", len(articles))
        )

        usage = await tracker.get_usage_stats()

        return NewsResponse(
            pagination=pagination,
            data=articles,
            usage=UsageStats(**usage)
        )

    except MediaStackError as e:
        logger.error(f"MediaStack API error: {e.message} (code={e.code})")
        raise HTTPException(
            status_code=502,
            detail=f"MediaStack API error: {e.message}"
        )


@router.get("/historical", response_model=NewsResponse)
async def get_historical_news(
    keywords: Optional[str] = Query(None, description="Search keywords"),
    sources: Optional[str] = Query(None, description="Filter by sources"),
    categories: Optional[str] = Query(None, description="Filter by categories"),
    countries: Optional[str] = Query(None, description="Filter by countries"),
    languages: Optional[str] = Query(None, description="Filter by languages"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sort: Optional[str] = Query("published_desc", description="Sort order: published_desc, published_asc, popularity"),
    limit: int = Query(25, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    client: MediaStackClient = Depends(get_client),
    tracker: UsageTracker = Depends(get_tracker)
) -> NewsResponse:
    """
    Fetch historical news articles from MediaStack API.

    **Note:** This endpoint requires a PAID MediaStack plan.
    Free plan users will receive an API error.
    """
    # Check rate limit
    if not await tracker.can_make_request():
        usage = await tracker.get_usage_stats()
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Monthly rate limit exceeded",
                "usage": usage
            }
        )

    try:
        result = await client.fetch_historical_news(
            keywords=keywords,
            sources=sources,
            categories=categories,
            countries=countries,
            languages=languages,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            limit=limit,
            offset=offset
        )

        await tracker.record_request()

        articles = [
            NewsArticle(**article) for article in result.get("data", [])
        ]

        pagination_data = result.get("pagination", {})
        pagination = Pagination(
            limit=pagination_data.get("limit", limit),
            offset=pagination_data.get("offset", offset),
            count=pagination_data.get("count", len(articles)),
            total=pagination_data.get("total", len(articles))
        )

        usage = await tracker.get_usage_stats()

        return NewsResponse(
            pagination=pagination,
            data=articles,
            usage=UsageStats(**usage)
        )

    except MediaStackError as e:
        logger.error(f"MediaStack API error: {e.message} (code={e.code})")
        raise HTTPException(
            status_code=502,
            detail=f"MediaStack API error: {e.message}"
        )


@router.get("/sources", response_model=SourcesResponse)
async def get_sources(
    countries: Optional[str] = Query(None, description="Filter by countries"),
    categories: Optional[str] = Query(None, description="Filter by categories"),
    languages: Optional[str] = Query(None, description="Filter by languages"),
    limit: int = Query(100, ge=1, le=1000, description="Max sources"),
    client: MediaStackClient = Depends(get_client),
    tracker: UsageTracker = Depends(get_tracker)
) -> SourcesResponse:
    """
    Get available news sources from MediaStack.

    Use this to discover which sources are available for filtering.
    """
    if not await tracker.can_make_request():
        usage = await tracker.get_usage_stats()
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Monthly rate limit exceeded",
                "usage": usage
            }
        )

    try:
        result = await client.get_sources(
            countries=countries,
            categories=categories,
            languages=languages,
            limit=limit
        )

        await tracker.record_request()

        sources = [
            SourceInfo(**source) for source in result.get("data", [])
        ]

        usage = await tracker.get_usage_stats()

        return SourcesResponse(
            data=sources,
            usage=UsageStats(**usage)
        )

    except MediaStackError as e:
        logger.error(f"MediaStack API error: {e.message} (code={e.code})")
        raise HTTPException(
            status_code=502,
            detail=f"MediaStack API error: {e.message}"
        )


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    tracker: UsageTracker = Depends(get_tracker)
) -> UsageStats:
    """
    Get current API usage statistics.

    Returns:
    - current_calls: Calls made this month
    - monthly_limit: Maximum calls allowed
    - remaining: Calls remaining
    - percentage: Percentage of limit used
    - status: ok/warning/critical
    """
    usage = await tracker.get_usage_stats()
    return UsageStats(**usage)
