# services/clustering-service/app/schemas/cluster.py
"""Pydantic schemas for cluster API."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EntityRef(BaseModel):
    """Reference to an entity."""
    id: str
    name: str
    type: str


class ArticleClusterRequest(BaseModel):
    """Request to assign article to cluster."""
    article_id: UUID
    embedding: List[float] = Field(..., min_length=1)
    title: str
    published_at: Optional[datetime] = None
    entities: Optional[List[EntityRef]] = None
    simhash_fingerprint: Optional[int] = None


class ArticleClusterResponse(BaseModel):
    """Response after assigning article to cluster."""
    cluster_id: UUID
    is_new_cluster: bool
    similarity_score: float
    cluster_article_count: int


class ClusterSummary(BaseModel):
    """Summary of a cluster for list view."""
    id: UUID
    title: str
    article_count: int
    status: str
    tension_score: Optional[float] = None
    is_breaking: bool = False
    first_seen_at: datetime
    last_updated_at: datetime


class ClusterDetail(ClusterSummary):
    """Full cluster details."""
    summary: Optional[str] = None
    centroid_vector: Optional[List[float]] = None
    primary_entities: Optional[List[EntityRef]] = None
    burst_detected_at: Optional[datetime] = None


class ClusterListResponse(BaseModel):
    """Response for cluster list endpoint."""
    clusters: List[ClusterSummary]
    pagination: dict


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    limit: int
    offset: int
    has_more: bool


class ClusterArticle(BaseModel):
    """Article belonging to a cluster."""
    id: str
    title: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    source_name: Optional[str] = None
    joined_at: Optional[str] = None
    similarity_score: Optional[float] = None


class ClusterArticlesResponse(BaseModel):
    """Response for cluster articles endpoint."""
    cluster_id: UUID
    articles: List[ClusterArticle]
    pagination: PaginationMeta
