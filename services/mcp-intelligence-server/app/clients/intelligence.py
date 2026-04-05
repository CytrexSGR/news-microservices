"""HTTP client for intelligence-service with circuit breaker protection."""

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


class IntelligenceClient:
    """Client for intelligence-service (Port 8118) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.intelligence_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="intelligence-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="intelligence:event_clusters"
    )
    async def get_event_clusters(
        self, limit: int = 50, min_articles: int = 3
    ) -> Dict[str, Any]:
        """
        Get event clusters from intelligence analysis.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes to reduce load on intelligence-service.

        Args:
            limit: Maximum clusters to return
            min_articles: Minimum articles per cluster

        Returns:
            List of event clusters with metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/intelligence/clusters",
                params={"limit": limit, "min_articles": min_articles},
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"limit": limit, "min_articles": min_articles, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get event clusters: {e}",
                extra={"limit": limit, "min_articles": min_articles, "error": str(e)},
            )
            raise

    async def get_cluster_details(self, cluster_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific event cluster.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            cluster_id: Cluster identifier

        Returns:
            Cluster details with articles, entities, and timeline

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/intelligence/clusters/{cluster_id}"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"cluster_id": cluster_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get cluster details for {cluster_id}: {e}",
                extra={"cluster_id": cluster_id, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_short,
        key_prefix="intelligence:latest_events"
    )
    async def get_latest_events(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get latest intelligence events with timestamps.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes for fast-changing data.

        Args:
            limit: Maximum events to return

        Returns:
            Latest events with summaries and timestamps

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/intelligence/events/latest", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"limit": limit, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get latest events: {e}",
                extra={"limit": limit, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="intelligence:overview"
    )
    async def get_intelligence_overview(self) -> Dict[str, Any]:
        """
        Get intelligence overview dashboard with statistics.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes for dashboard data.

        Returns:
            Overview with cluster counts, trending entities, and metrics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/intelligence/overview")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get intelligence overview: {e}",
                extra={"error": str(e)},
            )
            raise

    async def trigger_clustering(self) -> Dict[str, Any]:
        """
        Trigger manual event clustering analysis.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Clustering job status

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post("/api/v1/intelligence/cluster/trigger")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to trigger clustering: {e}",
                extra={"error": str(e)},
            )
            raise

    async def get_cluster_events(
        self, cluster_id: str, page: int = 1, per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated events for a specific cluster.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            cluster_id: Cluster identifier
            page: Page number (1-indexed)
            per_page: Items per page (max 100)

        Returns:
            Paginated list of events with title, source, entities, keywords, sentiment

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails or cluster not found
        """
        try:
            response = await self.client.get(
                f"/api/v1/intelligence/clusters/{cluster_id}/events",
                params={"page": page, "per_page": per_page},
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"cluster_id": cluster_id, "page": page, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get cluster events for {cluster_id}: {e}",
                extra={"cluster_id": cluster_id, "page": page, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="intelligence:subcategories"
    )
    async def get_subcategories(self) -> Dict[str, Any]:
        """
        Get top 2 sub-topics per category (geo, finance, tech).

        Dynamic sub-category discovery from current news data.
        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes (semi-stable data).

        Returns:
            Top 2 keywords/topics per category with risk scores and event counts
            Example: {"geo": [{"name": "Ukraine", "risk_score": 85.2, "event_count": 42}], ...}

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/intelligence/subcategories")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get subcategories: {e}",
                extra={"error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_short,
        key_prefix="intelligence:risk_history"
    )
    async def get_risk_history(self, days: int = 7) -> Dict[str, Any]:
        """
        Get historical risk scores for trend visualization.

        Returns daily risk score history for global, geo, and finance categories.
        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes (frequently updated data).

        Args:
            days: Days to look back (1-30, default: 7)

        Returns:
            Daily risk history with dates, risk scores, and event counts
            Example: {"history": [{"date": "2025-12-01", "global_risk": 72.5, "geo_risk": 85.0, ...}], ...}

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/intelligence/risk-history", params={"days": days}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"days": days, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get risk history: {e}",
                extra={"days": days, "error": str(e)},
            )
            raise

    async def detect_events(
        self,
        text: str,
        include_keywords: bool = True,
        max_keywords: int = 10
    ) -> Dict[str, Any]:
        """
        Detect entities and keywords from text content.

        Uses spaCy NLP to extract persons, organizations, locations,
        and important keywords from the provided text.

        Circuit breaker protection: Fails fast during service outages.
        NOT cached since results depend on unique input text.

        Args:
            text: Text content to analyze (10-50000 chars)
            include_keywords: Include keyword extraction (default: True)
            max_keywords: Maximum keywords to extract (1-50, default: 10)

        Returns:
            Extracted entities and keywords with processing metrics
            Example: {
                "entities": {"persons": [...], "organizations": [...], "locations": [...]},
                "keywords": [...],
                "entity_count": 5,
                "text_length": 1234,
                "processing_time_ms": 45
            }

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(
                "/api/v1/intelligence/events/detect",
                json={
                    "text": text,
                    "include_keywords": include_keywords,
                    "max_keywords": max_keywords,
                },
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"text_length": len(text), "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to detect events: {e}",
                extra={"text_length": len(text), "error": str(e)},
            )
            raise

    async def calculate_risk(
        self,
        cluster_id: Optional[str] = None,
        entities: Optional[List[str]] = None,
        text: Optional[str] = None,
        include_factors: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate risk score for a cluster, entities, or text.

        Three calculation modes:
        1. Cluster mode: Provide cluster_id
        2. Entity mode: Provide entities (array of names)
        3. Text mode: Provide text content

        Circuit breaker protection: Fails fast during service outages.
        NOT cached since risk calculations should be fresh.

        Args:
            cluster_id: Cluster UUID to calculate risk for
            entities: Entity names to analyze
            text: Text content to analyze (max 50000 chars)
            include_factors: Include factor breakdown (default: True)

        Returns:
            Risk calculation result with score, level, and factors
            Example: {
                "risk_score": 67.5,
                "risk_level": "high",
                "risk_delta": 3.2,
                "factors": [...],
                "cluster_id": "...",
                "timestamp": "..."
            }

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
            ValueError: If no valid input provided
        """
        # Build request payload
        payload: Dict[str, Any] = {"include_factors": include_factors}

        if cluster_id:
            payload["cluster_id"] = cluster_id
        if entities:
            payload["entities"] = entities
        if text:
            payload["text"] = text

        # Validate at least one input
        if not any([cluster_id, entities, text]):
            raise ValueError("At least one of cluster_id, entities, or text required")

        try:
            response = await self.client.post(
                "/api/v1/intelligence/risk/calculate",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for intelligence-service: {e}",
                extra={"cluster_id": cluster_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to calculate risk: {e}",
                extra={"cluster_id": cluster_id, "error": str(e)},
            )
            raise
