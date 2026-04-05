# services/sitrep-service/app/schemas/sitrep.py
"""Schemas for SITREP reports.

Defines Pydantic models for SITREP generation and storage:
- EntityMention: Named entities mentioned in the report
- SentimentSummary: Overall sentiment analysis
- EmergingSignal: Detected trends or patterns
- RiskAssessment: Risk level assessment for key developments
- KeyDevelopment: Major development in the briefing
- SitrepCreate: Input schema for creating a SITREP
- SitrepResponse: Full SITREP response with all fields
- GenerationPrompt: Context for LLM prompt generation
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EntityMention(BaseModel):
    """Entity mentioned in SITREP.

    Represents a named entity (person, organization, location, etc.)
    extracted from the aggregated stories.

    Attributes:
        name: Entity name/identifier
        type: Entity type (person, organization, location, event, etc.)
        mention_count: Number of times entity appears across stories
        sentiment: Entity-specific sentiment (positive, negative, neutral)
    """

    name: str
    type: str  # person, organization, location, event, etc.
    mention_count: int = 1
    sentiment: Optional[str] = None  # positive, negative, neutral

    model_config = {"from_attributes": True}


class SentimentSummary(BaseModel):
    """Sentiment analysis summary.

    Provides aggregate sentiment metrics across all stories
    included in the SITREP.

    Attributes:
        overall: Dominant sentiment (positive, negative, neutral, mixed)
        positive_percent: Percentage of positive stories
        negative_percent: Percentage of negative stories
        neutral_percent: Percentage of neutral stories
    """

    overall: str  # positive, negative, neutral, mixed
    positive_percent: float = 0.0
    negative_percent: float = 0.0
    neutral_percent: float = 0.0

    model_config = {"from_attributes": True}


class EmergingSignal(BaseModel):
    """Emerging trend or signal detected.

    Represents a pattern, trend, or signal identified from
    the aggregated stories that may warrant attention.

    Attributes:
        signal_type: Type of signal (trend, pattern, anomaly, etc.)
        description: Human-readable description of the signal
        confidence: Confidence score for the signal (0-1)
        related_entities: Entities associated with this signal
    """

    signal_type: str
    description: str
    confidence: float
    related_entities: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RiskAssessment(BaseModel):
    """Risk level assessment for developments.

    Provides structured risk analysis for key developments
    in the intelligence briefing.

    Attributes:
        level: Risk level (low, medium, high, critical)
        category: Risk category (geopolitical, economic, security, etc.)
        description: Brief description of the risk
        likelihood: Estimated likelihood (0-1)
        impact: Estimated impact severity (0-10)
        mitigations: Suggested mitigations or considerations
    """

    level: str  # low, medium, high, critical
    category: str  # geopolitical, economic, security, operational
    description: str
    likelihood: Optional[float] = None  # 0-1
    impact: Optional[float] = None  # 0-10
    mitigations: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class KeyDevelopment(BaseModel):
    """Key development in the intelligence briefing.

    Represents a major development or story that warrants
    special attention in the SITREP.

    Attributes:
        title: Development headline
        summary: Brief summary of the development
        significance: Why this development matters
        risk_assessment: Associated risk assessment
        related_entities: Key entities involved
        source_cluster_id: ID of the source cluster
    """

    title: str
    summary: str
    significance: str
    risk_assessment: Optional[RiskAssessment] = None
    related_entities: List[str] = Field(default_factory=list)
    source_cluster_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class SitrepCreate(BaseModel):
    """Schema for creating a new SITREP.

    Input schema used when generating a new SITREP from
    aggregated story data.

    Attributes:
        report_date: Date of the report
        report_type: Type of report (daily, weekly, breaking)
        top_stories: List of top story data
        key_entities: Extracted key entities
        sentiment_summary: Aggregate sentiment analysis
        emerging_signals: Detected emerging signals
        articles_analyzed: Total articles analyzed
    """

    report_date: date
    report_type: str = "daily"  # daily, weekly, breaking
    top_stories: List[Dict[str, Any]]
    key_entities: List[EntityMention]
    sentiment_summary: SentimentSummary
    emerging_signals: Optional[List[EmergingSignal]] = None
    articles_analyzed: int

    model_config = {"from_attributes": True}


class SitrepResponse(BaseModel):
    """Schema for SITREP response.

    Full SITREP response with generated content and metadata.
    This is the primary output of the SitrepGenerator.

    Attributes:
        id: Unique SITREP identifier
        report_date: Date of the report
        report_type: Type of report (daily, weekly, breaking)
        category: Optional category filter (politics, finance, etc.)
        title: Generated report title
        executive_summary: High-level summary (2-3 sentences)
        content_markdown: Full report in Markdown format
        content_html: Optional HTML-rendered report
        key_developments: List of key developments with risk assessment
        top_stories: Source story data
        key_entities: Extracted entities
        sentiment_summary: Aggregate sentiment
        emerging_signals: Detected signals/trends
        generation_model: Model used for generation
        generation_time_ms: Time to generate in milliseconds
        prompt_tokens: Tokens used in prompt
        completion_tokens: Tokens used in completion
        articles_analyzed: Total articles analyzed
        confidence_score: Overall confidence in the analysis
        human_reviewed: Whether report has been reviewed
        created_at: When the report was created
    """

    id: UUID
    report_date: date
    report_type: str
    category: Optional[str] = None
    title: str
    executive_summary: str
    content_markdown: str
    content_html: Optional[str] = None
    key_developments: List[KeyDevelopment] = Field(default_factory=list)
    top_stories: List[Dict[str, Any]]
    key_entities: List[Dict[str, Any]]
    sentiment_summary: Dict[str, Any]
    emerging_signals: Optional[List[Dict[str, Any]]] = None
    generation_model: str
    generation_time_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    articles_analyzed: int
    confidence_score: Optional[float] = None
    human_reviewed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationPrompt(BaseModel):
    """Prompt context for LLM generation.

    Contains all the context needed to generate the LLM prompt
    for SITREP creation.

    Attributes:
        top_stories: List of top story data with metrics
        key_entities: Extracted entity names
        total_articles: Total articles analyzed
        time_range_hours: Lookback period for stories
        report_type: Type of report being generated
        breaking_count: Number of breaking news stories
    """

    top_stories: List[Dict[str, Any]]
    key_entities: List[str]
    total_articles: int
    time_range_hours: int = 24
    report_type: str = "daily"
    breaking_count: int = 0

    model_config = {"from_attributes": True}
