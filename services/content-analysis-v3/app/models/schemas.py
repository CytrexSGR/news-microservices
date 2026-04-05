"""
Content-Analysis-V3 Pydantic Models
Based on: /home/cytrex/userdocs/content-analysis-v3/design/data-model.md
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID

from app.models.validators import CanonicalTypeValidator


# ============================================================================
# TIER 0: TRIAGE
# ============================================================================

class TriageDecision(BaseModel):
    """Tier 0 output - Fast keep/discard decision."""

    PriorityScore: int = Field(ge=0, le=10, description="Urgency score 0-10")
    category: Literal[
        "CONFLICT", "FINANCE", "POLITICS", "HUMANITARIAN",
        "SECURITY", "TECHNOLOGY", "HEALTH", "OTHER"
    ]
    keep: bool = Field(description="True = process further, False = discard")

    # Metadata
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""

    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, v):
        """Map unrecognized categories to canonical ones."""
        if not isinstance(v, str):
            return v

        # Mapping of common LLM variations to canonical categories
        category_map = {
            "ECONOMICS": "FINANCE",
            "ECONOMIC": "FINANCE",
            "BUSINESS": "FINANCE",
            "RELIGION": "OTHER",
            "RELIGIOUS": "OTHER",
            "CULTURE": "OTHER",
            "CULTURAL": "OTHER",
            "ENVIRONMENT": "OTHER",
            "CLIMATE": "OTHER",
            "EDUCATION": "OTHER",
            "SCIENCE": "TECHNOLOGY",
        }

        v_upper = v.upper()
        return category_map.get(v_upper, v_upper if v_upper in [
            "CONFLICT", "FINANCE", "POLITICS", "HUMANITARIAN",
            "SECURITY", "TECHNOLOGY", "HEALTH", "OTHER"
        ] else "OTHER")


# ============================================================================
# TIER 1: FOUNDATION EXTRACTION
# ============================================================================

class Entity(BaseModel):
    """Single entity extraction."""
    name: str = Field(max_length=200)
    type: Literal[
        "PERSON", "ORGANIZATION", "LOCATION", "EVENT",  # Core types
        "CONCEPT", "TECHNOLOGY", "PRODUCT",             # Tech/Abstract
        "CURRENCY", "FINANCIAL_INSTRUMENT",             # Finance
        "LAW", "POLICY",                                # Politics/Legal
        "TIME",                                         # Temporal entities
        "OTHER"                                         # Catch-all
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    mentions: int = Field(ge=0, description="How often mentioned")

    # Optional enrichment
    aliases: list[str] = Field(default_factory=list)
    role: Optional[str] = None  # e.g., "CEO", "Minister"

    @field_validator('type', mode='before')
    @classmethod
    def normalize_entity_type(cls, v):
        """Normalize common LLM variations to canonical entity types."""
        return CanonicalTypeValidator.normalize_entity_type(v)


class Relation(BaseModel):
    """Subject-Predicate-Object relation."""
    subject: str = Field(description="Entity name")
    predicate: str = Field(description="Relation type (WORKS_FOR, LOCATED_IN, etc.)")
    object: str = Field(description="Target entity name")
    confidence: float = Field(ge=0.0, le=1.0)


class Topic(BaseModel):
    """Categorical topic classification."""
    keyword: str = Field(description="Router keyword (FINANCE, CONFLICT, etc.)")
    confidence: float = Field(ge=0.0, le=1.0)
    parent_category: str = Field(description="TOPIC_CLASSIFIER parent topic")


class Tier1Results(BaseModel):
    """Tier 1 structured extraction output."""

    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    topics: list[Topic] = Field(default_factory=list)

    @field_validator('relations', mode='before')
    @classmethod
    def filter_invalid_relations(cls, v):
        """Filter out relations with None values in subject, predicate, or object."""
        if not isinstance(v, list):
            return v
        return [
            rel for rel in v
            if isinstance(rel, dict) and
            rel.get('subject') is not None and
            rel.get('predicate') is not None and
            rel.get('object') is not None
        ]

    # Scores (numerical only)
    impact_score: float = Field(ge=0.0, le=10.0)
    credibility_score: float = Field(ge=0.0, le=10.0)
    urgency_score: float = Field(ge=0.0, le=10.0)

    # Metadata
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""


# ============================================================================
# TIER 2: SPECIALIST ANALYSIS
# ============================================================================

class SpecialistFindings(BaseModel):
    """Output from a single specialist (e.g., FINANCIAL_ANALYST)."""

    specialist_name: Literal[
        "TOPIC_CLASSIFIER", "ENTITY_EXTRACTOR", "FINANCIAL_ANALYST",
        "GEOPOLITICAL_ANALYST", "SENTIMENT_ANALYZER"
    ]

    # Structured findings only
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)

    # Metadata
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    execution_time_ms: float = 0.0


class Tier2Results(BaseModel):
    """Tier 2 output - All specialist findings."""

    TOPIC_CLASSIFIER: Optional[SpecialistFindings] = None
    ENTITY_EXTRACTOR: Optional[SpecialistFindings] = None
    FINANCIAL_ANALYST: Optional[SpecialistFindings] = None
    GEOPOLITICAL_ANALYST: Optional[SpecialistFindings] = None
    SENTIMENT_ANALYZER: Optional[SpecialistFindings] = None

    # Aggregated metadata
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    specialists_executed: int = 0


# ============================================================================
# TIER 3: INTELLIGENCE MODULES
# ============================================================================

class SymbolicFinding(BaseModel):
    """Single symbolic finding for Neo4j ingestion."""

    finding_type: Literal[
        "ENTITY_CLUSTER",
        "CAUSAL_CHAIN",
        "TEMPORAL_SEQUENCE",
        "CONFLICT_PATTERN",
        "INFLUENCE_NETWORK"
    ]

    # Graph-ready structure
    nodes: list[dict] = Field(description="Nodes with properties")
    edges: list[dict] = Field(description="Edges with properties")

    confidence: float = Field(ge=0.0, le=1.0)


class IntelligenceModuleOutput(BaseModel):
    """Output from a single intelligence module (e.g., FINANCIAL_INTELLIGENCE)."""

    module_name: Literal[
        "EVENT_INTELLIGENCE", "SECURITY_INTELLIGENCE",
        "HUMANITARIAN_INTELLIGENCE", "GEOPOLITICAL_INTELLIGENCE",
        "FINANCIAL_INTELLIGENCE", "REGIONAL_INTELLIGENCE"
    ]

    symbolic_findings: list[SymbolicFinding] = Field(default_factory=list)

    # Numerical metrics only (for PostgreSQL)
    metrics: dict[str, float] = Field(default_factory=dict)

    # Metadata
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    execution_time_ms: float = 0.0


class RouterDecision(BaseModel):
    """Intelligence Router decision."""

    modules_to_run: list[str] = Field(default_factory=list)
    skipped_modules: list[str] = Field(default_factory=list)
    decision_time_ms: float = 0.0


class Tier3Results(BaseModel):
    """Tier 3 output - Router-triggered intelligence modules."""

    # Modules (0-7 can be triggered)
    EVENT_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None
    SECURITY_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None
    HUMANITARIAN_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None
    GEOPOLITICAL_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None
    FINANCIAL_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None
    REGIONAL_INTELLIGENCE: Optional[IntelligenceModuleOutput] = None

    # Router decision
    router_decision: RouterDecision

    # Aggregated metadata
    modules_executed: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0


# ============================================================================
# COMPLETE V3 ARTICLE ANALYSIS
# ============================================================================

class V3ArticleAnalysis(BaseModel):
    """Complete V3 analysis result for a single article."""

    article_id: UUID
    version: Literal["v3"] = "v3"

    # Tier results
    tier0: TriageDecision
    tier1: Tier1Results
    tier2: Tier2Results
    tier3: Tier3Results

    # Aggregated statistics
    total_cost_usd: float
    total_tokens: int
    processing_time_ms: int

    # Provider breakdown
    providers_used: dict[str, int] = Field(
        description="Token usage per provider",
        example={"gemini-flash": 11800, "gpt-4o-mini": 3000}
    )

    created_at: datetime


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeArticleRequest(BaseModel):
    """Request to analyze a single article."""
    article_id: UUID


class AnalyzeArticleResponse(BaseModel):
    """Response from article analysis."""
    article_id: UUID
    status: Literal["pending", "processing", "completed", "failed"]
    message: str


# ============================================================================
# PROVIDER METADATA
# ============================================================================

class ProviderMetadata(BaseModel):
    """Metadata returned by LLM provider."""
    tokens_used: int
    cost_usd: float
    model: str
    latency_ms: int
    provider: str  # "gemini" or "openai"
