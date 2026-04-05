"""Service API Tools for NEXUS Agent.

Provides access to other microservices via HTTP API calls.
"""

import httpx
from datetime import datetime
from typing import Any, Dict, Optional

from app.tools.base import BaseTool, ToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Service registry with base URLs
SERVICE_REGISTRY = {
    "search": "http://search-service:8106",
    "analytics": "http://analytics-service:8107",
    "research": "http://research-service:8103",
    "knowledge-graph": "http://knowledge-graph-service:8111",
    "fmp": "http://fmp-service:8113",
}


class SearchServiceTool(BaseTool):
    """Search articles using the search service (Elasticsearch)."""

    name: str = "search_service"
    description: str = (
        "Perform full-text search on articles using Elasticsearch. "
        "More powerful than database search - supports fuzzy matching, "
        "relevance scoring, and advanced text search features."
    )

    def __init__(self):
        self.base_url = SERVICE_REGISTRY["search"]
        self.timeout = 30

    async def execute(
        self,
        query: str,
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        """
        Search articles via search service.

        Args:
            query: Search query string
            limit: Maximum results (default 10, max 50)
            **kwargs: Additional parameters

        Returns:
            ToolResult with search results
        """
        if not query or not query.strip():
            return ToolResult(
                success=False,
                error="Query cannot be empty",
                tool_name=self.name,
            )

        limit = min(max(1, limit), 50)

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                response = await client.get(
                    "/api/v1/search",
                    params={"q": query, "limit": limit},
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    "search_service_success",
                    query=query,
                    results_count=len(data.get("results", [])),
                )

                return ToolResult(
                    success=True,
                    data=data,
                    tool_name=self.name,
                )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "search_service_http_error",
                status_code=exc.response.status_code,
            )
            return ToolResult(
                success=False,
                error=f"Search service error: {exc.response.status_code}",
                tool_name=self.name,
            )

        except httpx.RequestError as exc:
            logger.error(
                "search_service_request_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Search service unavailable: {str(exc)}",
                tool_name=self.name,
            )


class AnalyticsServiceTool(BaseTool):
    """Get analytics and metrics from the analytics service."""

    name: str = "analytics_service"
    description: str = (
        "Get analytics metrics including article trends, sentiment distributions, "
        "top entities, and category statistics."
    )

    def __init__(self):
        self.base_url = SERVICE_REGISTRY["analytics"]
        self.timeout = 30

    async def execute(
        self,
        metric_type: str = "overview",
        days: int = 7,
        **kwargs,
    ) -> ToolResult:
        """
        Get analytics metrics.

        Args:
            metric_type: Type of metric - 'overview', 'sentiment', 'entities', 'trends'
            days: Number of days to analyze (default 7)
            **kwargs: Additional parameters

        Returns:
            ToolResult with analytics data
        """
        valid_types = ["overview", "sentiment", "entities", "trends"]
        if metric_type not in valid_types:
            metric_type = "overview"

        days = min(max(1, days), 90)

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                response = await client.get(
                    f"/api/v1/metrics/{metric_type}",
                    params={"days": days},
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    "analytics_service_success",
                    metric_type=metric_type,
                )

                return ToolResult(
                    success=True,
                    data=data,
                    tool_name=self.name,
                )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "analytics_service_http_error",
                status_code=exc.response.status_code,
            )
            return ToolResult(
                success=False,
                error=f"Analytics service error: {exc.response.status_code}",
                tool_name=self.name,
            )

        except httpx.RequestError as exc:
            logger.error(
                "analytics_service_request_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Analytics service unavailable: {str(exc)}",
                tool_name=self.name,
            )


class KnowledgeGraphTool(BaseTool):
    """Query the knowledge graph for entity relationships."""

    name: str = "knowledge_graph"
    description: str = (
        "Query the knowledge graph (Neo4j) for entity relationships. "
        "Find connections between people, organizations, events, and topics."
    )

    def __init__(self):
        self.base_url = SERVICE_REGISTRY["knowledge-graph"]
        self.timeout = 30

    async def execute(
        self,
        entity: str,
        relationship_type: Optional[str] = None,
        depth: int = 1,
        **kwargs,
    ) -> ToolResult:
        """
        Query knowledge graph for entity relationships.

        Args:
            entity: Entity name to query
            relationship_type: Optional filter by relationship type
            depth: Relationship depth (1-3, default 1)
            **kwargs: Additional parameters

        Returns:
            ToolResult with entity relationships
        """
        if not entity or not entity.strip():
            return ToolResult(
                success=False,
                error="Entity name cannot be empty",
                tool_name=self.name,
            )

        depth = min(max(1, depth), 3)

        try:
            params = {"entity": entity, "depth": depth}
            if relationship_type:
                params["type"] = relationship_type

            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                response = await client.get(
                    "/api/v1/relationships",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    "knowledge_graph_success",
                    entity=entity,
                    relationships_count=len(data.get("relationships", [])),
                )

                return ToolResult(
                    success=True,
                    data=data,
                    tool_name=self.name,
                )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "knowledge_graph_http_error",
                status_code=exc.response.status_code,
            )
            return ToolResult(
                success=False,
                error=f"Knowledge graph error: {exc.response.status_code}",
                tool_name=self.name,
            )

        except httpx.RequestError as exc:
            logger.error(
                "knowledge_graph_request_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Knowledge graph unavailable: {str(exc)}",
                tool_name=self.name,
            )


class FMPServiceTool(BaseTool):
    """Get financial market data from FMP service."""

    name: str = "fmp_service"
    description: str = (
        "Get financial market data including stock quotes, company profiles, "
        "and market news. Useful for finance-related queries."
    )

    def __init__(self):
        self.base_url = SERVICE_REGISTRY["fmp"]
        self.timeout = 30

    async def execute(
        self,
        symbol: str,
        data_type: str = "quote",
        **kwargs,
    ) -> ToolResult:
        """
        Get financial market data.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            data_type: Type of data - 'quote', 'profile', 'news'
            **kwargs: Additional parameters

        Returns:
            ToolResult with financial data
        """
        if not symbol or not symbol.strip():
            return ToolResult(
                success=False,
                error="Stock symbol cannot be empty",
                tool_name=self.name,
            )

        valid_types = ["quote", "profile", "news"]
        if data_type not in valid_types:
            data_type = "quote"

        symbol = symbol.upper().strip()

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                response = await client.get(
                    f"/api/v1/{data_type}/{symbol}",
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    "fmp_service_success",
                    symbol=symbol,
                    data_type=data_type,
                )

                return ToolResult(
                    success=True,
                    data=data,
                    tool_name=self.name,
                )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "fmp_service_http_error",
                status_code=exc.response.status_code,
            )
            return ToolResult(
                success=False,
                error=f"FMP service error: {exc.response.status_code}",
                tool_name=self.name,
            )

        except httpx.RequestError as exc:
            logger.error(
                "fmp_service_request_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"FMP service unavailable: {str(exc)}",
                tool_name=self.name,
            )


class ServiceHealthTool(BaseTool):
    """Check health status of microservices."""

    name: str = "service_health"
    description: str = (
        "Check the health status of all microservices in the system. "
        "Returns which services are up, down, or degraded."
    )

    def __init__(self):
        self.timeout = 5  # Short timeout for health checks

    async def execute(self, **kwargs) -> ToolResult:
        """
        Check health of all registered services.

        Returns:
            ToolResult with service health status
        """
        health_status = {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for service_name, base_url in SERVICE_REGISTRY.items():
                try:
                    response = await client.get(f"{base_url}/health")
                    if response.status_code == 200:
                        health_status[service_name] = {
                            "status": "healthy",
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                        }
                    else:
                        health_status[service_name] = {
                            "status": "degraded",
                            "status_code": response.status_code,
                        }
                except httpx.RequestError:
                    health_status[service_name] = {
                        "status": "unhealthy",
                        "error": "Connection failed",
                    }

        healthy_count = sum(1 for s in health_status.values() if s["status"] == "healthy")
        total_count = len(health_status)

        logger.info(
            "service_health_check",
            healthy=healthy_count,
            total=total_count,
        )

        return ToolResult(
            success=True,
            data={
                "services": health_status,
                "summary": {
                    "healthy": healthy_count,
                    "total": total_count,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            tool_name=self.name,
        )
