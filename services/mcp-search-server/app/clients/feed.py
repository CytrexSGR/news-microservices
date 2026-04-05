"""HTTP client for feed-service with circuit breaker protection."""

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


class FeedClient:
    """Client for feed-service (Port 8101) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.feed_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="feed-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    @cache_manager.cached(ttl=settings.cache_ttl_medium, key_prefix="feed:list")
    async def list_feeds(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all RSS/Atom feeds with pagination.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            page: Page number
            page_size: Results per page
            status: Filter by feed status (active, paused, error)
            category: Filter by category

        Returns:
            List of feeds with metadata, health scores, last fetch time

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"page": page, "page_size": page_size}
            if status:
                params["status"] = status
            if category:
                params["category"] = category

            response = await self.client.get("/api/v1/feeds", params=params)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"page": page, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to list feeds: {e}",
                extra={"page": page, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_medium, key_prefix="feed:details")
    async def get_feed(self, feed_id: int) -> Dict[str, Any]:
        """
        Get specific feed details.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            feed_id: Feed ID

        Returns:
            Feed details with configuration, health, statistics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/feeds/{feed_id}")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get feed: {e}",
                extra={"feed_id": feed_id, "error": str(e)},
            )
            raise

    async def create_feed(
        self,
        url: str,
        name: str,
        category: Optional[str] = None,
        fetch_interval: int = 300,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create/add new RSS/Atom feed.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            url: Feed URL
            name: Feed name
            category: Optional category
            fetch_interval: Fetch interval in seconds (default: 300 = 5min)
            tags: Optional tags for organization

        Returns:
            Created feed with ID and initial health assessment

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {
                "url": url,
                "name": name,
                "fetch_interval": fetch_interval,
            }
            if category:
                payload["category"] = category
            if tags:
                payload["tags"] = tags

            response = await self.client.post("/api/v1/feeds", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"url": url, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to create feed: {e}",
                extra={"url": url, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_short, key_prefix="feed:items")
    async def get_feed_items(
        self,
        feed_id: int,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get feed items/articles with pagination.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes for frequently changing content.

        Args:
            feed_id: Feed ID
            page: Page number
            page_size: Results per page
            date_from: Filter by date from (ISO format)
            date_to: Filter by date to (ISO format)

        Returns:
            List of feed items with title, content, published date, metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"page": page, "page_size": page_size}
            if date_from:
                params["date_from"] = date_from
            if date_to:
                params["date_to"] = date_to

            response = await self.client.get(
                f"/api/v1/feeds/{feed_id}/items", params=params
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "page": page, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get feed items: {e}",
                extra={"feed_id": feed_id, "page": page, "error": str(e)},
            )
            raise

    async def assess_feed(self, feed_id: int) -> Dict[str, Any]:
        """
        Assess feed credibility with Perplexity AI.

        Circuit breaker protection: Fails fast during service outages.
        Uses Perplexity to evaluate source reliability, bias, fact-checking record.

        Args:
            feed_id: Feed ID to assess

        Returns:
            Credibility assessment with scores, reasoning, recommendations

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(f"/api/v1/feeds/{feed_id}/assess")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to assess feed: {e}",
                extra={"feed_id": feed_id, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_short, key_prefix="feed:health")
    async def get_feed_health(self, feed_id: int) -> Dict[str, Any]:
        """
        Get feed health status.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes.

        Args:
            feed_id: Feed ID

        Returns:
            Health metrics: uptime, error rate, fetch success rate, response time

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/feeds/{feed_id}/health")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get feed health: {e}",
                extra={"feed_id": feed_id, "error": str(e)},
            )
            raise

    async def pre_assess_feed(self, feed_url: str) -> Dict[str, Any]:
        """
        Pre-assess feed before adding (preview quality).

        Circuit breaker protection: Fails fast during service outages.
        Uses Perplexity to evaluate feed quality before committing.

        Args:
            feed_url: Feed URL to assess

        Returns:
            Quality assessment with recommendation (add/skip), reasoning

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {"url": feed_url}
            response = await self.client.post("/api/v1/feeds/pre-assess", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_url": feed_url, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to pre-assess feed: {e}",
                extra={"feed_url": feed_url, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium, key_prefix="feed:assessment_history"
    )
    async def get_assessment_history(
        self, feed_id: int, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get feed assessment history.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            feed_id: Feed ID
            limit: Maximum assessments to return

        Returns:
            List of historical assessments with scores and trends

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/feeds/{feed_id}/assessment-history", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get assessment history: {e}",
                extra={"feed_id": feed_id, "error": str(e)},
            )
            raise

    async def fetch_feed(self, feed_id: int) -> Dict[str, Any]:
        """
        Manually trigger feed fetch (immediate update).

        Circuit breaker protection: Fails fast during service outages.

        Args:
            feed_id: Feed ID to fetch

        Returns:
            Fetch result with new items count, errors, status

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(f"/api/v1/feeds/{feed_id}/fetch")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for feed-service: {e}",
                extra={"feed_id": feed_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to fetch feed: {e}",
                extra={"feed_id": feed_id, "error": str(e)},
            )
            raise
