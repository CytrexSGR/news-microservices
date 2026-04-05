"""Security View Schemas for geo-map intelligence visualization."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class ThreatLevel(str, Enum):
    """Threat level classification based on priority score."""
    CRITICAL = "critical"  # Priority 9-10
    HIGH = "high"          # Priority 7-8
    MEDIUM = "medium"      # Priority 5-6
    LOW = "low"            # Priority 3-4


class SecurityCategory(str, Enum):
    """Security-relevant article categories."""
    CONFLICT = "CONFLICT"
    SECURITY = "SECURITY"
    HUMANITARIAN = "HUMANITARIAN"
    POLITICS = "POLITICS"


class TrendDirection(str, Enum):
    """Trend direction for threat evolution."""
    ESCALATING = "escalating"
    STABLE = "stable"
    DE_ESCALATING = "de-escalating"


# =============================================================================
# Security Event Schemas
# =============================================================================

class SecurityEvent(BaseModel):
    """Single security event/article for map visualization."""

    id: str
    article_id: UUID
    title: str
    country_code: str
    country_name: str
    lat: float
    lon: float

    # Classification
    category: str
    threat_level: ThreatLevel
    priority_score: int = Field(..., ge=0, le=10)

    # Tier1 metrics
    impact_score: Optional[float] = None
    urgency_score: Optional[float] = None

    # Tier2 geopolitical metrics
    conflict_severity: Optional[float] = None
    diplomatic_impact: Optional[float] = None
    regional_stability_risk: Optional[float] = None
    countries_involved: List[str] = []

    # Tier2 narrative metrics
    dominant_frame: Optional[str] = None
    narrative_tension: Optional[float] = None
    propaganda_detected: bool = False

    # Entities
    entities: List[Dict[str, Any]] = []

    # Temporal
    published_at: Optional[datetime] = None
    created_at: datetime


class SecurityEventList(BaseModel):
    """Paginated list of security events."""

    events: List[SecurityEvent]
    total: int
    page: int
    per_page: int
    filters_applied: Dict[str, Any] = {}


# =============================================================================
# Country Threat Profile
# =============================================================================

class CountryThreatSummary(BaseModel):
    """Aggregated threat data for a country."""

    country_code: str
    country_name: str
    lat: float
    lon: float
    region: Optional[str] = None

    # Counts by category
    total_events: int = 0
    conflict_count: int = 0
    security_count: int = 0
    humanitarian_count: int = 0
    politics_count: int = 0

    # Severity metrics
    max_priority_score: int = 0
    avg_priority_score: float = 0.0
    max_threat_level: ThreatLevel = ThreatLevel.LOW

    # Geopolitical metrics (averaged)
    avg_conflict_severity: Optional[float] = None
    avg_regional_stability_risk: Optional[float] = None
    avg_diplomatic_impact: Optional[float] = None

    # Trend
    trend: TrendDirection = TrendDirection.STABLE
    trend_change_percent: float = 0.0

    # Last update
    last_event_at: Optional[datetime] = None


class CountryThreatDetail(CountryThreatSummary):
    """Full country threat profile with recent events."""

    # Key entities in this country's events
    key_entities: List[Dict[str, Any]] = []

    # Geopolitical relations
    relations: List[Dict[str, Any]] = []

    # Recent events preview
    recent_events: List[SecurityEvent] = []


# =============================================================================
# Overview / Dashboard
# =============================================================================

class SecurityOverview(BaseModel):
    """Global security overview for dashboard."""

    # Time range
    from_date: datetime
    to_date: datetime

    # Global counts
    total_events: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0

    # By category
    by_category: Dict[str, int] = {}

    # By region
    by_region: Dict[str, int] = {}

    # Top threat countries
    hotspots: List[CountryThreatSummary] = []

    # Recent critical events
    critical_events: List[SecurityEvent] = []

    # Trend comparison (vs previous period)
    trend_vs_previous: Dict[str, float] = {}


# =============================================================================
# Geopolitical Relations
# =============================================================================

class GeopoliticalRelation(BaseModel):
    """Relation between two countries from news analysis."""

    source_country: str
    target_country: str
    relation_type: str  # OPPOSES, SUPPORTS, NEGOTIATES, CONDEMNS, ALLIES
    article_count: int = 1
    avg_tension: Optional[float] = None
    last_seen: Optional[datetime] = None


class RelationNetwork(BaseModel):
    """Network of geopolitical relations for visualization."""

    nodes: List[Dict[str, Any]]  # Countries
    edges: List[GeopoliticalRelation]
    generated_at: datetime


# =============================================================================
# Map Marker (Extended)
# =============================================================================

class SecurityMarker(BaseModel):
    """Security marker for map visualization."""

    id: str
    lat: float
    lon: float
    country_code: str

    # Threat classification
    threat_level: ThreatLevel
    category: str

    # Content
    title: str
    summary: Optional[str] = None

    # Metrics
    priority_score: int
    conflict_severity: Optional[float] = None
    impact_score: Optional[float] = None

    # Context
    entities: List[str] = []
    countries_involved: List[str] = []
    article_count: int = 1

    # Temporal
    first_seen: datetime
    last_update: datetime

    # Analysis flags
    dominant_frame: Optional[str] = None
    propaganda_detected: bool = False


# =============================================================================
# Watchlist Schemas
# =============================================================================

class WatchlistItemType(str, Enum):
    """Types of items that can be watched."""
    ENTITY = "entity"
    COUNTRY = "country"
    KEYWORD = "keyword"
    REGION = "region"


class WatchlistItemCreate(BaseModel):
    """Create a new watchlist item."""
    item_type: WatchlistItemType
    item_value: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = None
    notes: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)
    notify_on_new: bool = True
    notify_threshold: int = Field(7, ge=1, le=10)


class WatchlistItem(WatchlistItemCreate):
    """Watchlist item with metadata."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    # Computed fields
    match_count_24h: int = 0
    match_count_7d: int = 0
    last_match_at: Optional[datetime] = None


class WatchlistItemUpdate(BaseModel):
    """Update watchlist item."""
    display_name: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    notify_on_new: Optional[bool] = None
    notify_threshold: Optional[int] = Field(None, ge=1, le=10)


class SecurityAlert(BaseModel):
    """Alert triggered by watchlist match."""
    id: UUID
    watchlist_id: UUID
    article_id: UUID
    title: str
    priority_score: int
    threat_level: ThreatLevel
    country_code: Optional[str] = None
    matched_value: str
    is_read: bool = False
    created_at: datetime


class AlertList(BaseModel):
    """Paginated list of alerts."""
    alerts: List[SecurityAlert]
    total: int
    unread_count: int
    page: int
    per_page: int


class AlertStats(BaseModel):
    """Alert statistics for badge display."""
    total_unread: int
    critical_unread: int
    high_unread: int
    last_alert_at: Optional[datetime] = None


# =============================================================================
# Anomaly Detection Schemas
# =============================================================================

class AnomalyData(BaseModel):
    """Anomaly detection data for a region/country."""
    entity: str  # Country code or region name
    entity_type: str  # 'country' or 'region'
    current_count: int
    baseline_avg: float
    baseline_stddev: float
    deviation_factor: float  # How many stddevs above baseline
    is_anomaly: bool
    trend: str  # 'spike', 'elevated', 'normal', 'low'
    category_breakdown: Dict[str, int] = {}


class AnomalyResponse(BaseModel):
    """Anomaly detection response."""
    period: str
    baseline_days: int
    anomalies: List[AnomalyData]
    escalating_regions: List[str]


# =============================================================================
# Entity Graph Schemas
# =============================================================================

class EntityNode(BaseModel):
    """Node in entity relationship graph."""
    id: str
    name: str
    type: str  # PERSON, ORG, GPE, etc.
    threat_score: Optional[float] = None
    mention_count: int = 0
    countries: List[str] = []


class EntityEdge(BaseModel):
    """Edge in entity relationship graph."""
    source: str
    target: str
    relationship: str  # OPPOSES, SUPPORTS, WORKS_FOR, etc.
    weight: float = 1.0
    evidence: Optional[str] = None


class EntityGraphResponse(BaseModel):
    """Entity relationship graph response."""
    nodes: List[EntityNode]
    edges: List[EntityEdge]
    total_nodes: int
    total_edges: int