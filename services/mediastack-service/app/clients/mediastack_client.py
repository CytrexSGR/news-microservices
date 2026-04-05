"""MediaStack API Client with Rate Limiting."""

import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaStackError(Exception):
    """MediaStack API error."""

    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MediaStackClient:
    """
    Client for MediaStack News API.

    Free Plan Limits:
    - 10,000 requests/month
    - HTTP only (no HTTPS)
    - Live news only (no historical)

    Paid Plan adds:
    - HTTPS support
    - Historical news
    - More sources
    """

    def __init__(self):
        self.base_url = settings.MEDIASTACK_BASE_URL
        self.api_key = settings.MEDIASTACK_API_KEY

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        )

        logger.info(f"MediaStack client initialized (base_url={self.base_url})")

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make request to MediaStack API.

        Args:
            endpoint: API endpoint (e.g., 'news', 'sources')
            params: Query parameters

        Returns:
            API response data

        Raises:
            MediaStackError: On API error
        """
        url = f"{self.base_url}/{endpoint}"

        # Add API key to params
        request_params = {"access_key": self.api_key}
        if params:
            request_params.update(params)

        try:
            response = await self.client.get(url, params=request_params)
            data = response.json()

            # Check for API error
            if "error" in data:
                error = data["error"]
                raise MediaStackError(
                    message=error.get("message", "Unknown error"),
                    code=error.get("code", 0)
                )

            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise MediaStackError(f"HTTP error: {e}")

    async def fetch_live_news(
        self,
        keywords: Optional[str] = None,
        sources: Optional[str] = None,
        categories: Optional[str] = None,
        countries: Optional[str] = None,
        languages: Optional[str] = None,
        sort: Optional[str] = "published_desc",
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch live news articles.

        Args:
            keywords: Search keywords (comma-separated for OR)
            sources: Filter by sources (e.g., "cnn,bbc")
            categories: Filter by categories (general,business,technology,etc.)
            countries: Filter by countries (e.g., "us,gb")
            languages: Filter by languages (e.g., "en,de")
            sort: Sort order (published_desc, published_asc, popularity)
            limit: Results per page (max 100)
            offset: Pagination offset

        Returns:
            API response with pagination and articles
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }

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

        return await self._request("news", params=params)

    async def fetch_historical_news(
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
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch historical news articles (paid plans only).

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            sort: Sort order (published_desc, published_asc, popularity)
            ... (same as fetch_live_news)

        Returns:
            API response with pagination and articles
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }

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
        if date_from and date_to:
            params["date"] = f"{date_from},{date_to}"
        elif date_from:
            params["date"] = date_from
        if sort:
            params["sort"] = sort

        return await self._request("news", params=params)

    async def get_sources(
        self,
        countries: Optional[str] = None,
        categories: Optional[str] = None,
        languages: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get available news sources.

        Args:
            countries: Filter by countries
            categories: Filter by categories
            languages: Filter by languages
            limit: Max sources to return

        Returns:
            List of available sources
        """
        params = {"limit": limit}

        if countries:
            params["countries"] = countries
        if categories:
            params["categories"] = categories
        if languages:
            params["languages"] = languages

        return await self._request("sources", params=params)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton instance
_client: Optional[MediaStackClient] = None


def get_mediastack_client() -> MediaStackClient:
    """Get singleton MediaStack client."""
    global _client
    if _client is None:
        _client = MediaStackClient()
    return _client
