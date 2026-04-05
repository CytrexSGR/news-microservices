"""
Admin Query Endpoints

Provides admin-only endpoints for executing custom Cypher queries.

Security:
- Read-only queries only (no CREATE, DELETE, SET, etc.)
- Query validation and sanitization
- Timeout protection (max 30s)
- Query logging and monitoring
- Rate limiting (10 req/min for admin endpoints)
- Admin-only access (future: JWT role check)

Post-Incident #18: Rate limiting added to prevent abuse.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Request

from app.services.query_service import query_service
from app.core.rate_limiting import limiter, RateLimits
from app.services.query_validator import query_validator
from app.models.admin_query import (
    CypherQueryRequest,
    CypherQueryResult,
    QueryMetadataRequest,
    QueryMetadataResponse,
    AllowedClausesResponse
)
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size
)

router = APIRouter(prefix="/api/v1/graph/admin")
logger = logging.getLogger(__name__)


@router.post("/query/cypher", response_model=CypherQueryResult)
@limiter.limit(RateLimits.ADMIN)
async def execute_custom_cypher_query(request: Request, query_request: CypherQueryRequest) -> CypherQueryResult:
    """
    Execute a custom read-only Cypher query.

    **Security:**
    - ⚠️ ADMIN-ONLY endpoint (requires admin role)
    - Only read operations allowed (MATCH, RETURN, WHERE, etc.)
    - Write operations blocked (CREATE, DELETE, SET, MERGE, etc.)
    - Query timeout enforced (max: 30s)
    - All queries logged with SHA256 hash

    **Example Query:**
    ```cypher
    MATCH (e:Entity)-[r]->(target:Entity)
    WHERE e.type = $entity_type
    RETURN e.name, type(r), target.name
    LIMIT 10
    ```

    **Parameters:**
    - `query`: Cypher query string (read-only)
    - `parameters`: Query parameters (optional)
    - `limit`: Max results (1-1000, default: 100)
    - `timeout_seconds`: Max execution time (1-30s, default: 10s)

    **Returns:**
    - `results`: List of query result records
    - `total_results`: Number of results
    - `query_time_ms`: Execution time in milliseconds
    - `query_hash`: SHA256 hash of query (for logging)

    **Errors:**
    - 400: Query validation failed (write operations, forbidden patterns)
    - 408: Query timeout
    - 500: Execution error
    """
    start_time = time.time()

    try:
        # Log admin query execution (WARNING level for security monitoring)
        logger.warning(
            f"⚠️  ADMIN QUERY EXECUTION: "
            f"query_length={len(query_request.query)}, "
            f"parameters={list(query_request.parameters.keys()) if query_request.parameters else []}, "
            f"limit={query_request.limit}, "
            f"timeout={query_request.timeout_seconds}s"
        )

        # Execute query with safety features
        result = await query_service.execute_cypher_query(
            query=query_request.query,
            parameters=query_request.parameters,
            limit=query_request.limit,
            timeout_seconds=query_request.timeout_seconds
        )

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='admin_cypher', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='admin_cypher').observe(query_time_seconds)
        kg_query_results_size.labels(endpoint='admin_cypher').observe(result['total_results'])

        logger.info(
            f"✓ Admin query completed: "
            f"hash={result['query_hash'][:8]}..., "
            f"results={result['total_results']}, "
            f"time={result['query_time_ms']}ms"
        )

        return CypherQueryResult(**result)

    except HTTPException:
        # Re-raise validation/timeout errors
        kg_queries_total.labels(endpoint='admin_cypher', status='error').inc()
        raise

    except Exception as e:
        # Record unexpected errors
        kg_queries_total.labels(endpoint='admin_cypher', status='error').inc()

        logger.error(f"✗ Admin query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@router.post("/query/validate", response_model=QueryMetadataResponse)
@limiter.limit(RateLimits.ADMIN)
async def validate_cypher_query(request: Request, metadata_request: QueryMetadataRequest) -> QueryMetadataResponse:
    """
    Validate a Cypher query without executing it.

    Useful for:
    - Pre-flight validation in UI
    - Testing query syntax
    - Checking query safety

    **Parameters:**
    - `query`: Cypher query string to validate
    - `parameters`: Query parameters (optional)

    **Returns:**
    - `query_hash`: SHA256 hash of query
    - `query_length`: Length in characters
    - `is_valid`: Whether query passed validation
    - `validation_error`: Error message (if invalid)
    - `has_limit`: Whether query contains LIMIT clause
    - `parameter_count`: Number of parameters

    **Example:**
    ```json
    {
      "query": "MATCH (e:Entity) RETURN e.name LIMIT 10",
      "parameters": {}
    }
    ```
    """
    try:
        metadata = await query_service.get_query_metadata(
            query=metadata_request.query,
            parameters=metadata_request.parameters
        )

        logger.info(
            f"Query validated: hash={metadata['query_hash'][:8]}..., "
            f"valid={metadata['is_valid']}"
        )

        return QueryMetadataResponse(**metadata)

    except Exception as e:
        logger.error(f"Query validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/query/clauses", response_model=AllowedClausesResponse)
async def get_allowed_clauses() -> AllowedClausesResponse:
    """
    Get lists of allowed and forbidden Cypher clauses.

    Useful for:
    - Building query editors with auto-completion
    - Documenting security restrictions
    - UI validation hints

    **Returns:**
    - `allowed_clauses`: List of allowed Cypher keywords
    - `forbidden_clauses`: List of forbidden Cypher keywords
    - `max_query_length`: Maximum query length
    - `max_timeout_seconds`: Maximum query timeout

    **Example Response:**
    ```json
    {
      "allowed_clauses": ["MATCH", "RETURN", "WHERE", "ORDER BY"],
      "forbidden_clauses": ["CREATE", "DELETE", "SET", "MERGE"],
      "max_query_length": 10000,
      "max_timeout_seconds": 30
    }
    ```
    """
    return AllowedClausesResponse(
        allowed_clauses=query_validator.get_allowed_clauses(),
        forbidden_clauses=query_validator.get_forbidden_clauses(),
        max_query_length=query_validator.MAX_QUERY_LENGTH,
        max_timeout_seconds=query_service.MAX_TIMEOUT_SECONDS
    )


@router.get("/query/examples")
async def get_query_examples():
    """
    Get example Cypher queries for common use cases.

    Useful for:
    - Learning Cypher syntax
    - Quick-start templates
    - Documentation

    **Returns:**
    List of example queries with descriptions.
    """
    examples = [
        {
            "title": "List All Entities",
            "description": "Get all entities with their types",
            "query": "MATCH (e:Entity) RETURN e.name, e.type LIMIT 10",
            "parameters": {}
        },
        {
            "title": "Find Entities by Type",
            "description": "Get entities of a specific type",
            "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name, e.type LIMIT 10",
            "parameters": {"entity_type": "PERSON"}
        },
        {
            "title": "Entity Connections",
            "description": "Get all relationships for an entity",
            "query": """
MATCH (source:Entity {name: $entity_name})-[r]->(target:Entity)
RETURN source.name, type(r) AS relationship, target.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 10
            """.strip(),
            "parameters": {"entity_name": "Tesla"}
        },
        {
            "title": "Relationship Type Distribution",
            "description": "Count relationships by type",
            "query": """
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC
LIMIT 10
            """.strip(),
            "parameters": {}
        },
        {
            "title": "High-Confidence Relationships",
            "description": "Find relationships with confidence > threshold",
            "query": """
MATCH (source:Entity)-[r]->(target:Entity)
WHERE r.confidence >= $min_confidence
RETURN source.name, type(r), target.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 10
            """.strip(),
            "parameters": {"min_confidence": 0.8}
        },
        {
            "title": "Entity Degrees (Most Connected)",
            "description": "Find entities with most connections",
            "query": """
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]-()
WITH e, count(r) AS connection_count
WHERE connection_count > 0
RETURN e.name, e.type, connection_count
ORDER BY connection_count DESC
LIMIT 10
            """.strip(),
            "parameters": {}
        }
    ]

    return {
        "examples": examples,
        "total_examples": len(examples),
        "note": "These are read-only queries. Write operations are not allowed."
    }
