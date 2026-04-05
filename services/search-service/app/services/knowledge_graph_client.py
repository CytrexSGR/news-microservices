"""
Knowledge Graph Client (Layer 2.2)

HTTP client for integrating with knowledge-graph-service Neo4j API.
Provides entity relationship lookups from the knowledge graph.

Usage:
    client = get_knowledge_graph_client()
    entities = await client.get_article_entities("article-uuid-123")
"""

import logging
import time
from typing import List, Optional, Dict, Any
from functools import lru_cache

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeGraphClient:
    """
    HTTP client for knowledge-graph-service.

    Provides methods to query Neo4j-backed entity relationships
    through the knowledge-graph-service REST API.
    """

    def __init__(self):
        self.base_url = settings.KNOWLEDGE_GRAPH_SERVICE_URL
        self.timeout = settings.KNOWLEDGE_GRAPH_REQUEST_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_article_entities(
        self,
        article_id: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get entities for an article from Neo4j knowledge graph.

        Args:
            article_id: Article UUID or ID
            entity_type: Filter by entity type (PERSON, ORGANIZATION, etc.)
            limit: Maximum entities to return

        Returns:
            Dict with article info and entities list
        """
        start_time = time.time()
        client = await self._get_client()

        # Build query params
        params: Dict[str, Any] = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type

        try:
            response = await client.get(
                f"/api/v1/graph/articles/{article_id}/entities",
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                logger.debug(
                    f"Knowledge graph article entities: article_id={article_id}, "
                    f"entities={data.get('total_entities', 0)}, "
                    f"time={int((time.time() - start_time) * 1000)}ms"
                )
                return data
            elif response.status_code == 404:
                logger.debug(f"Article not found in knowledge graph: {article_id}")
                return {
                    "article_id": article_id,
                    "article_title": None,
                    "article_url": None,
                    "total_entities": 0,
                    "entities": [],
                    "query_time_ms": int((time.time() - start_time) * 1000),
                }
            else:
                logger.warning(
                    f"Knowledge graph API error: status={response.status_code}, "
                    f"article_id={article_id}"
                )
                return None

        except httpx.TimeoutException:
            logger.warning(f"Knowledge graph timeout: article_id={article_id}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Knowledge graph request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Knowledge graph unexpected error: {e}")
            return None

    async def get_entity_connections(
        self,
        entity_name: str,
        relationship_type: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get connections for an entity from Neo4j knowledge graph.

        Args:
            entity_name: Entity name (e.g., "Tesla", "Elon Musk")
            relationship_type: Filter by relationship type (WORKS_FOR, MENTIONED_WITH, etc.)
            limit: Maximum connections to return

        Returns:
            Dict with nodes and edges
        """
        start_time = time.time()
        client = await self._get_client()

        # Build query params
        params: Dict[str, Any] = {"limit": limit}
        if relationship_type:
            params["relationship_type"] = relationship_type

        try:
            response = await client.get(
                f"/api/v1/graph/entity/{entity_name}/connections",
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                logger.debug(
                    f"Knowledge graph entity connections: entity={entity_name}, "
                    f"nodes={data.get('total_nodes', 0)}, edges={data.get('total_edges', 0)}, "
                    f"time={int((time.time() - start_time) * 1000)}ms"
                )
                return data
            elif response.status_code == 404:
                logger.debug(f"Entity not found in knowledge graph: {entity_name}")
                return {
                    "nodes": [],
                    "edges": [],
                    "total_nodes": 0,
                    "total_edges": 0,
                }
            else:
                logger.warning(
                    f"Knowledge graph API error: status={response.status_code}, "
                    f"entity={entity_name}"
                )
                return None

        except httpx.TimeoutException:
            logger.warning(f"Knowledge graph timeout: entity={entity_name}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Knowledge graph request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Knowledge graph unexpected error: {e}")
            return None

    async def find_entity_paths(
        self,
        entity1: str,
        entity2: str,
    ) -> Dict[str, Any]:
        """
        Find paths between two entities in the knowledge graph.

        Args:
            entity1: First entity name
            entity2: Second entity name

        Returns:
            Dict with paths between entities
        """
        start_time = time.time()
        client = await self._get_client()

        try:
            response = await client.get(
                f"/api/v1/graph/path/{entity1}/{entity2}",
            )

            if response.status_code == 200:
                data = response.json()
                logger.debug(
                    f"Knowledge graph paths: {entity1} -> {entity2}, "
                    f"paths={data.get('total_paths', 0)}, "
                    f"time={int((time.time() - start_time) * 1000)}ms"
                )
                return data
            elif response.status_code == 404:
                logger.debug(f"No paths found: {entity1} -> {entity2}")
                return {
                    "paths": [],
                    "total_paths": 0,
                    "shortest_path_length": None,
                }
            else:
                logger.warning(
                    f"Knowledge graph API error: status={response.status_code}, "
                    f"path={entity1}->{entity2}"
                )
                return None

        except httpx.TimeoutException:
            logger.warning(f"Knowledge graph timeout: path={entity1}->{entity2}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Knowledge graph request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Knowledge graph unexpected error: {e}")
            return None

    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get basic graph statistics.

        Returns:
            Dict with total nodes, relationships, entity types
        """
        client = await self._get_client()

        try:
            response = await client.get("/api/v1/graph/stats")

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Knowledge graph stats error: status={response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Knowledge graph stats error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if knowledge-graph-service is available."""
        client = await self._get_client()

        try:
            response = await client.get("/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False


# Singleton client instance
_client_instance: Optional[KnowledgeGraphClient] = None


def get_knowledge_graph_client() -> KnowledgeGraphClient:
    """Get singleton knowledge graph client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = KnowledgeGraphClient()
    return _client_instance
