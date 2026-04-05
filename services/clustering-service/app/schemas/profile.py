# services/clustering-service/app/schemas/profile.py
"""Pydantic schemas for Topic Profile API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    """Base fields for topic profile."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique profile identifier")
    display_name: Optional[str] = Field(None, max_length=200, description="Human-readable name")
    description_text: str = Field(..., min_length=10, description="Descriptive text to embed")
    min_similarity: float = Field(0.40, ge=0.0, le=1.0, description="Matching threshold")
    priority: int = Field(0, ge=0, description="Sort order (higher = more prominent)")


class ProfileCreate(ProfileBase):
    """Request schema for creating a profile."""

    pass


class ProfileUpdate(BaseModel):
    """Request schema for updating a profile."""

    display_name: Optional[str] = Field(None, max_length=200)
    description_text: Optional[str] = Field(None, min_length=10)
    min_similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProfileSummary(BaseModel):
    """Summary response for profile listing."""

    id: int
    name: str
    display_name: Optional[str]
    min_similarity: float
    priority: int
    is_active: bool
    has_embedding: bool = Field(description="Whether embedding has been generated")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileDetail(ProfileSummary):
    """Detailed response including description text."""

    description_text: str


class ProfileListResponse(BaseModel):
    """Response for listing profiles."""

    profiles: List[ProfileSummary]
    total: int


class ClusterMatch(BaseModel):
    """A cluster matching a profile.

    Fields are compatible with both batch_clusters (int IDs) and
    article_clusters (UUID IDs) to support the USE_ARTICLE_CLUSTERS feature flag.
    """

    # Note: id can be int (batch_clusters) or str/UUID (article_clusters)
    id: Any  # Union[int, str] - using Any for flexibility
    cluster_idx: Optional[int] = None  # Only present in batch_clusters
    label: Optional[str]
    article_count: int
    keywords: Optional[Dict[str, Any]] = None  # Only present in batch_clusters
    similarity: float = Field(description="Cosine similarity (0.0-1.0)")
    # CSAI fields from article_clusters
    csai_status: Optional[str] = None
    csai_score: Optional[float] = None


class ProfileMatchesResponse(BaseModel):
    """Response for profile cluster matches."""

    profile_name: str
    profile_display_name: Optional[str]
    min_similarity: float
    matches: List[ClusterMatch]
    total_matches: int


class AllProfileMatchesResponse(BaseModel):
    """Response for all profile matches grouped by profile."""

    profiles: Dict[str, List[ClusterMatch]]


class EmbedProfilesResponse(BaseModel):
    """Response for batch embedding operation."""

    embedded: Dict[str, bool]
    total_success: int
    total_failed: int
