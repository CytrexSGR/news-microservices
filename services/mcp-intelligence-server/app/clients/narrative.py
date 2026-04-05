"""HTTP client for narrative-service with circuit breaker protection."""

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


class NarrativeClient:
    """Client for narrative-service (Port 8119) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.narrative_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="narrative-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for narrative frames and bias.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            text: Text to analyze

        Returns:
            Narrative analysis with frames, bias scores, propaganda signals

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(
                "/api/v1/narrative/analyze/text", json={"text": text}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for narrative-service: {e}",
                extra={"text_length": len(text), "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to analyze text: {e}",
                extra={"text_length": len(text), "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="narrative:frames"
    )
    async def get_narrative_frames(
        self, limit: int = 50, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get narrative frames from article analysis.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            limit: Maximum frames to return
            category: Optional category filter

        Returns:
            Narrative frames with frequency and examples

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if category:
                params["category"] = category

            response = await self.client.get(
                "/api/v1/narrative/frames", params=params
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for narrative-service: {e}",
                extra={"limit": limit, "category": category, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get narrative frames: {e}",
                extra={"limit": limit, "category": category, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="narrative:bias"
    )
    async def get_bias_analysis(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get bias analysis with distribution and trends.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis

        Returns:
            Bias analysis with distribution, trends, and examples

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            response = await self.client.get(
                "/api/v1/narrative/bias", params=params
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for narrative-service: {e}",
                extra={"start_date": start_date, "end_date": end_date, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get bias analysis: {e}",
                extra={"start_date": start_date, "end_date": end_date, "error": str(e)},
            )
            raise

    async def get_narrative_clusters(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get narrative clusters showing related frames.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            limit: Maximum clusters to return

        Returns:
            Narrative clusters with frame relationships

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/narrative/clusters", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for narrative-service: {e}",
                extra={"limit": limit, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get narrative clusters: {e}",
                extra={"limit": limit, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="narrative:overview"
    )
    async def get_narrative_overview(self) -> Dict[str, Any]:
        """
        Get narrative overview dashboard with statistics.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes for dashboard data.

        Returns:
            Overview with top frames, bias distribution, and trends

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/narrative/overview")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for narrative-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get narrative overview: {e}",
                extra={"error": str(e)},
            )
            raise
