"""
Pydantic schemas for Narrative Service API
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class NarrativeFrameCreate(BaseModel):
    """Schema for creating a narrative frame"""
    event_id: str
    frame_type: str
    confidence: float
    text_excerpt: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    frame_metadata: Optional[Dict[str, Any]] = None


class NarrativeFrameResponse(BaseModel):
    """Schema for narrative frame response"""
    id: str
    event_id: str
    frame_type: str
    confidence: float
    text_excerpt: Optional[str]
    entities: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
        }

    @field_validator('id', 'event_id', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class BiasAnalysisResponse(BaseModel):
    """Schema for bias analysis response"""
    id: str
    event_id: str
    source: Optional[str]
    bias_score: float = Field(..., ge=-1, le=1)
    bias_label: str
    sentiment: float = Field(..., ge=-1, le=1)
    language_indicators: Optional[Dict[str, Any]]
    perspective: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
        }

    @field_validator('id', 'event_id', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class NarrativeClusterResponse(BaseModel):
    """Schema for narrative cluster response"""
    id: str
    name: str
    dominant_frame: str
    frame_count: int
    bias_score: Optional[float]
    keywords: List[str]
    entities: Optional[Dict[str, Any]]
    sentiment: Optional[float]
    perspectives: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
        }

    @field_validator('id', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class NarrativeOverviewResponse(BaseModel):
    """Schema for narrative overview endpoint"""
    total_frames: int
    total_clusters: int
    frame_distribution: Dict[str, int]  # frame_type -> count
    bias_distribution: Dict[str, int]  # bias_label -> count
    avg_bias_score: float
    avg_sentiment: float
    top_narratives: List[NarrativeClusterResponse]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FramesListResponse(BaseModel):
    """Schema for frames list endpoint"""
    frames: List[NarrativeFrameResponse]
    total: int
    page: int
    per_page: int


class BiasComparisonResponse(BaseModel):
    """Schema for bias comparison endpoint"""
    source_count: int
    spectrum_distribution: Dict[str, int]  # left, center-left, center, center-right, right
    avg_bias_score: float
    avg_sentiment: float
    sources: List[BiasAnalysisResponse]
