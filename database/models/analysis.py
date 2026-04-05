"""
Analysis models for Content Analysis Service.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Numeric, Enum, Index, UniqueConstraint,
    Table, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship

from database.models.base import Base, TimestampMixin


class AnalysisType(PyEnum):
    """Types of analysis available."""
    FULL = "full"
    CATEGORY = "category"  # Fixed category assignment (6 categories)
    SENTIMENT = "sentiment"
    FINANCE_SENTIMENT = "finance_sentiment"
    GEOPOLITICAL_SENTIMENT = "geopolitical_sentiment"
    ENTITIES = "entities"
    TOPICS = "topics"
    SUMMARY = "summary"
    FACTS = "facts"
    KEYWORDS = "keywords"
    EVENT_ANALYSIS = "EVENT_ANALYSIS"  # OSINT Event Analysis (keep uppercase to match DB)


class AnalysisStatus(PyEnum):
    """Status of analysis job."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SentimentLabel(PyEnum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    NOT_APPLICABLE = "not_applicable"  # Article is purely factual/informational without sentiment


class BiasDirection(PyEnum):
    """Political bias direction."""
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    UNKNOWN = "unknown"


class MarketSentiment(PyEnum):
    """Market sentiment direction for finance analysis."""
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    NOT_APPLICABLE = "not_applicable"  # Article has no financial/market relevance


class TimeHorizon(PyEnum):
    """Time horizon for analysis predictions."""
    SHORT = "short"  # Days to weeks
    MEDIUM = "medium"  # Weeks to months
    LONG = "long"  # Months to years
    NOT_APPLICABLE = "not_applicable"  # No time-based prediction applicable


class ConflictType(PyEnum):
    """Types of geopolitical conflicts."""
    DIPLOMATIC = "diplomatic"
    ECONOMIC = "economic"
    HYBRID = "hybrid"
    INTERSTATE_WAR = "interstate_war"
    NUCLEAR_THREAT = "nuclear_threat"
    NOT_APPLICABLE = "not_applicable"  # Article has no geopolitical conflict relevance
    UNKNOWN = "unknown"


class EntityType(PyEnum):
    """Types of named entities."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    # NEW: Extended types for Knowledge Graph (2025-10-24 - Phase 2)
    QUANTITY = "QUANTITY"  # Numerical quantities (e.g., "30 workers")
    MOVIE = "MOVIE"  # Film/movie titles
    LEGISLATION = "LEGISLATION"  # Laws, regulations, legal codes
    NATIONALITY = "NATIONALITY"  # Nationalities, ethnic groups (NORP)
    PLATFORM = "PLATFORM"  # Software platforms, services
    LEGAL_CASE = "LEGAL_CASE"  # Court cases, legal proceedings
    NOT_APPLICABLE = "NOT_APPLICABLE"  # No entities to extract from this content


class RelationshipType(PyEnum):
    """Types of entity relationships."""
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    RELATED_TO = "related_to"
    MEMBER_OF = "member_of"
    PARTNER_OF = "partner_of"
    # NEW: Extended types for Knowledge Graph (2025-10-23)
    RULED_AGAINST = "ruled_against"  # Legal/judicial decisions
    ABUSED_MONOPOLY_IN = "abused_monopoly_in"  # Antitrust violations
    ANNOUNCED = "announced"  # Official announcements
    # NEW: Phase 2 Extensions (2025-10-24) - From test analysis
    REPORTS_TO = "reports_to"  # Reporting hierarchies
    PRODUCES = "produces"  # Manufacturing/creation relationships
    FOUNDED_IN = "founded_in"  # Founding/inception in location
    ADVISED = "advised"  # Advisory relationships
    OWNED_BY = "owned_by"  # Ownership (inverse of owns)
    WORKED_WITH = "worked_with"  # Collaboration
    CREATED = "created"  # Creation/authorship
    COLLABORATED_WITH = "collaborated_with"  # Professional collaboration
    FOUNDED_BY = "founded_by"  # Company/org founded by person
    INVESTED_IN = "invested_in"  # Investment relationships
    BRAND_AMBASSADOR_FOR = "brand_ambassador_for"  # Brand representation
    SPOKESPERSON_FOR = "spokesperson_for"  # Official representation
    RAN = "ran"  # Leadership of campaigns/initiatives
    OVERSAW = "oversaw"  # Oversight/management
    INITIALLY_AGREED_TO_ACQUIRE = "initially_agreed_to_acquire"  # Acquisition intent
    SUPPORTS = "supports"  # Political/ideological support
    OPPOSES = "opposes"  # Political/ideological opposition
    STUDIED_AT = "studied_at"  # Educational relationships
    COMPETES_WITH = "competes_with"  # Competitive relationships
    ACQUIRED = "acquired"  # Completed acquisitions
    REGULATES = "regulates"  # Regulatory authority
    NOT_APPLICABLE = "not_applicable"  # No relationships to extract


class SummaryType(PyEnum):
    """Types of summaries."""
    SHORT = "short"  # 1 sentence
    MEDIUM = "medium"  # 3 sentences
    LONG = "long"  # 1 paragraph


class FactType(PyEnum):
    """Types of extracted facts."""
    CLAIM = "claim"
    STATISTIC = "statistic"
    QUOTE = "quote"
    EVENT = "event"


class VerificationStatus(PyEnum):
    """Fact verification status."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    FALSE = "false"


class ArticleCategory(PyEnum):
    """Fixed article categories (6 main categories)."""
    GEOPOLITICS_SECURITY = "Geopolitics Security"
    POLITICS_SOCIETY = "Politics Society"
    ECONOMY_MARKETS = "Economy Markets"
    CLIMATE_ENVIRONMENT_HEALTH = "Climate Environment Health"
    PANORAMA = "Panorama"
    TECHNOLOGY_SCIENCE = "Technology Science"


class ModelProvider(str, PyEnum):
    """LLM model providers."""
    OPENAI = "OPENAI"  # Must match database enum (uppercase)
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    HUGGINGFACE = "HUGGINGFACE"


# Association table for many-to-many relationship between entities
entity_relationships = Table(
    'entity_relationships_assoc',
    Base.metadata,
    Column('relationship_id', UUID(as_uuid=True), ForeignKey('entity_relationships.id')),
    Column('entity_id', UUID(as_uuid=True), ForeignKey('extracted_entities.id'))
)


class AnalysisResult(Base, TimestampMixin):
    """Main analysis results table."""

    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # FK to feed-service items
    analysis_type = Column(Enum(AnalysisType, name='analysistype', create_type=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    model_used = Column(String(100), nullable=False)
    model_provider = Column(Enum(ModelProvider), nullable=False)
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING, index=True)

    # Cost tracking
    total_cost = Column(Numeric(10, 6), default=0)
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)

    # Performance tracking
    processing_time_ms = Column(Integer)
    cached = Column(Boolean, default=False, index=True)
    cache_key = Column(String(64))  # SHA256 hash

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Raw response storage
    raw_response = Column(JSONB)

    # NEW: Structured relationship triplets for Knowledge Graph (2025-10-23)
    extracted_relationships = Column(
        JSONB,
        comment="Structured relationship triplets [[entity1, relation, entity2], ...]"
    )
    relationship_metadata = Column(
        JSONB,
        comment="Confidence scores, evidence, validation metrics for relationships"
    )

    # ============ UQ (Uncertainty Quantification) Fields (2025-10-24) ============
    uq_confidence_score = Column(
        Float,
        nullable=True,
        comment='UQ confidence score (0.0-1.0)'
    )
    uncertainty_factors = Column(
        JSONB,
        nullable=True,
        comment='List of textual uncertainty reasons'
    )
    requires_verification = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment='Flag to trigger DIA verification workflow'
    )
    uq_metadata = Column(
        JSONB,
        nullable=True,
        comment='Detailed UQ metrics (mean_logprob, entropy, etc.)'
    )

    # Relationships
    category = relationship("CategoryClassification", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")
    sentiment = relationship("SentimentAnalysis", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")
    finance_sentiment = relationship("FinanceSentiment", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")
    geopolitical_sentiment = relationship("GeopoliticalSentiment", back_populates="analysis_result", uselist=False, cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="analysis_result", cascade="all, delete-orphan")
    topics = relationship("TopicClassification", back_populates="analysis_result", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="analysis_result", cascade="all, delete-orphan")
    facts = relationship("ExtractedFact", back_populates="analysis_result", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_analysis_article_type', 'article_id', 'analysis_type'),
        Index('idx_analysis_status_created', 'status', 'created_at'),
        Index('idx_analysis_uq_score', 'uq_confidence_score'),  # UQ score queries
        UniqueConstraint('article_id', 'analysis_type', 'model_used', name='uq_analysis_article_type_model'),
    )


class CategoryClassification(Base, TimestampMixin):
    """Fixed category classification (6 main categories)."""

    __tablename__ = "category_classification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, unique=True)

    # Category assignment
    category = Column(Enum(ArticleCategory), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Alternative categories (second and third best matches)
    alternative_categories = Column(JSONB)  # [{"category": "...", "confidence": 0.x}, ...]

    # Reasoning
    reasoning = Column(Text, nullable=False)
    key_indicators = Column(JSONB)  # List of keywords/phrases that influenced decision

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="category")

    # Indexes
    __table_args__ = (
        Index('idx_category_classification', 'category', 'confidence'),
    )


class SentimentAnalysis(Base, TimestampMixin):
    """Sentiment analysis results."""

    __tablename__ = "sentiment_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, unique=True)

    # Core sentiment
    overall_sentiment = Column(Enum(SentimentLabel), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Detailed scores
    positive_score = Column(Float, default=0.0)
    negative_score = Column(Float, default=0.0)
    neutral_score = Column(Float, default=0.0)

    # Bias detection
    bias_detected = Column(Boolean, default=False)
    bias_direction = Column(Enum(BiasDirection))
    bias_confidence = Column(Float)

    # Additional metrics
    subjectivity_score = Column(Float)  # 0.0 (objective) to 1.0 (subjective)
    emotion_scores = Column(JSONB)  # {"joy": 0.8, "fear": 0.2, ...}

    # Reasoning
    reasoning = Column(Text)
    key_phrases = Column(JSONB)  # List of phrases that influenced sentiment

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="sentiment")


class FinanceSentiment(Base, TimestampMixin):
    """Finance-specific sentiment analysis results."""

    __tablename__ = "finance_sentiment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, unique=True)

    # Market Direction
    market_sentiment = Column(Enum(MarketSentiment), nullable=False, index=True)
    market_confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Time Horizon
    time_horizon = Column(Enum(TimeHorizon), nullable=False, index=True)

    # Risk Metrics
    uncertainty = Column(Float, nullable=False)  # 0.0 to 1.0
    volatility = Column(Float, nullable=False)  # 0.0 to 1.0
    economic_impact = Column(Float, nullable=False)  # 0.0 to 1.0

    # Analysis Details
    reasoning = Column(Text, nullable=False)
    key_indicators = Column(JSONB)  # List of economic indicators mentioned

    # Affected Markets
    affected_sectors = Column(JSONB)  # ["technology", "finance", ...]
    affected_assets = Column(JSONB)  # ["stocks", "bonds", "crypto", ...]

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="finance_sentiment")

    # Indexes
    __table_args__ = (
        Index('idx_finance_market_horizon', 'market_sentiment', 'time_horizon'),
    )


class GeopoliticalSentiment(Base, TimestampMixin):
    """Geopolitical sentiment analysis results."""

    __tablename__ = "geopolitical_sentiment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, unique=True)

    # Stability Assessment
    stability_score = Column(Float, nullable=False, index=True)  # -1.0 (unstable) to +1.0 (stable)
    security_relevance = Column(Float, nullable=False)  # 0.0 to 1.0
    escalation_potential = Column(Float, nullable=False)  # 0.0 to 1.0

    # Conflict Classification
    conflict_type = Column(Enum(ConflictType), nullable=False, index=True)

    # Time and Confidence
    time_horizon = Column(Enum(TimeHorizon), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Geographic Impact
    regions_affected = Column(ARRAY(String))  # List of regions/countries

    # Stakeholder Impact
    impact_beneficiaries = Column(ARRAY(String))  # Countries/entities that benefit
    impact_affected = Column(ARRAY(String))  # Countries/entities negatively affected
    alliance_activation = Column(ARRAY(String))  # Alliances that may activate (NATO, etc.)

    # Diplomatic Impact Scores (multi-perspective)
    diplomatic_impact_global = Column(Float)  # -1.0 to +1.0
    diplomatic_impact_western = Column(Float)  # -1.0 to +1.0
    diplomatic_impact_regional = Column(Float)  # -1.0 to +1.0

    # Analysis Details
    reasoning = Column(Text, nullable=False)
    key_factors = Column(JSONB)  # List of key geopolitical factors

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="geopolitical_sentiment")

    # Indexes
    __table_args__ = (
        Index('idx_geopolitical_stability_conflict', 'stability_score', 'conflict_type'),
        Index('idx_geopolitical_horizon', 'time_horizon'),
    )


class ExtractedEntity(Base, TimestampMixin):
    """Named entities extracted from content."""

    __tablename__ = "extracted_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, index=True)

    # Entity information
    entity_text = Column(String(500), nullable=False, index=True)
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Occurrence tracking
    mention_count = Column(Integer, default=1)
    first_position = Column(Integer)  # Character position of first mention
    positions = Column(JSONB)  # All character positions

    # Additional metadata
    normalized_text = Column(String(500))  # Canonical form
    wikipedia_url = Column(String(1000))
    wikidata_id = Column(String(50))
    description = Column(Text)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="entities")
    relationships_as_entity1 = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.entity1_id",
        back_populates="entity1",
        cascade="all, delete-orphan"
    )
    relationships_as_entity2 = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.entity2_id",
        back_populates="entity2",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('idx_entity_text_type', 'entity_text', 'entity_type'),
        Index('idx_entity_analysis_type', 'analysis_id', 'entity_type'),
    )


class EntityRelationship(Base, TimestampMixin):
    """Relationships between extracted entities."""

    __tablename__ = "entity_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity1_id = Column(UUID(as_uuid=True), ForeignKey("extracted_entities.id"), nullable=False, index=True)
    entity2_id = Column(UUID(as_uuid=True), ForeignKey("extracted_entities.id"), nullable=False, index=True)

    relationship_type = Column(Enum(RelationshipType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Context
    evidence = Column(Text)  # Text snippet supporting the relationship
    position = Column(Integer)  # Character position in text

    # Sentiment Analysis (2025-10-25)
    sentiment_score = Column(Float)  # -1.0 to +1.0
    sentiment_category = Column(String(20))  # positive, negative, neutral
    sentiment_confidence = Column(Float)  # 0.0 to 1.0

    # Relationships
    entity1 = relationship("ExtractedEntity", foreign_keys=[entity1_id], back_populates="relationships_as_entity1")
    entity2 = relationship("ExtractedEntity", foreign_keys=[entity2_id], back_populates="relationships_as_entity2")

    # Indexes
    __table_args__ = (
        Index('idx_relationship_entities', 'entity1_id', 'entity2_id'),
        UniqueConstraint('entity1_id', 'entity2_id', 'relationship_type', name='uq_entity_relationship'),
    )


class TopicClassification(Base, TimestampMixin):
    """Topic classifications for content."""

    __tablename__ = "topic_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, index=True)

    # Topic information
    topic = Column(String(100), nullable=False, index=True)
    relevance_score = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False)

    # Hierarchical topics
    parent_topic = Column(String(100))
    topic_hierarchy = Column(JSONB)  # ["Technology", "AI", "Machine Learning"]

    # Keywords
    keywords = Column(JSONB, nullable=False)  # List of relevant keywords
    keyword_scores = Column(JSONB)  # {"keyword": score, ...}

    # Additional metadata
    is_primary = Column(Boolean, default=False)
    reasoning = Column(Text)

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="topics")

    # Indexes
    __table_args__ = (
        Index('idx_topic_analysis_primary', 'analysis_id', 'is_primary'),
        Index('idx_topic_name_score', 'topic', 'relevance_score'),
    )


class Summary(Base, TimestampMixin):
    """Content summaries."""

    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, index=True)

    # Summary information
    summary_type = Column(Enum(SummaryType), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)

    # Metrics
    compression_ratio = Column(Float)  # original_length / summary_length
    original_length = Column(Integer)
    summary_length = Column(Integer)

    # Quality metrics
    coherence_score = Column(Float)  # 0.0 to 1.0
    coverage_score = Column(Float)  # How well key points are covered

    # Additional features
    bullet_points = Column(JSONB)  # List of key points
    key_sentences = Column(JSONB)  # Original sentences used

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="summaries")

    # Indexes
    __table_args__ = (
        UniqueConstraint('analysis_id', 'summary_type', name='uq_summary_analysis_type'),
    )


class ExtractedFact(Base, TimestampMixin):
    """Facts extracted from content."""

    __tablename__ = "extracted_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_results.id"), nullable=False, index=True)

    # Fact information
    fact_text = Column(Text, nullable=False)
    fact_type = Column(Enum(FactType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Verification
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED, index=True)
    verification_source = Column(String(500))
    verification_date = Column(DateTime)

    # Context
    context = Column(Text)  # Surrounding text
    position = Column(Integer)  # Character position in text

    # Attribution
    attributed_to = Column(String(500))  # Person or organization
    source_quote = Column(Text)  # Original quote if applicable

    # Metadata
    tags = Column(JSONB)  # List of relevant tags
    related_entities = Column(JSONB)  # Entity IDs this fact relates to

    # Relationship
    analysis_result = relationship("AnalysisResult", back_populates="facts")

    # Indexes
    __table_args__ = (
        Index('idx_fact_type_verification', 'fact_type', 'verification_status'),
    )


class AnalysisModel(Base, TimestampMixin):
    """Available LLM models and configurations."""

    __tablename__ = "analysis_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Model identification
    provider = Column(Enum(ModelProvider), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))

    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)

    # Capabilities
    supports_sentiment = Column(Boolean, default=True)
    supports_entities = Column(Boolean, default=True)
    supports_topics = Column(Boolean, default=True)
    supports_summary = Column(Boolean, default=True)
    supports_facts = Column(Boolean, default=True)

    # Performance characteristics
    max_tokens = Column(Integer, nullable=False)
    max_context_length = Column(Integer, nullable=False)
    temperature_default = Column(Float, default=0.1)

    # Cost information (per 1M tokens)
    input_cost_per_million = Column(Numeric(10, 4))
    output_cost_per_million = Column(Numeric(10, 4))

    # Configuration
    config = Column(JSONB)  # Provider-specific configuration

    # Metrics
    total_requests = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 4), default=0)
    average_latency_ms = Column(Integer)
    error_rate = Column(Float, default=0)

    # Indexes
    __table_args__ = (
        UniqueConstraint('provider', 'model_name', 'model_version', name='uq_model_provider_name_version'),
    )


class AnalysisTemplate(Base, TimestampMixin):
    """Reusable analysis templates."""

    __tablename__ = "analysis_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Template identification
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)

    # Configuration
    is_active = Column(Boolean, default=True)
    analysis_types = Column(ARRAY(String))  # List of AnalysisType values

    # Prompts
    system_prompt = Column(Text)
    user_prompt_template = Column(Text)

    # Model configuration
    preferred_model_id = Column(UUID(as_uuid=True), ForeignKey("analysis_models.id"))
    temperature = Column(Float, default=0.1)
    max_tokens = Column(Integer)

    # Output configuration
    output_format = Column(String(20), default="json")  # json, text, markdown
    output_schema = Column(JSONB)  # JSON schema for validation

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Relationship
    preferred_model = relationship("AnalysisModel")


class AnalysisCache(Base, TimestampMixin):
    """Cache for expensive analysis operations."""

    __tablename__ = "analysis_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Cache key (SHA256 of content + analysis_type + model)
    cache_key = Column(String(64), nullable=False, unique=True, index=True)

    # Cache metadata
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    model_used = Column(String(100), nullable=False)

    # Cached result
    result = Column(JSONB, nullable=False)

    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)

    # Usage tracking
    hit_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)

    # Source tracking
    source_hash = Column(String(64))  # Hash of original content
    source_length = Column(Integer)


class ContentEmbedding(Base, TimestampMixin):
    """Vector embeddings for semantic search."""

    __tablename__ = "content_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Source identification
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_index = Column(Integer, default=0)  # For long content split into chunks

    # Embedding information
    model_used = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)

    # The actual embedding (stored as JSONB for simplicity, could use pgvector)
    embedding = Column(JSONB, nullable=False)

    # Metadata
    text_chunk = Column(Text)  # The text this embedding represents
    chunk_length = Column(Integer)

    # Search optimization
    search_vector = Column(TSVECTOR)  # For full-text search

    # Indexes
    __table_args__ = (
        UniqueConstraint('article_id', 'chunk_index', 'model_used', name='uq_embedding_article_chunk_model'),
        Index('idx_embedding_search_vector', 'search_vector', postgresql_using='gin'),
    )


class AnalysisMetric(Base, TimestampMixin):
    """Performance and accuracy metrics."""

    __tablename__ = "analysis_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Metric identification
    metric_date = Column(DateTime, nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # daily, hourly

    # Analysis metrics
    total_analyses = Column(Integer, default=0)
    successful_analyses = Column(Integer, default=0)
    failed_analyses = Column(Integer, default=0)
    cancelled_analyses = Column(Integer, default=0)

    # Performance metrics
    average_latency_ms = Column(Integer)
    p50_latency_ms = Column(Integer)
    p95_latency_ms = Column(Integer)
    p99_latency_ms = Column(Integer)

    # Cost metrics
    total_cost = Column(Numeric(10, 4), default=0)
    total_tokens_used = Column(Integer, default=0)

    # Cache metrics
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    cache_hit_rate = Column(Float)

    # Model breakdown
    model_metrics = Column(JSONB)  # {model_name: {requests, tokens, cost, latency}}

    # Analysis type breakdown
    type_metrics = Column(JSONB)  # {analysis_type: {count, avg_latency, cost}}

    # Indexes
    __table_args__ = (
        UniqueConstraint('metric_date', 'metric_type', name='uq_metric_date_type'),
        Index('idx_metric_date_type', 'metric_date', 'metric_type'),
    )


class ModelUsageStat(Base, TimestampMixin):
    """Track model usage and costs."""

    __tablename__ = "model_usage_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Time window
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Model identification
    model_id = Column(UUID(as_uuid=True), ForeignKey("analysis_models.id"), nullable=False)

    # Usage statistics
    request_count = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)

    # Token usage
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)

    # Cost tracking
    total_cost = Column(Numeric(10, 4), default=0)

    # Performance
    average_latency_ms = Column(Integer)
    max_latency_ms = Column(Integer)
    min_latency_ms = Column(Integer)

    # Error tracking
    error_count = Column(Integer, default=0)
    error_types = Column(JSONB)  # {error_type: count}

    # Relationship
    model = relationship("AnalysisModel")

    # Indexes
    __table_args__ = (
        Index('idx_usage_period_model', 'period_start', 'model_id'),
        UniqueConstraint('period_start', 'period_end', 'model_id', name='uq_usage_period_model'),
    )