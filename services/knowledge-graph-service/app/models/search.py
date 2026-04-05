"""
Search Data Models

Pydantic models for entity search requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EntitySearchResult(BaseModel):
    """Entity search result with metadata and connection count."""

    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (PERSON, ORGANIZATION, etc.)")
    last_seen: Optional[datetime] = Field(None, description="Last time this entity was seen in data")
    connection_count: int = Field(default=0, description="Number of connections to other entities")
    wikidata_id: Optional[str] = Field(None, description="Wikidata identifier (if enriched)")


class EntitySearchResponse(BaseModel):
    """Complete search response with results and metadata."""

    results: List[EntitySearchResult]
    total_results: int = Field(..., description="Total number of results returned")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    query: str = Field(..., description="Original search query")
    entity_type_filter: Optional[str] = Field(None, description="Entity type filter applied")
