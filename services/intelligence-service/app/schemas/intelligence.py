"""
Intelligence API Response Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class ClusterSummary(BaseModel):
    """Summary of an intelligence cluster"""
    id: uuid.UUID
    name: str
    risk_score: float
    risk_delta: float
    event_count: int
    keywords: List[str]
    category: Optional[str] = None
    time_window: Optional[str] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class TopRegion(BaseModel):
    """Top region by event activity"""
    name: str
    event_count: int
    risk_score: float


class TrendingEntity(BaseModel):
    """A trending entity with mention count"""
    name: str
    type: str
    mention_count: int


class OverviewResponse(BaseModel):
    """Response for /api/v1/intelligence/overview endpoint"""
    global_risk_index: float = Field(..., description="Average risk score of top clusters (0-100)")
    top_clusters: List[ClusterSummary] = Field(..., description="Top 5 clusters by risk score")
    geo_risk: float = Field(..., description="Risk score for geopolitical category")
    finance_risk: float = Field(..., description="Risk score for financial category")
    top_regions: List[TopRegion] = Field(..., description="Top 5 regions by activity")
    trending_entities: List[TrendingEntity] = Field(default_factory=list, description="Top 10 entities by mention count (24h)")
    total_clusters: int = Field(..., description="Total number of active clusters")
    total_events: int = Field(..., description="Total number of events in last 7 days")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class TimelinePoint(BaseModel):
    """Timeline data point for cluster"""
    date: datetime
    event_count: int
    avg_sentiment: float


class ClusterDetail(BaseModel):
    """Detailed cluster information"""
    id: uuid.UUID
    name: str
    risk_score: float
    risk_delta: float
    event_count: int
    keywords: List[str]
    category: Optional[str] = None
    time_window: Optional[str] = None
    avg_sentiment: float
    unique_sources: int
    is_active: bool
    first_seen: datetime  # Changed from created_at to match DB column
    last_updated: datetime
    timeline: List[TimelinePoint] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ClustersResponse(BaseModel):
    """Response for /api/v1/intelligence/clusters endpoint"""
    clusters: List[ClusterDetail]
    total: int
    page: int
    per_page: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Event Detection Schemas
# =============================================================================

class EventDetectRequest(BaseModel):
    """Request for POST /events/detect endpoint"""
    text: str = Field(..., min_length=10, max_length=50000, description="Text to analyze for event detection")
    include_keywords: bool = Field(True, description="Include keyword extraction")
    max_keywords: int = Field(10, ge=1, le=50, description="Maximum keywords to extract")


class DetectedEntity(BaseModel):
    """A detected entity from text"""
    name: str
    type: str  # PERSON, ORGANIZATION, LOCATION
    count: int = 1


class EventDetectResponse(BaseModel):
    """Response for POST /events/detect endpoint"""
    entities: dict = Field(..., description="Extracted entities by type")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entity_count: int = Field(..., description="Total number of unique entities")
    text_length: int = Field(..., description="Input text length")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


# =============================================================================
# Risk Calculation Schemas
# =============================================================================

class RiskCalculateRequest(BaseModel):
    """Request for POST /risk/calculate endpoint"""
    cluster_id: Optional[uuid.UUID] = Field(None, description="Cluster ID to calculate risk for")
    entities: Optional[List[str]] = Field(None, description="Entity names to analyze")
    text: Optional[str] = Field(None, max_length=50000, description="Text to analyze for risk")
    include_factors: bool = Field(True, description="Include risk factor breakdown")


class RiskFactor(BaseModel):
    """Individual risk factor"""
    name: str
    value: float
    weight: float
    contribution: float


class RiskCalculateResponse(BaseModel):
    """Response for POST /risk/calculate endpoint"""
    risk_score: float = Field(..., ge=0, le=100, description="Calculated risk score (0-100)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    risk_delta: Optional[float] = Field(None, description="Change from previous calculation")
    factors: List[RiskFactor] = Field(default_factory=list, description="Risk factor breakdown")
    cluster_id: Optional[uuid.UUID] = Field(None, description="Associated cluster if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
