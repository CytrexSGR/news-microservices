"""
Pathfinding Data Models

Pydantic models for graph pathfinding operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PathNode(BaseModel):
    """Node in a graph path."""

    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (PERSON, ORGANIZATION, etc.)")


class PathRelationship(BaseModel):
    """Relationship in a graph path."""

    type: str = Field(..., description="Relationship type (WORKS_FOR, LOCATED_IN, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Relationship confidence score")
    evidence: Optional[str] = Field(None, description="Evidence supporting this relationship")


class PathResult(BaseModel):
    """Single path result between two entities."""

    length: int = Field(..., description="Path length (number of hops)")
    nodes: List[PathNode] = Field(..., description="Ordered list of nodes in path")
    relationships: List[PathRelationship] = Field(..., description="Ordered list of relationships in path")


class PathfindingResponse(BaseModel):
    """Complete pathfinding response."""

    paths: List[PathResult] = Field(..., description="List of found paths")
    shortest_path_length: int = Field(..., description="Length of shortest path found")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    entity1: str = Field(..., description="Source entity name")
    entity2: str = Field(..., description="Target entity name")
    max_depth: int = Field(..., description="Maximum path depth searched")
    total_paths_found: int = Field(..., description="Total number of paths found")
