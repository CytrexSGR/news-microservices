"""MediaStack service client for MCP Orchestration Server."""

import logging
from typing import Any, Dict, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class MediaStackClient(BaseClient):
    """Client for mediastack-service (Port 8121)."""

    def __init__(self):
        super().__init__(
            service_name="mediastack-service",
            base_url=settings.mediastack_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    # =========================================================================
    # Live News
    # =========================================================================

    async def get_live_news(
        self,
        keywords: Optional[str] = None,
        sources: Optional[str] = None,
        categories: Optional[str] = None,
        countries: Optional[str] = None,
        languages: Optional[str] = None,
        sort: Optional[str] = "published_desc",
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Fetch live news articles.

        Args:
            keywords: Search keywords
            sources: Filter by sources (comma-separated)
            categories: Filter by categories (comma-separated)
            countries: Filter by countries (comma-separated)
            languages: Filter by languages (comma-separated)
            sort: Sort order (published_desc, published_asc, popularity)
            limit: Results per page (1-100)
            offset: Pagination offset

        Returns:
            News articles with pagination and usage stats
        """
        params = {"limit": limit, "offset": offset}
        if keywords:
            params["keywords"] = keywords
        if sources:
            params["sources"] = sources
        if categories:
            params["categories"] = categories
        if countries:
            params["countries"] = countries
        if languages:
            params["languages"] = languages
        if sort:
            params["sort"] = sort

        return await self.request("GET", "/api/v1/news/live", params=params)

    # =========================================================================
    # Historical News
    # =========================================================================

    async def get_historical_news(
        self,
        keywords: Optional[str] = None,
        sources: Optional[str] = None,
        categories: Optional[str] = None,
        countries: Optional[str] = None,
        languages: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort: Optional[str] = "published_desc",
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Fetch historical news articles.

        Note: Requires PAID MediaStack plan.

        Args:
            keywords: Search keywords
            sources: Filter by sources
            categories: Filter by categories
            countries: Filter by countries
            languages: Filter by languages
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            sort: Sort order (published_desc, published_asc, popularity)
            limit: Results per page (1-100)
            offset: Pagination offset

        Returns:
            Historical news articles with pagination
        """
        params = {"limit": limit, "offset": offset}
        if keywords:
            params["keywords"] = keywords
        if sources:
            params["sources"] = sources
        if categories:
            params["categories"] = categories
        if countries:
            params["countries"] = countries
        if languages:
            params["languages"] = languages
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if sort:
            params["sort"] = sort

        return await self.request("GET", "/api/v1/news/historical", params=params)

    # =========================================================================
    # Sources
    # =========================================================================

    async def get_sources(
        self,
        countries: Optional[str] = None,
        categories: Optional[str] = None,
        languages: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get available news sources.

        Args:
            countries: Filter by countries
            categories: Filter by categories
            languages: Filter by languages
            limit: Maximum sources to return

        Returns:
            List of available news sources
        """
        params = {"limit": limit}
        if countries:
            params["countries"] = countries
        if categories:
            params["categories"] = categories
        if languages:
            params["languages"] = languages

        return await self.request("GET", "/api/v1/news/sources", params=params)

    # =========================================================================
    # Usage Statistics
    # =========================================================================

    async def get_usage(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.

        Returns:
            Usage stats including calls made, remaining, percentage used
        """
        return await self.request("GET", "/api/v1/news/usage")
