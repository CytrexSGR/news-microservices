"""HTTP client for knowledge-graph-service with circuit breaker protection."""

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

logger = logging.getLogger(__name__)


class KnowledgeGraphClient:
    """Client for knowledge-graph-service (Port 8111) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.knowledge_graph_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="knowledge-graph-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    # ==================== Entity Operations ====================

    async def get_entity_connections(
        self,
        entity_name: str,
        relationship_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get all connections for an entity.

        Args:
            entity_name: Name of the entity
            relationship_type: Filter by relationship type (optional)
            limit: Maximum number of connections to return

        Returns:
            Entity connections with relationship types and weights

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if relationship_type:
                params["relationship_type"] = relationship_type

            response = await self.client.get(
                f"/api/v1/graph/entity/{entity_name}/connections",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get entity connections failed for {entity_name}: {e}")
            raise

    async def find_entity_path(
        self,
        entity1: str,
        entity2: str,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Find paths between two entities.

        Args:
            entity1: Starting entity
            entity2: Target entity
            max_depth: Maximum path depth

        Returns:
            Paths with relationships and intermediary nodes

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"max_depth": max_depth}
            response = await self.client.get(
                f"/api/v1/graph/path/{entity1}/{entity2}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Find path failed from {entity1} to {entity2}: {e}")
            raise

    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search entities by name or properties.

        Args:
            query: Search query
            entity_type: Filter by entity type (optional)
            limit: Maximum results

        Returns:
            Matching entities with scores

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"query": query, "limit": limit}
            if entity_type:
                params["entity_type"] = entity_type

            response = await self.client.get("/api/v1/graph/search", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Search entities failed for query '{query}': {e}")
            raise

    # ==================== Analytics Operations ====================

    async def get_top_entities(
        self,
        limit: int = 10,
        metric: str = "connections",
    ) -> Dict[str, Any]:
        """
        Get top entities by connections or mentions.

        Args:
            limit: Number of top entities
            metric: Ranking metric (connections, mentions, importance)

        Returns:
            Top entities with metrics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit, "metric": metric}
            response = await self.client.get("/api/v1/graph/analytics/top-entities", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get top entities failed: {e}")
            raise

    async def get_relationship_stats(self) -> Dict[str, Any]:
        """
        Get relationship type statistics.

        Returns:
            Relationship counts and distribution

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/analytics/relationship-stats")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get relationship stats failed: {e}")
            raise

    async def get_growth_history(
        self,
        period: str = "7d",
    ) -> Dict[str, Any]:
        """
        Get graph growth history over time.

        Args:
            period: Time period (1d, 7d, 30d, 90d)

        Returns:
            Time series of entity and relationship growth

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"period": period}
            response = await self.client.get("/api/v1/graph/analytics/growth-history", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get growth history failed: {e}")
            raise

    async def get_cross_article_coverage(self) -> Dict[str, Any]:
        """
        Get entity coverage across articles.

        Returns:
            Entity appearance statistics across articles

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/analytics/cross-article-coverage")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get cross-article coverage failed: {e}")
            raise

    # ==================== Article Operations ====================

    async def get_article_entities(
        self,
        article_id: int,
    ) -> Dict[str, Any]:
        """
        Get all entities extracted from an article.

        Args:
            article_id: Article identifier

        Returns:
            Entities with types and relationships

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/graph/articles/{article_id}/entities")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get article entities failed for article {article_id}: {e}")
            raise

    async def get_article_info(
        self,
        article_id: int,
    ) -> Dict[str, Any]:
        """
        Get article node information from graph.

        Args:
            article_id: Article identifier

        Returns:
            Article node with properties and relationships

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/graph/articles/{article_id}/info")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get article info failed for article {article_id}: {e}")
            raise

    # ==================== Market Operations ====================

    async def query_markets(
        self,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Query market nodes with filters.

        Args:
            symbol: Filter by symbol (optional)
            exchange: Filter by exchange (optional)
            limit: Maximum results

        Returns:
            Market nodes matching filters

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if symbol:
                params["symbol"] = symbol
            if exchange:
                params["exchange"] = exchange

            response = await self.client.get("/api/v1/graph/markets", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Query markets failed: {e}")
            raise

    async def get_market_details(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """
        Get market details with entity relationships.

        Args:
            symbol: Trading symbol (e.g., "BTCUSD")

        Returns:
            Market node with connected entities

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/graph/markets/{symbol}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get market details failed for {symbol}: {e}")
            raise

    async def get_market_history(
        self,
        symbol: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get historical market price data.

        Args:
            symbol: Trading symbol
            days: Number of days of history

        Returns:
            Historical price data from Neo4j

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"days": days}
            response = await self.client.get(f"/api/v1/graph/markets/{symbol}/history", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get market history failed for {symbol}: {e}")
            raise

    async def get_market_stats(self) -> Dict[str, Any]:
        """
        Get market statistics overview.

        Returns:
            Market node counts, connections, etc.

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/markets/stats")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get market stats failed: {e}")
            raise

    # ==================== Quality Operations ====================

    async def get_quality_integrity(self) -> Dict[str, Any]:
        """
        Get graph integrity check results.

        Returns:
            Integrity issues, orphaned nodes, broken relationships

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/quality/integrity")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get integrity check failed: {e}")
            raise

    async def get_quality_disambiguation(self) -> Dict[str, Any]:
        """
        Get entity disambiguation quality metrics.

        Returns:
            Disambiguation statistics and ambiguous entities

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/quality/disambiguation")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get disambiguation quality failed: {e}")
            raise

    # ==================== Statistics Operations ====================

    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get basic graph statistics.

        Returns:
            Entity count, relationship count, basic metrics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/stats")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get graph stats failed: {e}")
            raise

    async def get_detailed_stats(self) -> Dict[str, Any]:
        """
        Get detailed graph statistics.

        Returns:
            Comprehensive statistics including entity types, relationship distributions

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/stats/detailed")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get detailed stats failed: {e}")
            raise

    # ==================== Narrative Analysis Operations ====================

    async def get_narrative_frames(
        self,
        entity_name: str,
        frame_type: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get narrative frames associated with an entity.

        Args:
            entity_name: Name of the entity to query
            frame_type: Optional filter (conflict, responsibility, etc.)
            min_confidence: Minimum confidence score (0.0-1.0)
            limit: Maximum number of frames to return

        Returns:
            List of narrative frames with metadata

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_confidence": min_confidence, "limit": limit}
            if frame_type:
                params["frame_type"] = frame_type

            response = await self.client.get(
                f"/api/v1/graph/narratives/frames/{entity_name}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get narrative frames failed for {entity_name}: {e}")
            raise

    async def get_frame_distribution(
        self,
        min_count: int = 10,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of narrative frame types.

        Args:
            min_count: Minimum frame count to include
            limit: Maximum frame types to return

        Returns:
            Frame type distribution with statistics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_count": min_count, "limit": limit}
            response = await self.client.get(
                "/api/v1/graph/narratives/distribution",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get frame distribution failed: {e}")
            raise

    async def get_entity_framing_analysis(
        self,
        entity_name: str,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get comprehensive framing analysis for an entity.

        Args:
            entity_name: Name of the entity to analyze
            min_confidence: Minimum confidence threshold
            limit: Maximum frames to analyze

        Returns:
            Entity framing with frame breakdown and statistics

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_confidence": min_confidence, "limit": limit}
            response = await self.client.get(
                f"/api/v1/graph/narratives/entity-framing/{entity_name}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get entity framing analysis failed for {entity_name}: {e}")
            raise

    async def get_narrative_cooccurrence(
        self,
        entity_name: Optional[str] = None,
        frame_type: Optional[str] = None,
        min_shared: int = 3,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Find entities that appear together in narratives.

        Args:
            entity_name: Optional - only find pairs including this entity
            frame_type: Optional - only consider this frame type
            min_shared: Minimum number of shared frames
            limit: Maximum pairs to return

        Returns:
            Entity pairs with shared frame details

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_shared": min_shared, "limit": limit}
            if entity_name:
                params["entity_name"] = entity_name
            if frame_type:
                params["frame_type"] = frame_type

            response = await self.client.get(
                "/api/v1/graph/narratives/cooccurrence",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get narrative cooccurrence failed: {e}")
            raise

    async def get_high_tension_narratives(
        self,
        min_tension: float = 0.7,
        frame_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Find narratives with high emotional tension.

        Args:
            min_tension: Minimum tension score (0.0-1.0)
            frame_type: Optional frame type filter
            limit: Maximum narratives to return

        Returns:
            High tension narratives with details

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_tension": min_tension, "limit": limit}
            if frame_type:
                params["frame_type"] = frame_type

            response = await self.client.get(
                "/api/v1/graph/narratives/high-tension",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get high tension narratives failed: {e}")
            raise

    async def get_narrative_stats(self) -> Dict[str, Any]:
        """
        Get overall narrative analysis statistics.

        Returns:
            Total frames, entity counts, frame type breakdown

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/graph/narratives/stats")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get narrative stats failed: {e}")
            raise

    async def get_top_narrative_entities(
        self,
        frame_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get entities with most narrative frame mentions.

        Args:
            frame_type: Optional frame type filter
            limit: Maximum entities to return

        Returns:
            Top entities with mention counts and frame breakdown

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if frame_type:
                params["frame_type"] = frame_type

            response = await self.client.get(
                "/api/v1/graph/narratives/top-entities",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for knowledge-graph-service: {e}")
            raise HTTPCircuitBreakerError(
                service="knowledge-graph-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get top narrative entities failed: {e}")
            raise
