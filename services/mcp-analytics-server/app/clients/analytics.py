"""HTTP client for analytics-service with circuit breaker protection."""

import httpx
import logging
from typing import Dict, Any, Optional

from ..config import settings
from ..resilience import (
    ResilientHTTPClient,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    HTTPCircuitBreakerError,
)
from ..cache import cache_manager

logger = logging.getLogger(__name__)


class AnalyticsClient:
    """Client for analytics-service (Port 8107) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.analytics_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="analytics-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_overview(self) -> Dict[str, Any]:
        """
        Get system-wide analytics overview.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Overview with metrics summary, health status, trends

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/analytics/overview")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Analytics overview request failed: {e}")
            raise

    async def get_trends(
        self,
        metric: Optional[str] = None,
        period: str = "7d",
    ) -> Dict[str, Any]:
        """
        Get analytics trends over time.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            metric: Specific metric to get trends for (optional)
            period: Time period (1h, 24h, 7d, 30d)

        Returns:
            Trend data with time series

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"period": period}
            if metric:
                params["metric"] = metric

            response = await self.client.get("/api/v1/analytics/trends", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Analytics trends request failed: {e}")
            raise

    async def get_circuit_breakers(self) -> Dict[str, Any]:
        """
        Get circuit breaker status for all monitored services.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Circuit breaker status for each service

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/monitoring/circuit-breakers")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Circuit breaker status request failed: {e}")
            raise

    async def get_query_performance(self) -> Dict[str, Any]:
        """
        Get database query performance metrics.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Query performance stats (slow queries, avg times, etc.)

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/monitoring/query-performance")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Query performance request failed: {e}")
            raise

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get detailed system metrics.

        Returns:
            Detailed metrics for all monitored components
        """
        try:
            response = await self.client.get("/api/v1/analytics/metrics")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Analytics metrics request failed: {e}")
            raise

    async def get_service_analytics(self, service_name: str) -> Dict[str, Any]:
        """
        Get analytics for a specific service.

        Args:
            service_name: Name of the service to analyze

        Returns:
            Service-specific analytics data
        """
        try:
            response = await self.client.get(f"/api/v1/analytics/service/{service_name}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Service analytics request failed: {e}")
            raise

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Cache hit rates, memory usage, and performance metrics
        """
        try:
            response = await self.client.get("/api/v1/cache/stats")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Cache stats request failed: {e}")
            raise

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get system health summary.

        Returns:
            Overall health status and component statuses
        """
        try:
            response = await self.client.get("/api/v1/health/summary")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Health summary request failed: {e}")
            raise

    async def get_health_containers(self) -> Dict[str, Any]:
        """
        Get container health status.

        Returns:
            Health status of all Docker containers
        """
        try:
            response = await self.client.get("/api/v1/health/containers")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Container health request failed: {e}")
            raise

    async def list_dashboards(self) -> Dict[str, Any]:
        """
        List all available dashboards.

        Returns:
            List of dashboard definitions
        """
        try:
            response = await self.client.get("/api/v1/dashboards")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"List dashboards request failed: {e}")
            raise

    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """
        Get data for a specific dashboard.

        Args:
            dashboard_id: Dashboard identifier

        Returns:
            Dashboard data with all widgets
        """
        try:
            response = await self.client.get(f"/api/v1/dashboards/{dashboard_id}/data")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Dashboard data request failed: {e}")
            raise

    async def ask_intelligence(
        self,
        question: str,
        depth: str = "brief",
    ) -> Dict[str, Any]:
        """
        Ask an intelligence question via RAG.

        Uses RAG (Retrieval-Augmented Generation) to search relevant articles,
        aggregate intelligence context, and generate an answer using LLM.

        Args:
            question: Natural language question (5-500 chars)
            depth: "brief" (2-3 sentences) or "detailed" (full analysis)

        Returns:
            Answer with sources and metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"question": question, "depth": depth}
            response = await self.client.get(
                "/api/v1/intelligence/ask",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Ask intelligence request failed: {e}")
            raise

    async def get_intelligence_context(
        self,
        question: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        entity: Optional[str] = None,
        sector: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get intelligence context data for Claude interpretation.

        Returns raw, structured data without LLM interpretation.
        Claude Desktop can analyze this data directly.

        Args:
            question: Natural language question (used for semantic search)
            limit: Maximum articles to return (1-50, default: 10)
            min_similarity: Minimum similarity threshold (0.0-1.0, default: 0.5)
            entity: Filter by specific entity name (optional)
            sector: Filter by sector (optional)
            days: Time window in days (1-90, default: 7)

        Returns:
            Structured context with articles, intelligence summary, pagination info

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {
                "question": question,
                "limit": limit,
                "min_similarity": min_similarity,
                "days": days,
            }
            if entity:
                params["entity"] = entity
            if sector:
                params["sector"] = sector

            response = await self.client.get(
                "/api/v1/intelligence/context",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get intelligence context request failed: {e}")
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_short,  # Short cache for sentiment data
        key_prefix="analytics:entity_sentiment"
    )
    async def get_entity_sentiment_history(
        self,
        entity: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get sentiment timeseries for an entity.

        Circuit breaker protection: Fails fast during service outages.
        Cached for short period (sentiment data changes frequently).

        Args:
            entity: Entity name to search for
            days: Number of days to look back (default: 30)

        Returns:
            Daily sentiment aggregations with article counts

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"entity": entity, "days": days}
            response = await self.client.get(
                "/api/v1/intelligence/entity-sentiment-history",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for analytics-service: {e}")
            raise HTTPCircuitBreakerError(
                service="analytics-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Entity sentiment history request failed: {e}")
            raise
