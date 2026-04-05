"""HTTP client for entity-canonicalization service with circuit breaker protection."""

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


class EntityCanonClient:
    """Client for entity-canonicalization service (Port 8112) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.entity_canon_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="entity-canonicalization",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def canonicalize_entity(
        self, entity_name: str, entity_type: str
    ) -> Dict[str, Any]:
        """
        Canonicalize entity to resolve duplicates and variations.

        Uses vector similarity (SentenceTransformer) to find canonical form.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            entity_name: Entity name to canonicalize
            entity_type: Entity type (PERSON, ORG, GPE, etc.)

        Returns:
            Canonical entity with similarity score

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(
                "/api/v1/canonicalize",
                json={"entity_name": entity_name, "entity_type": entity_type},
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"entity_name": entity_name, "entity_type": entity_type, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to canonicalize entity {entity_name} ({entity_type}): {e}",
                extra={
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "error": str(e),
                },
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_long,
        key_prefix="entity_canon:clusters"
    )
    async def get_entity_clusters(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get entity clusters showing relationships.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 1 hour (stable data).

        Args:
            limit: Maximum clusters to return

        Returns:
            Entity clusters with relationship counts

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                "/api/v1/clusters", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"limit": limit, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get entity clusters: {e}",
                extra={"limit": limit, "error": str(e)},
            )
            raise

    async def batch_canonicalize_entities(
        self, entities: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Batch canonicalize multiple entities in single request.

        More efficient than individual calls for large batches.
        Circuit breaker protection: Fails fast during service outages.

        Args:
            entities: List of dicts with keys: entity_name, entity_type, language (optional)
                Example: [
                    {"entity_name": "USA", "entity_type": "LOCATION", "language": "en"},
                    {"entity_name": "Barack Obama", "entity_type": "PERSON", "language": "en"}
                ]

        Returns:
            Batch canonicalization results with success/failure per entity

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.post(
                "/api/v1/canonicalization/canonicalize/batch",
                json={"entities": entities},
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"batch_size": len(entities), "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to batch canonicalize {len(entities)} entities: {e}",
                extra={"batch_size": len(entities), "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_medium,
        key_prefix="entity_canon:stats"
    )
    async def get_canonicalization_stats(self) -> Dict[str, Any]:
        """
        Get canonicalization statistics and metrics.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 15 minutes (semi-stable data).

        Returns:
            Statistics including:
            - Total entities processed
            - Canonical entities count
            - Merge operations
            - Entity type distribution
            - Cache hit rates

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/canonicalization/stats")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get canonicalization stats: {e}",
                extra={"error": str(e)},
            )
            raise

    async def get_async_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of async batch canonicalization job.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            job_id: Job ID from async batch request

        Returns:
            Job status (pending, processing, completed, failed) with progress

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/canonicalization/jobs/{job_id}/status"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"job_id": job_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get job status for {job_id}: {e}",
                extra={"job_id": job_id, "error": str(e)},
            )
            raise

    async def get_async_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get result of completed async batch canonicalization job.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            job_id: Job ID from async batch request

        Returns:
            Canonicalization results if job completed, error if failed/pending

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails or job not completed
        """
        try:
            response = await self.client.get(
                f"/api/v1/canonicalization/jobs/{job_id}/result"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"job_id": job_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get job result for {job_id}: {e}",
                extra={"job_id": job_id, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_long,
        key_prefix="entity_canon:aliases"
    )
    async def get_entity_aliases(self, canonical_name: str) -> Dict[str, Any]:
        """
        Get all aliases/variants for a canonical entity name.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 1 hour (stable data).

        Args:
            canonical_name: Canonical entity name

        Returns:
            List of all aliases/variants that resolve to this canonical entity

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/canonicalization/aliases/{canonical_name}"
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for entity-canonicalization: {e}",
                extra={"canonical_name": canonical_name, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get aliases for {canonical_name}: {e}",
                extra={"canonical_name": canonical_name, "error": str(e)},
            )
            raise
