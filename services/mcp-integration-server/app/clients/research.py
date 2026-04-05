"""HTTP client for Research service (Perplexity AI integration)."""

import logging
from typing import Dict, Any, List, Optional

from ..config import settings
from .base import BaseClient, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class ResearchClient(BaseClient):
    """Client for Research service (Port 8103)."""

    def __init__(self):
        super().__init__(
            name="research-service",
            base_url=settings.research_service_url,
            timeout=60.0,  # Research queries can take longer
        )

    # =========================================================================
    # Research Queries
    # =========================================================================

    async def research(
        self,
        query: str,
        model: str = "sonar",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Execute research query using Perplexity AI.

        Args:
            query: Research question or topic
            model: Perplexity model (sonar, sonar-pro)
            max_tokens: Max response tokens
            temperature: Response temperature

        Returns:
            Research result with answer and sources
        """
        response = await self.post(
            "/api/v1/research/",
            json={
                "query": query,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )
        response.raise_for_status()
        return response.json()

    async def research_batch(
        self,
        queries: List[str],
        model: str = "sonar",
    ) -> Dict[str, Any]:
        """
        Execute batch research queries.

        Args:
            queries: List of research questions
            model: Perplexity model

        Returns:
            Batch results with task IDs
        """
        response = await self.post(
            "/api/v1/research/batch",
            json={
                "queries": queries,
                "model": model,
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_research_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get research result by task ID.

        Args:
            task_id: Research task ID

        Returns:
            Research result or status
        """
        response = await self.get(f"/api/v1/research/{task_id}")
        response.raise_for_status()
        return response.json()

    async def research_feed(
        self,
        feed_id: int,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute research query for RSS feed.

        Args:
            feed_id: Feed ID to research
            query: Optional specific query

        Returns:
            Research result for feed context
        """
        params = {}
        if query:
            params["query"] = query

        response = await self.post(
            f"/api/v1/research/feed/{feed_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_research_history(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get research query history.

        Args:
            limit: Max results
            offset: Result offset

        Returns:
            Research history
        """
        response = await self.get(
            "/api/v1/research/history",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()

    async def get_research_stats(self) -> Dict[str, Any]:
        """Get research service statistics."""
        response = await self.get("/api/v1/research/stats")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Templates
    # =========================================================================

    async def list_templates(self) -> Dict[str, Any]:
        """List available research templates."""
        response = await self.get("/api/v1/templates/")
        response.raise_for_status()
        return response.json()

    async def get_template(self, template_id: int) -> Dict[str, Any]:
        """
        Get research template details.

        Args:
            template_id: Template ID

        Returns:
            Template configuration
        """
        response = await self.get(f"/api/v1/templates/{template_id}")
        response.raise_for_status()
        return response.json()

    async def apply_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply research template with variables.

        Args:
            template_id: Template ID
            variables: Template variable values

        Returns:
            Research result from template
        """
        response = await self.post(
            f"/api/v1/templates/{template_id}/apply",
            json={"variables": variables}
        )
        response.raise_for_status()
        return response.json()

    async def preview_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Preview template with variables (without execution).

        Args:
            template_id: Template ID
            variables: Template variable values

        Returns:
            Preview of rendered template
        """
        response = await self.post(
            f"/api/v1/templates/{template_id}/preview",
            json={"variables": variables}
        )
        response.raise_for_status()
        return response.json()

    async def get_template_functions(self) -> Dict[str, Any]:
        """Get available template functions."""
        response = await self.get("/api/v1/templates/functions")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Runs
    # =========================================================================

    async def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List research runs.

        Args:
            limit: Max results
            offset: Result offset

        Returns:
            Research runs
        """
        response = await self.get(
            "/api/v1/runs/",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()

    async def get_run(self, run_id: str) -> Dict[str, Any]:
        """
        Get research run details.

        Args:
            run_id: Run ID

        Returns:
            Run details with status and results
        """
        response = await self.get(f"/api/v1/runs/{run_id}")
        response.raise_for_status()
        return response.json()

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get research run status.

        Args:
            run_id: Run ID

        Returns:
            Run status (pending, running, completed, failed)
        """
        response = await self.get(f"/api/v1/runs/{run_id}/status")
        response.raise_for_status()
        return response.json()

    async def cancel_run(self, run_id: str) -> Dict[str, Any]:
        """
        Cancel research run.

        Args:
            run_id: Run ID to cancel

        Returns:
            Cancellation result
        """
        response = await self.post(f"/api/v1/runs/{run_id}/cancel")
        response.raise_for_status()
        return response.json()

    async def run_template(
        self,
        template_id: int,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create and run research from template.

        Args:
            template_id: Template ID
            variables: Template variables

        Returns:
            Created run with run_id
        """
        json_body = {}
        if variables:
            json_body["variables"] = variables

        response = await self.post(
            f"/api/v1/runs/template/{template_id}",
            json=json_body
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Rate Limits
    # =========================================================================

    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        response = await self.get("/status/rate-limits")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Health
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check research service health."""
        response = await self.get("/health")
        response.raise_for_status()
        return response.json()
