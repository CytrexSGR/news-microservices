"""HTTP client for search-service with circuit breaker protection."""

import httpx
import logging
from typing import Dict, Any, Optional, List

from ..config import settings
from ..resilience import (
    ResilientHTTPClient,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    HTTPCircuitBreakerError,
)
from ..cache import cache_manager

logger = logging.getLogger(__name__)


class SearchClient:
    """Client for search-service (Port 8106) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.search_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="search-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def search_articles(
        self,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        source: Optional[str] = None,
        sentiment: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Basic article search with PostgreSQL full-text search.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            query: Search query
            page: Page number
            page_size: Results per page (max 100)
            source: Filter by source (comma-separated)
            sentiment: Filter by sentiment (comma-separated)
            date_from: Filter by date from (ISO format)
            date_to: Filter by date to (ISO format)

        Returns:
            Search results with articles, pagination, and facets

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"page": page, "page_size": page_size}
            if query:
                params["query"] = query
            if source:
                params["source"] = source
            if sentiment:
                params["sentiment"] = sentiment
            if date_from:
                params["date_from"] = date_from
            if date_to:
                params["date_to"] = date_to

            response = await self.client.get("/api/v1/search", params=params)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"query": query, "page": page, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to search articles: {e}",
                extra={"query": query, "page": page, "error": str(e)},
            )
            raise

    async def advanced_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        fuzzy: bool = False,
        highlight: bool = True,
        facets: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Advanced search with complex query features.

        Supports: fuzzy matching, highlighting, faceted search,
        AND/OR operators, phrase search, field search, exclusion.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            query: Search query
            filters: Advanced filters (source, sentiment, date range, etc.)
            fuzzy: Enable fuzzy matching
            highlight: Enable result highlighting
            facets: Facets to return
            page: Page number
            page_size: Results per page

        Returns:
            Search results with facets and highlights

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {
                "query": query,
                "filters": filters or {},
                "fuzzy": fuzzy,
                "highlight": highlight,
                "facets": facets or [],
                "page": page,
                "page_size": page_size,
            }

            response = await self.client.post("/api/v1/search/advanced", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"query": query, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed advanced search: {e}",
                extra={"query": query, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_short, key_prefix="search:suggestions"
    )
    async def get_search_suggestions(
        self, query: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get search query suggestions/autocomplete.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes for fast response.

        Args:
            query: Partial query string
            limit: Maximum suggestions to return

        Returns:
            List of suggested queries with metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/search/suggest", params={"query": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"query": query, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get search suggestions: {e}",
                extra={"query": query, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_medium, key_prefix="search:facets")
    async def get_search_facets(self) -> Dict[str, Any]:
        """
        Get available facets for search filtering.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes (facets change slowly).

        Returns:
            Available facets (sources, sentiment, categories, etc.)

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/search/facets")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get search facets: {e}", extra={"error": str(e)}
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_short, key_prefix="search:popular")
    async def get_popular_searches(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get popular/trending searches.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes for trending data.

        Args:
            limit: Maximum searches to return

        Returns:
            Popular searches with search counts

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/search/popular", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get popular searches: {e}", extra={"error": str(e)}
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_short, key_prefix="search:related")
    async def get_related_searches(
        self, query: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get related searches based on query.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes.

        Args:
            query: Search query
            limit: Maximum related searches to return

        Returns:
            Related searches with relevance scores

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/search/related", params={"query": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"query": query, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get related searches: {e}",
                extra={"query": query, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium, key_prefix="search:saved_searches"
    )
    async def list_saved_searches(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List user's saved searches.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            user_id: Optional user ID for filtering

        Returns:
            List of saved searches

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {}
            if user_id:
                params["user_id"] = user_id

            response = await self.client.get(
                "/api/v1/saved-searches", params=params if params else None
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to list saved searches: {e}", extra={"error": str(e)}
            )
            raise

    async def create_saved_search(
        self, name: str, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create/save a search query.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            name: Name for the saved search
            query: Search query
            filters: Optional filters

        Returns:
            Created saved search

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {"name": name, "query": query, "filters": filters or {}}

            response = await self.client.post("/api/v1/saved-searches", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"name": name, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to create saved search: {e}",
                extra={"name": name, "error": str(e)},
            )
            raise

    async def delete_saved_search(self, search_id: str) -> None:
        """
        Delete saved search.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            search_id: Saved search ID

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.delete(
                f"/api/v1/saved-searches/{search_id}"
            )
            response.raise_for_status()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"search_id": search_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to delete saved search: {e}",
                extra={"search_id": search_id, "error": str(e)},
            )
            raise

    async def get_saved_search(self, search_id: str) -> Dict[str, Any]:
        """
        Get single saved search by ID.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            search_id: Saved search ID

        Returns:
            Saved search details

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/search/saved/{search_id}")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"search_id": search_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get saved search: {e}",
                extra={"search_id": search_id, "error": str(e)},
            )
            raise

    async def update_saved_search(
        self,
        search_id: str,
        name: Optional[str] = None,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update saved search.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            search_id: Saved search ID
            name: New name (optional)
            query: New query (optional)
            filters: New filters (optional)

        Returns:
            Updated saved search

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {}
            if name is not None:
                payload["name"] = name
            if query is not None:
                payload["query"] = query
            if filters is not None:
                payload["filters"] = filters

            response = await self.client.put(
                f"/api/v1/search/saved/{search_id}", json=payload
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"search_id": search_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to update saved search: {e}",
                extra={"search_id": search_id, "error": str(e)},
            )
            raise

    async def get_search_history(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get search history.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            user_id: Optional user ID for filtering
            limit: Maximum results

        Returns:
            Search history with queries and timestamps

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if user_id:
                params["user_id"] = user_id

            response = await self.client.get("/api/v1/search/history", params=params)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get search history: {e}", extra={"error": str(e)}
            )
            raise

    async def clear_search_history(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear search history.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            user_id: Optional user ID (clears all if not provided)

        Returns:
            Deletion result

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {}
            if user_id:
                params["user_id"] = user_id

            response = await self.client.delete(
                "/api/v1/search/history", params=params if params else None
            )
            response.raise_for_status()
            return {"success": True, "message": "Search history cleared"}
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for search-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to clear search history: {e}", extra={"error": str(e)}
            )
            raise
