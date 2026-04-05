"""
Query Service

Executes custom Cypher queries with timeout and safety features.
"""

import logging
import time
import hashlib
from typing import Dict, Any, List, Optional
import asyncio
from fastapi import HTTPException

from app.services.neo4j_service import neo4j_service
from app.services.query_validator import query_validator

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service for executing custom Cypher queries.

    Features:
    - Query validation (read-only enforcement)
    - Timeout protection (configurable, default 10s)
    - Query hashing (for caching/logging)
    - Result size limiting
    """

    DEFAULT_TIMEOUT_SECONDS = 10
    MAX_TIMEOUT_SECONDS = 30
    DEFAULT_LIMIT = 100
    MAX_LIMIT = 1000

    async def execute_cypher_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Execute a custom Cypher query with safety features.

        Args:
            query: Cypher query string
            parameters: Query parameters
            limit: Maximum number of results
            timeout_seconds: Query timeout in seconds

        Returns:
            Dict containing:
                - results: List of result records
                - total_results: Number of results returned
                - query_time_ms: Execution time in milliseconds
                - query_hash: SHA256 hash of the query

        Raises:
            HTTPException: On validation failure, timeout, or execution error
        """
        start_time = time.time()

        # 1. Validate query
        query_validator.validate(query)

        # 2. Generate query hash (for logging/caching)
        query_hash = self._hash_query(query, parameters)

        # 3. Enforce timeout
        if timeout_seconds > self.MAX_TIMEOUT_SECONDS:
            timeout_seconds = self.MAX_TIMEOUT_SECONDS
            logger.warning(
                f"Timeout reduced to maximum: {self.MAX_TIMEOUT_SECONDS}s"
            )

        # 4. Add LIMIT clause if not present
        if 'LIMIT' not in query.upper():
            query = f"{query}\nLIMIT {limit}"
            logger.info(f"Added LIMIT {limit} to query")

        # 5. Execute with timeout
        try:
            logger.info(
                f"Executing admin query (hash: {query_hash[:8]}..., "
                f"timeout: {timeout_seconds}s)"
            )

            # Execute query with timeout
            results = await asyncio.wait_for(
                neo4j_service.execute_query(query, parameters=parameters),
                timeout=timeout_seconds
            )

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Query completed (hash: {query_hash[:8]}..., "
                f"results: {len(results)}, time: {query_time_ms}ms)"
            )

            return {
                "results": results,
                "total_results": len(results),
                "query_time_ms": query_time_ms,
                "query_hash": query_hash
            }

        except asyncio.TimeoutError:
            query_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Query timeout after {timeout_seconds}s"
            logger.error(
                f"{error_msg} (hash: {query_hash[:8]}..., "
                f"time: {query_time_ms}ms)"
            )
            raise HTTPException(
                status_code=408,
                detail=error_msg
            )

        except Exception as e:
            query_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Query execution failed (hash: {query_hash[:8]}..., "
                f"time: {query_time_ms}ms): {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Query execution failed: {str(e)}"
            )

    def _hash_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SHA256 hash of query for logging/caching.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            SHA256 hash as hex string
        """
        # Normalize query (remove extra whitespace)
        normalized_query = ' '.join(query.split())

        # Include parameters in hash
        params_str = str(sorted(parameters.items())) if parameters else ""

        # Generate hash
        hash_input = f"{normalized_query}|{params_str}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()

    async def get_query_metadata(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get metadata about a query without executing it.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Dict containing query metadata
        """
        # Validate query
        is_valid, error_msg = True, ""
        try:
            query_validator.validate(query)
        except HTTPException as e:
            is_valid = False
            error_msg = e.detail

        return {
            "query_hash": self._hash_query(query, parameters),
            "query_length": len(query),
            "is_valid": is_valid,
            "validation_error": error_msg if not is_valid else None,
            "has_limit": 'LIMIT' in query.upper(),
            "parameter_count": len(parameters) if parameters else 0
        }


# Global query service instance
query_service = QueryService()
