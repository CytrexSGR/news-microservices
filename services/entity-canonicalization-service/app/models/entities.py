"""Pydantic models for entity canonicalization."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class EntityCanonical(BaseModel):
    """Canonical entity representation."""

    canonical_name: str = Field(..., description="Canonical entity name")
    canonical_id: Optional[str] = Field(None, description="Wikidata Q-ID (e.g., Q30)")
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Canonicalization confidence")
    source: str = Field(..., description="Source of canonicalization: exact|fuzzy|wikidata|semantic|new")
    entity_type: Optional[str] = Field(None, description="Entity type (PERSON, ORGANIZATION, etc.)")


class CanonicalizeRequest(BaseModel):
    """Request to canonicalize an entity."""

    entity_name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., description="Entity type from extraction")
    language: str = Field(default="de", description="Language code (de, en, etc.)")


class CanonicalizeResponse(BaseModel):
    """Response from canonicalization."""

    canonical_name: str
    canonical_id: Optional[str] = None
    aliases: List[str] = []
    confidence: float
    source: str
    entity_type: str
    processing_time_ms: Optional[float] = None


class CanonicalizeBatchRequest(BaseModel):
    """Batch canonicalization request."""

    entities: List[CanonicalizeRequest] = Field(..., min_length=1, max_length=100)


class CanonicalizeBatchResponse(BaseModel):
    """Batch canonicalization response."""

    results: List[CanonicalizeResponse]
    total_processed: int
    total_time_ms: float


class AliasInfo(BaseModel):
    """Information about an alias."""

    alias: str
    canonical_name: str
    canonical_id: Optional[str] = None
    created_at: datetime


class CanonicalizationStats(BaseModel):
    """Canonicalization statistics."""

    total_canonical_entities: int
    total_aliases: int
    wikidata_linked: int
    coverage_percentage: float
    cache_hit_rate: Optional[float] = None


class TopCanonicalEntity(BaseModel):
    """Top canonical entity with alias count."""

    canonical_name: str
    canonical_id: Optional[str] = None
    entity_type: str
    alias_count: int
    wikidata_linked: bool


class SourceBreakdown(BaseModel):
    """Breakdown of canonicalization sources."""

    exact: int = Field(0, description="Exact alias matches")
    fuzzy: int = Field(0, description="Fuzzy string matches")
    semantic: int = Field(0, description="Semantic similarity matches")
    wikidata: int = Field(0, description="Wikidata API matches")
    new: int = Field(0, description="Newly created entities")


class DetailedCanonicalizationStats(BaseModel):
    """Detailed canonicalization statistics for admin dashboard."""

    # Basic stats
    total_canonical_entities: int
    total_aliases: int
    wikidata_linked: int
    wikidata_coverage_percent: float
    deduplication_ratio: float = Field(..., description="Aliases per canonical entity")

    # Source breakdown
    source_breakdown: SourceBreakdown

    # Entity type distribution
    entity_type_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Count of entities by type"
    )

    # Top deduplicated entities
    top_entities_by_aliases: List[TopCanonicalEntity] = Field(
        default_factory=list,
        description="Entities with most aliases (top 10)"
    )

    # Quality metrics
    entities_without_qid: int = Field(..., description="Entities without Wikidata Q-ID")

    # Performance metrics
    avg_cache_hit_time_ms: Optional[float] = Field(None, description="Average cache hit response time")
    cache_hit_rate: Optional[float] = Field(None, description="Percentage of cache hits")

    # Impact metrics
    total_api_calls_saved: int = Field(..., description="Estimated API calls saved by caching")
    estimated_cost_savings_monthly: float = Field(..., description="Estimated monthly cost savings")


class WikidataMatch(BaseModel):
    """Wikidata entity match."""

    id: str = Field(..., description="Wikidata Q-ID")
    label: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    aliases: List[str] = []
    entity_type: Optional[str] = None


# ===========================
# Batch Reprocessing Models
# ===========================

class ReprocessingStats(BaseModel):
    """Statistics tracked during batch reprocessing."""
    total_entities: int = 0
    processed_entities: int = 0
    duplicates_found: int = 0
    entities_merged: int = 0
    qids_added: int = 0
    errors: int = 0


class ReprocessingStatus(BaseModel):
    """Current status of batch reprocessing job."""
    status: Literal["idle", "running", "completed", "failed"] = "idle"
    progress_percent: float = 0.0
    current_phase: Optional[
        Literal[
            "analyzing",
            "fuzzy_matching",
            "semantic_matching",
            "wikidata_lookup",
            "merging",
            "updating"
        ]
    ] = None
    stats: ReprocessingStats = Field(default_factory=ReprocessingStats)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    dry_run: bool = False


class StartReprocessingRequest(BaseModel):
    """Request to start batch reprocessing."""
    dry_run: bool = Field(False, description="If true, only analyze without making changes")


class EntityTypeTrendData(BaseModel):
    """Entity type counts for a specific date."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    PERSON: int = 0
    ORGANIZATION: int = 0
    LOCATION: int = 0
    EVENT: int = 0
    PRODUCT: int = 0
    OTHER: int = 0
    MISC: int = 0
    NOT_APPLICABLE: int = 0


class EntityTypeTrendsResponse(BaseModel):
    """Response with entity type trends over time."""
    trends: List[EntityTypeTrendData] = Field(..., description="Daily entity type counts")
    days: int = Field(..., description="Number of days included")
    total_entities: int = Field(..., description="Total entities across all types")


# ===========================
# Async Batch Processing Models
# ===========================

class AsyncBatchJobResponse(BaseModel):
    """Response when starting an async batch canonicalization job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field("queued", description="Initial job status")
    message: str = Field(..., description="Confirmation message")
    total_entities: int = Field(..., description="Total entities to process")


class AsyncBatchJobStats(BaseModel):
    """Statistics tracked during async batch processing."""
    total_entities: int = 0
    processed_entities: int = 0
    successful: int = 0
    failed: int = 0


class AsyncBatchJobStatus(BaseModel):
    """Current status of async batch canonicalization job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field("queued", description="Current job status")
    progress_percent: float = Field(0.0, ge=0.0, le=100.0, description="Completion percentage")
    stats: AsyncBatchJobStats = Field(default_factory=AsyncBatchJobStats, description="Processing statistics")
    started_at: Optional[str] = Field(None, description="ISO8601 timestamp when job started")
    completed_at: Optional[str] = Field(None, description="ISO8601 timestamp when job completed")
    error_message: Optional[str] = Field(None, description="Error message if job failed")


class AsyncBatchJobResult(BaseModel):
    """Result of completed async batch canonicalization job."""
    job_id: str = Field(..., description="Unique job identifier")
    results: List[CanonicalizeResponse] = Field(..., description="Canonicalization results")
    total_processed: int = Field(..., description="Total entities processed")
    total_time_ms: float = Field(..., description="Total processing time in milliseconds")
