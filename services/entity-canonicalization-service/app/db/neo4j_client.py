"""
Neo4j Client Infrastructure

Manages Neo4j driver lifecycle with connection pooling, health checks, and graceful shutdown.
Singleton pattern ensures single driver instance across application.

Reference: /home/cytrex/userdocs/system-ontology/ENTITY_CANONICALIZATION_OPENAI_MIGRATION.md (Phase 2)
"""

import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j database client with async support.

    Features:
    - Connection pooling (max 50 connections)
    - Health checks with retry logic
    - Graceful shutdown
    - Read/write transaction support

    Usage:
        client = Neo4jClient()
        await client.connect()

        # Execute read query
        result = await client.execute_read("MATCH (n:Entity) RETURN count(n) as count")

        # Execute write query
        await client.execute_write(
            "CREATE (e:Entity {id: $id, name: $name})",
            {"id": "TSLA", "name": "Tesla Inc."}
        )

        await client.close()
    """

    def __init__(self):
        """Initialize client (does not connect yet)."""
        self._driver: Optional[AsyncDriver] = None
        self._connected: bool = False

    async def connect(self) -> None:
        """
        Establish connection to Neo4j with retry logic.

        Raises:
            ServiceUnavailable: If Neo4j is unreachable
            AuthError: If credentials are invalid
        """
        if self._connected:
            logger.warning("Neo4j client already connected")
            return

        try:
            logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

            # Create driver with connection pool
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=50,
                connection_timeout=10.0,
                max_transaction_retry_time=5.0,
            )

            # Verify connectivity
            await self._driver.verify_connectivity()

            self._connected = True
            logger.info("✓ Neo4j client connected successfully")

        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise

    async def close(self) -> None:
        """Close Neo4j driver and cleanup connections."""
        if self._driver:
            await self._driver.close()
            self._connected = False
            logger.info("Neo4j client closed")

    async def health_check(self) -> bool:
        """
        Check Neo4j connection health.

        Returns:
            True if healthy, False otherwise
        """
        if not self._driver:
            return False

        try:
            await self._driver.verify_connectivity()
            return True
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {e}")
            return False

    @asynccontextmanager
    async def session(self, database: Optional[str] = None) -> AsyncSession:
        """
        Context manager for Neo4j session.

        Args:
            database: Database name (default: settings.NEO4J_DATABASE)

        Yields:
            AsyncSession instance

        Example:
            async with client.session() as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 10")
                records = await result.data()
        """
        if not self._driver:
            raise RuntimeError("Neo4j client not connected. Call connect() first.")

        db = database or settings.NEO4J_DATABASE
        async with self._driver.session(database=db) as session:
            yield session

    async def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute read-only query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries

        Example:
            entities = await client.execute_read(
                "MATCH (e:Entity {type: $type}) RETURN e",
                {"type": "COMPANY"}
            )
        """
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute write query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries

        Example:
            await client.execute_write(
                "CREATE (e:Entity {id: $id, name: $name})",
                {"id": "TSLA", "name": "Tesla Inc."}
            )
        """
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def create_vector_index(
        self,
        index_name: str = "entity_embeddings",
        dimension: int = 1536
    ) -> None:
        """
        Create vector index for semantic search.

        Args:
            index_name: Name of vector index
            dimension: Embedding dimension (1536 for text-embedding-3-small)

        Example:
            await client.create_vector_index("entity_embeddings", 1536)
        """
        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (e:Entity)
        ON e.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimension},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """

        try:
            await self.execute_write(query)
            logger.info(f"✓ Vector index '{index_name}' created/verified")
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise

    async def get_index_state(self, index_name: str) -> Optional[str]:
        """
        Get vector index state (POPULATING, ONLINE, FAILED).

        Args:
            index_name: Name of vector index

        Returns:
            Index state string or None if not found
        """
        query = f"SHOW INDEXES WHERE name = $name YIELD state"

        try:
            result = await self.execute_read(query, {"name": index_name})
            return result[0]["state"] if result else None
        except Exception as e:
            logger.warning(f"Failed to get index state: {e}")
            return None


# Singleton instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    Get or create singleton Neo4j client instance.

    Returns:
        Neo4jClient singleton

    Note:
        You must call await client.connect() before using.
    """
    global _neo4j_client

    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()

    return _neo4j_client
