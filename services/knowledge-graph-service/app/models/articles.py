"""
Article-related Data Models

Pydantic models for article entities and article-specific graph queries.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ArticleEntity(BaseModel):
    """Entity extracted from an article with extraction metadata."""

    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (PERSON, ORGANIZATION, etc.)")
    wikidata_id: Optional[str] = Field(None, description="Wikidata ID if enriched")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence (0.0-1.0)")
    mention_count: int = Field(..., ge=1, description="Number of times entity mentioned in article")
    first_mention_index: Optional[int] = Field(
        None,
        description="Character index of first mention in article text"
    )


class ArticleEntitiesResponse(BaseModel):
    """Response model for article entities endpoint."""

    article_id: str = Field(..., description="Article identifier")
    article_title: Optional[str] = Field(None, description="Article title if available")
    article_url: Optional[str] = Field(None, description="Article URL if available")
    total_entities: int = Field(..., description="Total number of entities matching filters")
    entities: List[ArticleEntity] = Field(
        default_factory=list,
        description="List of entities extracted from article"
    )
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")


class ArticleNode(BaseModel):
    """Article node information from graph."""

    article_id: str
    title: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[str] = None
    entity_count: int = Field(default=0, description="Number of entities extracted from article")
