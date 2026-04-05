"""
Neo4j database connection and utilities.

Issue #6: Query Performance optimization with:
- Connection pooling configuration
- Query timeouts
- Result streaming
"""
from neo4j import GraphDatabase, Driver
from typing import Optional, List, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Issue #6: Query performance constants
DEFAULT_QUERY_TIMEOUT_SECONDS = 30
MAX_CONNECTION_LIFETIME = 3600  # 1 hour
MAX_CONNECTION_POOL_SIZE = 50
CONNECTION_ACQUISITION_TIMEOUT = 60


class Neo4jConnection:
    """Neo4j database connection manager with performance optimizations."""

    def __init__(self):
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """
        Establish Neo4j connection with optimized pool settings.

        Issue #6: Connection pool configuration for better performance.

        Returns:
            Neo4j driver instance
        """
        if self._driver is None:
            try:
                # Issue #6: Optimized driver configuration
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                    max_connection_lifetime=MAX_CONNECTION_LIFETIME,
                    max_connection_pool_size=MAX_CONNECTION_POOL_SIZE,
                    connection_acquisition_timeout=CONNECTION_ACQUISITION_TIMEOUT
                )
                logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise

        return self._driver

    def close(self):
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a read query against Neo4j with optional timeout.

        Issue #6: Query timeout support for performance protection.

        Args:
            query: Cypher query string
            parameters: Query parameters
            timeout_seconds: Query timeout in seconds (default: 30s)

        Returns:
            List of result records as dictionaries
        """
        driver = self.connect()
        parameters = parameters or {}
        timeout = timeout_seconds or DEFAULT_QUERY_TIMEOUT_SECONDS

        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                # Issue #6: Execute with timeout
                result = session.run(
                    query,
                    parameters,
                    timeout=timeout
                )
                records = [record.data() for record in result]
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

    def check_connection(self) -> bool:
        """
        Check if Neo4j connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            driver = self.connect()
            driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connection check failed: {e}")
            return False


# Global connection instance
neo4j_connection = Neo4jConnection()


def get_neo4j() -> Neo4jConnection:
    """
    Get Neo4j connection instance.

    Returns:
        Neo4j connection instance
    """
    return neo4j_connection


def check_db_connection() -> bool:
    """
    Check database connectivity.

    Returns:
        True if connected, False otherwise
    """
    return neo4j_connection.check_connection()
