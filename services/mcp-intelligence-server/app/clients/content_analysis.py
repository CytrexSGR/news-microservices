"""HTTP client for content-analysis-v3 service with circuit breaker protection."""

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

logger = logging.getLogger(__name__)


class ContentAnalysisClient:
    """Client for content-analysis-v3 service (Port 8117) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.content_analysis_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="content-analysis-v3",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def analyze_article(self, article_id: str) -> Dict[str, Any]:
        """
        Analyze article using content-analysis-v3 AI pipeline.

        Extracts entities, sentiment, topics, and narrative frames.

        Circuit breaker protection: Automatically fails fast after 5 consecutive
        failures to prevent cascading failures and wasted resources.

        Args:
            article_id: UUID of article to analyze

        Returns:
            Complete analysis result with entities, sentiment, topics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(
                f"/api/v1/analyze/{article_id}"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for content-analysis: {e}",
                extra={"article_id": article_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to analyze article {article_id}: {e}",
                extra={"article_id": article_id, "error": str(e)},
            )
            raise

    async def extract_entities(self, article_id: str) -> Dict[str, Any]:
        """
        Extract entities from analyzed article.

        Returns 14 semantic entity types (PERSON, ORG, GPE, LOC, DATE, TIME,
        MONEY, PERCENT, PRODUCT, EVENT, FACILITY, LANGUAGE, LAW, NORP).

        Circuit breaker protection: Fails fast during service outages.

        Args:
            article_id: UUID of article

        Returns:
            Entity extraction results with types and mentions

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/entities/{article_id}"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for content-analysis: {e}",
                extra={"article_id": article_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to extract entities for article {article_id}: {e}",
                extra={"article_id": article_id, "error": str(e)},
            )
            raise

    async def get_analysis_status(self, article_id: str) -> Dict[str, Any]:
        """
        Get analysis status for article.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            article_id: UUID of article

        Returns:
            Analysis status (pending, processing, completed, failed)

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/status/{article_id}"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for content-analysis: {e}",
                extra={"article_id": article_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get analysis status for article {article_id}: {e}",
                extra={"article_id": article_id, "error": str(e)},
            )
            raise
