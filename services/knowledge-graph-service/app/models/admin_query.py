"""
Admin Query Models

Pydantic models for admin custom query endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class CypherQueryRequest(BaseModel):
    """Request model for custom Cypher query execution."""

    query: str = Field(
        ...,
        description="Cypher query string (read-only operations only)",
        min_length=1,
        max_length=10000
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Query parameters (for parameterized queries)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Query timeout in seconds (max: 30s)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name, e.type LIMIT 10",
                "parameters": {
                    "entity_type": "PERSON"
                },
                "limit": 10,
                "timeout_seconds": 10
            }
        }


class CypherQueryResult(BaseModel):
    """Response model for custom Cypher query execution."""

    results: List[Dict[str, Any]] = Field(
        ...,
        description="Query results (list of records)"
    )
    total_results: int = Field(
        ...,
        description="Number of results returned"
    )
    query_time_ms: int = Field(
        ...,
        description="Query execution time in milliseconds"
    )
    query_hash: str = Field(
        ...,
        description="SHA256 hash of query (for caching/logging)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {"e.name": "Elon Musk", "e.type": "PERSON"},
                    {"e.name": "Jeff Bezos", "e.type": "PERSON"}
                ],
                "total_results": 2,
                "query_time_ms": 45,
                "query_hash": "a3f5d2e1..."
            }
        }


class QueryMetadataRequest(BaseModel):
    """Request model for query metadata (validation without execution)."""

    query: str = Field(
        ...,
        description="Cypher query string to analyze",
        min_length=1,
        max_length=10000
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Query parameters"
    )


class QueryMetadataResponse(BaseModel):
    """Response model for query metadata."""

    query_hash: str = Field(
        ...,
        description="SHA256 hash of query"
    )
    query_length: int = Field(
        ...,
        description="Length of query in characters"
    )
    is_valid: bool = Field(
        ...,
        description="Whether query passed validation"
    )
    validation_error: Optional[str] = Field(
        None,
        description="Validation error message (if invalid)"
    )
    has_limit: bool = Field(
        ...,
        description="Whether query contains LIMIT clause"
    )
    parameter_count: int = Field(
        ...,
        description="Number of parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_hash": "a3f5d2e1b4c6f9e8...",
                "query_length": 89,
                "is_valid": True,
                "validation_error": None,
                "has_limit": True,
                "parameter_count": 1
            }
        }


class AllowedClausesResponse(BaseModel):
    """Response model for allowed/forbidden Cypher clauses."""

    allowed_clauses: List[str] = Field(
        ...,
        description="List of allowed Cypher clauses"
    )
    forbidden_clauses: List[str] = Field(
        ...,
        description="List of forbidden Cypher clauses"
    )
    max_query_length: int = Field(
        ...,
        description="Maximum query length in characters"
    )
    max_timeout_seconds: int = Field(
        ...,
        description="Maximum query timeout in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "allowed_clauses": [
                    "MATCH", "RETURN", "WHERE", "ORDER BY", "LIMIT"
                ],
                "forbidden_clauses": [
                    "CREATE", "DELETE", "SET", "MERGE", "DROP"
                ],
                "max_query_length": 10000,
                "max_timeout_seconds": 30
            }
        }
