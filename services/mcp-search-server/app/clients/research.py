"""HTTP client for research-service with circuit breaker protection."""

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


class ResearchClient:
    """Client for research-service (Port 8103) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.research_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="research-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def create_research_task(
        self,
        query: str,
        research_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create Perplexity research task.

        Circuit breaker protection: Fails fast during service outages.
        Uses Perplexity AI for comprehensive research with citations.

        Args:
            query: Research query/question
            research_type: Type of research (general, fact_check, trend_analysis,
                          feed_assessment, etc.)
            context: Additional context for research
            options: Research options (depth, sources, etc.)

        Returns:
            Task details with task_id, status, estimated completion time

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {
                "query": query,
                "research_type": research_type,
                "context": context or {},
                "options": options or {},
            }

            response = await self.client.post("/api/v1/research", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"query": query, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to create research task: {e}",
                extra={"query": query, "error": str(e)},
            )
            raise

    async def get_research_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get research task details and results.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            task_id: Task ID

        Returns:
            Task results with answer, citations, confidence, metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/research/{task_id}")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"task_id": task_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get research task: {e}",
                extra={"task_id": task_id, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_short, key_prefix="research:list")
    async def list_research_tasks(
        self,
        status: Optional[str] = None,
        research_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List research tasks with filtering.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 5 minutes.

        Args:
            status: Filter by status (pending, running, completed, failed)
            research_type: Filter by research type
            page: Page number
            page_size: Results per page

        Returns:
            List of research tasks with summary information

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"page": page, "page_size": page_size}
            if status:
                params["status"] = status
            if research_type:
                params["research_type"] = research_type

            response = await self.client.get("/api/v1/research", params=params)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"page": page, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to list research tasks: {e}",
                extra={"page": page, "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_medium, key_prefix="research:history")
    async def get_research_history(
        self,
        user_id: Optional[str] = None,
        feed_id: Optional[int] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get research task history.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 30 minutes.

        Args:
            user_id: Filter by user ID
            feed_id: Filter by feed ID
            days: Number of days of history (default: 7)

        Returns:
            Historical research data with trends and usage statistics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"days": days}
            if user_id:
                params["user_id"] = user_id
            if feed_id:
                params["feed_id"] = feed_id

            response = await self.client.get("/api/v1/research/history", params=params)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get research history: {e}", extra={"error": str(e)}
            )
            raise

    async def create_batch_research(
        self, queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple research tasks in batch.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            queries: List of research queries with type and options

        Returns:
            Batch task details with task IDs and status

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {"queries": queries}
            response = await self.client.post("/api/v1/research/batch", json=payload)
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"count": len(queries), "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to create batch research: {e}",
                extra={"count": len(queries), "error": str(e)},
            )
            raise

    @cache_manager.cached(ttl=settings.cache_ttl_long, key_prefix="research:templates")
    async def list_research_templates(
        self, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List research templates.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 1 hour (templates change slowly).

        Args:
            category: Filter by category (feed_assessment, fact_check, etc.)

        Returns:
            List of reusable research templates with parameters

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {}
            if category:
                params["category"] = category

            response = await self.client.get(
                "/api/v1/templates", params=params if params else None
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to list research templates: {e}", extra={"error": str(e)}
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_long, key_prefix="research:template_details"
    )
    async def get_research_template(self, template_id: str) -> Dict[str, Any]:
        """
        Get research template details.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 1 hour.

        Args:
            template_id: Template ID

        Returns:
            Template details with parameters, description, examples

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/templates/{template_id}")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"template_id": template_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to get research template: {e}",
                extra={"template_id": template_id, "error": str(e)},
            )
            raise

    async def apply_research_template(
        self, template_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply template to create research task.

        Circuit breaker protection: Fails fast during service outages.
        Quick research from pre-configured template.

        Args:
            template_id: Template ID
            parameters: Template parameters (feed_url, topic, etc.)

        Returns:
            Created task with task_id and status

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {"parameters": parameters}
            response = await self.client.post(
                f"/api/v1/templates/{template_id}/apply", json=payload
            )
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"template_id": template_id, "circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to apply research template: {e}",
                extra={"template_id": template_id, "error": str(e)},
            )
            raise

    @cache_manager.cached(
        ttl=settings.cache_ttl_long, key_prefix="research:functions"
    )
    async def list_research_functions(self) -> Dict[str, Any]:
        """
        List available research functions.

        Circuit breaker protection: Fails fast during service outages.
        Cached for 1 hour.

        Returns:
            List of research capabilities with descriptions and parameters

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/templates/functions")
            response.raise_for_status()
            return response.json()
        except (CircuitBreakerOpenError, HTTPCircuitBreakerError) as e:
            logger.error(
                f"Circuit breaker OPEN for research-service: {e}",
                extra={"circuit": "OPEN"},
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to list research functions: {e}", extra={"error": str(e)}
            )
            raise
