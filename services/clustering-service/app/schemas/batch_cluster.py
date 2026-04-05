# services/clustering-service/app/schemas/batch_cluster.py
"""Pydantic schemas for batch clustering API (Topic Discovery)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ----- Request Schemas -----

class TopicSearchRequest(BaseModel):
    """Request for keyword-based topic search."""
    q: str = Field(..., min_length=1, max_length=200, description="Search query (keywords)")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")


class SimilarTopicsRequest(BaseModel):
    """Request for similarity-based topic lookup."""
    embedding: List[float] = Field(..., min_length=1536, max_length=1536)
    limit: int = Field(5, ge=1, le=20)


class TopicFeedbackRequest(BaseModel):
    """Request to submit feedback for a topic cluster."""
    label: str = Field(..., min_length=1, max_length=255, description="Corrected label")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in correction")


# ----- Response Schemas -----

class TopicArticle(BaseModel):
    """Article within a topic cluster."""
    article_id: str
    title: str
    url: Optional[str] = None
    distance: Optional[float] = Field(None, description="Distance to cluster centroid")
    published_at: Optional[str] = Field(None, description="Article publication date")
    assigned_at: Optional[str] = Field(None, description="When article was assigned to cluster")


class TopicSummary(BaseModel):
    """Summary of a topic cluster for list views."""
    id: int
    label: Optional[str] = None
    keywords: Optional[List[str]] = None
    article_count: int
    label_confidence: Optional[float] = None


class TopicDetail(TopicSummary):
    """Full topic cluster details with sample articles."""
    batch_id: str
    cluster_idx: int
    created_at: Optional[datetime] = None
    sample_articles: List[TopicArticle] = []


class TopicSearchResult(BaseModel):
    """Topic matching a search query (keyword or semantic)."""
    cluster_id: int
    label: Optional[str] = None
    keywords: Optional[List[str]] = None
    article_count: int
    match_count: Optional[int] = Field(None, description="Number of articles matching search keywords (keyword mode)")
    similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cosine similarity score (semantic mode)")


class SimilarTopic(BaseModel):
    """Topic similar to a given embedding."""
    cluster_id: int
    label: Optional[str] = None
    keywords: Optional[List[str]] = None
    article_count: int
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")


class ArticleTopicInfo(BaseModel):
    """Topic information for a specific article."""
    cluster_id: int
    label: Optional[str] = None
    keywords: Optional[List[str]] = None
    article_count: int
    distance: Optional[float] = Field(None, description="Distance to cluster centroid")
    batch_id: str


class BatchInfo(BaseModel):
    """Information about a clustering batch run."""
    batch_id: str
    status: str = Field(..., pattern="^(running|completed|failed)$")
    article_count: int
    cluster_count: int
    noise_count: int
    csai_score: Optional[float] = Field(None, description="Cluster Stability Assessment Index")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ----- List Response Schemas -----

class TopicListResponse(BaseModel):
    """Paginated list of topic clusters."""
    topics: List[TopicSummary]
    total: int
    limit: int
    offset: int
    has_more: bool
    batch_id: Optional[str] = Field(None, description="Batch these topics belong to")


class TopicSearchResponse(BaseModel):
    """Response for topic search (keyword or semantic)."""
    results: List[TopicSearchResult]
    query: str
    mode: str = Field("keyword", description="Search mode: 'semantic' or 'keyword'")
    batch_id: Optional[str] = None


class SimilarTopicsResponse(BaseModel):
    """Response for similarity search."""
    topics: List[SimilarTopic]
    batch_id: Optional[str] = None


class BatchListResponse(BaseModel):
    """List of batch runs."""
    batches: List[BatchInfo]


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool
    feedback_id: int
    message: str
