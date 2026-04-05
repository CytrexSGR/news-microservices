"""
Graph Data Models

Pydantic models for nodes, relationships, and graph structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Entity(BaseModel):
    """Entity node in the knowledge graph."""

    name: str = Field(..., description="Entity name (unique identifier)")
    type: str = Field(..., description="Entity type (PERSON, ORGANIZATION, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional entity properties")
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class Relationship(BaseModel):
    """Relationship edge in the knowledge graph."""

    subject: str = Field(..., description="Subject entity name")
    subject_type: str = Field(..., description="Subject entity type")
    relationship_type: str = Field(..., description="Relationship type (WORKS_FOR, LOCATED_IN, etc.)")
    object: str = Field(..., description="Object entity name")
    object_type: str = Field(..., description="Object entity type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    evidence: Optional[str] = Field(None, description="Evidence text supporting this relationship")
    source_url: Optional[str] = Field(None, description="Source article URL")
    article_id: Optional[str] = Field(None, description="Source article ID")
    created_at: Optional[datetime] = None
    mention_count: int = Field(default=1, description="Number of times this relationship was mentioned")
    # Sentiment analysis fields (optional, may be added by future pipeline stages)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score (-1.0 to 1.0)")
    sentiment_category: Optional[str] = Field(None, description="Sentiment category (positive/negative/neutral)")
    sentiment_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Sentiment confidence (0.0-1.0)")


class Triplet(BaseModel):
    """
    (Subject) -[Relationship]-> (Object) triplet.

    This is the core data structure for ingesting relationships.
    """

    subject: Entity
    relationship: Relationship
    object: Entity


class GraphNode(BaseModel):
    """Graph node with connections (API response model)."""

    name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    connection_count: int = Field(default=0, description="Number of connections")


class GraphEdge(BaseModel):
    """Graph edge (API response model)."""

    source: str = Field(..., description="Source node name")
    target: str = Field(..., description="Target node name")
    relationship_type: str
    confidence: float
    mention_count: int = Field(default=1)
    evidence: Optional[str] = None


class GraphResponse(BaseModel):
    """Complete graph response with nodes and edges."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
