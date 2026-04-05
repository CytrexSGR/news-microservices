"""
Neo4j Connection Service

Manages Neo4j driver, connection pooling, and basic query execution.

Post-Incident #18: Includes Cypher syntax validation to prevent
retry storms from malformed queries.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.cypher_validator import validate_cypher_syntax, CypherSyntaxError

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j database connection and query service."""

    def __init__(self):
        """Initialize Neo4j service (driver created on startup)."""
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """
        Establish connection to Neo4j database.

        Called during application startup.
        """
        try:
            logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=settings.NEO4J_MAX_POOL_SIZE,
                connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT
            )

            # Verify connectivity
            await self.driver.verify_connectivity()

            logger.info("✓ Neo4j connection established")

            # Create indexes for performance
            await self._create_indexes()

        except Exception as e:
            logger.error(f"✗ Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self):
        """
        Close Neo4j driver connection.

        Called during application shutdown.
        """
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (default: settings.NEO4J_DATABASE)

        Returns:
            List of result records as dictionaries

        Example:
            results = await neo4j.execute_query(
                "MATCH (n:Person {name: $name}) RETURN n",
                parameters={"name": "Alice"}
            )
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        db = database or settings.NEO4J_DATABASE
        params = parameters or {}

        async with self.driver.session(database=db) as session:
            result = await session.run(query, params)
            records = await result.data()
            return records

    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a write transaction (CREATE, MERGE, DELETE, etc.).

        Post-Incident #18: Validates Cypher syntax BEFORE execution to prevent
        retry storms from malformed queries.

        Args:
            query: Cypher write query
            parameters: Query parameters
            database: Database name (default: settings.NEO4J_DATABASE)
            timeout_seconds: Query timeout (default: settings.MAX_QUERY_TIMEOUT_SECONDS)
            skip_validation: Skip Cypher syntax validation (use for index creation)

        Returns:
            Transaction summary

        Raises:
            CypherSyntaxError: If query fails syntax validation (non-retriable)
            asyncio.TimeoutError: If query exceeds timeout
            RuntimeError: If driver not initialized
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        # P1: Validate Cypher syntax BEFORE execution (Incident #18 prevention)
        if not skip_validation:
            validate_cypher_syntax(query, raise_on_error=True)

        db = database or settings.NEO4J_DATABASE
        params = parameters or {}
        timeout = timeout_seconds or settings.MAX_QUERY_TIMEOUT_SECONDS

        async def _run_query():
            async with self.driver.session(database=db) as session:
                result = await session.run(query, params)
                summary = await result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set
                }

        # P2: Execute with timeout to prevent long-running queries
        try:
            return await asyncio.wait_for(_run_query(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(
                f"Query timeout after {timeout}s",
                extra={"query_preview": query[:200] if len(query) > 200 else query}
            )
            raise

    async def _create_indexes(self):
        """
        Create indexes for entity names, relationship types, and narrative frames.

        Indexes improve query performance significantly.
        """
        try:
            logger.info("Creating Neo4j indexes...")

            # Create index on entity names (for fast entity lookups)
            # skip_validation=True because DDL queries don't use MERGE pattern
            await self.execute_write("""
                CREATE INDEX entity_name_index IF NOT EXISTS
                FOR (e:Entity)
                ON (e.name)
            """, skip_validation=True)

            # Create constraint for unique entity names per type
            # NOTE: This is kept for backwards compatibility with entities without wikidata_id
            await self.execute_write("""
                CREATE CONSTRAINT entity_unique IF NOT EXISTS
                FOR (e:Entity)
                REQUIRE (e.name, e.type) IS UNIQUE
            """, skip_validation=True)

            # === Entity Canonicalization Indexes (2025-12-28) ===
            # Index on wikidata_id for canonical entity merging
            # This is critical for the MERGE by wikidata_id strategy
            await self.execute_write("""
                CREATE INDEX entity_wikidata_id_index IF NOT EXISTS
                FOR (e:Entity)
                ON (e.wikidata_id)
            """, skip_validation=True)

            # Unique constraint on wikidata_id (only for non-null values)
            # This ensures no duplicate wikidata_ids in the graph
            try:
                await self.execute_write("""
                    CREATE CONSTRAINT entity_wikidata_unique IF NOT EXISTS
                    FOR (e:Entity)
                    REQUIRE e.wikidata_id IS UNIQUE
                """, skip_validation=True)
            except Exception as e:
                # Constraint may fail if duplicates exist - will be fixed by migration
                logger.warning(f"wikidata_id unique constraint not created (duplicates exist): {e}")

            # === NarrativeFrame Schema ===
            # Index on NarrativeFrame by article_id for efficient lookups
            await self.execute_write("""
                CREATE INDEX narrative_frame_article_index IF NOT EXISTS
                FOR (nf:NarrativeFrame)
                ON (nf.article_id)
            """, skip_validation=True)

            # Index on NarrativeFrame by frame_type for filtering
            await self.execute_write("""
                CREATE INDEX narrative_frame_type_index IF NOT EXISTS
                FOR (nf:NarrativeFrame)
                ON (nf.frame_type)
            """, skip_validation=True)

            # Composite index for article_id + frame_type queries
            await self.execute_write("""
                CREATE INDEX narrative_frame_composite_index IF NOT EXISTS
                FOR (nf:NarrativeFrame)
                ON (nf.article_id, nf.frame_type)
            """, skip_validation=True)

            # Index on NarrativeFrame created_at for time-based queries
            await self.execute_write("""
                CREATE INDEX narrative_frame_created_index IF NOT EXISTS
                FOR (nf:NarrativeFrame)
                ON (nf.created_at)
            """, skip_validation=True)

            logger.info("✓ Neo4j indexes created (including NarrativeFrame)")

        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")

    async def health_check(self) -> bool:
        """
        Check if Neo4j connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self.driver:
                return False

            # Simple query to test connection
            result = await self.execute_query("RETURN 1 AS test")
            return len(result) > 0 and result[0].get("test") == 1

        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False


# Global Neo4j service instance
neo4j_service = Neo4jService()
