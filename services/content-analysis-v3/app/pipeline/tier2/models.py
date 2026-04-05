"""
Tier2 Specialists Data Models
Pydantic models for specialist findings and metadata
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SpecialistType(str, Enum):
    """Supported Tier2 specialists."""
    TOPIC_CLASSIFIER = "TOPIC_CLASSIFIER"
    ENTITY_EXTRACTOR = "ENTITY_EXTRACTOR"
    FINANCIAL_ANALYST = "FINANCIAL_ANALYST"
    GEOPOLITICAL_ANALYST = "GEOPOLITICAL_ANALYST"
    SENTIMENT_ANALYZER = "SENTIMENT_ANALYZER"
    BIAS_SCORER = "BIAS_SCORER"
    NARRATIVE_ANALYST = "NARRATIVE_ANALYST"


class QuickCheckResult(BaseModel):
    """Output from Stage 1: quick_check."""
    is_relevant: bool = Field(..., description="Should deep_dive run?")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Relevance confidence")
    reasoning: str = Field(..., description="Why relevant/irrelevant")
    tokens_used: int = Field(..., ge=0, description="Tokens consumed in quick check")


class TopicClassification(BaseModel):
    """Topic classifier findings."""
    topics: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {topic, parent_topic, confidence}"
    )


class EntityEnrichment(BaseModel):
    """Entity extractor enhanced findings."""
    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Enhanced entity data with additional details"
    )


class FinancialMetrics(BaseModel):
    """Financial analyst findings."""
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="market_impact (float), volatility_expected (float), sector_affected (str), price_direction (str)"
    )
    affected_symbols: List[str] = Field(default_factory=list)


class GeopoliticalMetrics(BaseModel):
    """Geopolitical analyst findings."""
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="conflict_severity, diplomatic_impact, etc."
    )
    countries_involved: List[str] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)


class SentimentMetrics(BaseModel):
    """Sentiment analyzer findings."""
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="bullish_ratio (float), bearish_ratio (float), confidence (float), sentiment_type (str)"
    )


class PoliticalBiasMetrics(BaseModel):
    """Political bias scorer findings."""
    political_direction: str = Field(
        ...,
        description="far_left, left, center_left, center, center_right, right, far_right"
    )
    bias_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="-1.0 (far left) to +1.0 (far right), center = -0.15 to +0.15"
    )
    bias_strength: str = Field(
        ...,
        description="minimal, weak, moderate, strong, extreme"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="LLM confidence in bias assessment"
    )


class NarrativeFrame(BaseModel):
    """Single narrative frame detected in article."""
    frame_type: str = Field(
        ...,
        description="victim, hero, threat, solution, conflict, economic, moral, attribution"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in frame detection"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Entities involved in this frame"
    )
    text_excerpt: str = Field(
        "",
        description="Text excerpt supporting this frame"
    )
    role_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Entity to role mapping (e.g., {'Putin': 'threat', 'Ukraine': 'victim'})"
    )


class NarrativeFrameMetrics(BaseModel):
    """Narrative analyst findings - frame detection and portrayal analysis."""
    frames: List[NarrativeFrame] = Field(
        default_factory=list,
        description="List of detected narrative frames"
    )
    dominant_frame: Optional[str] = Field(
        None,
        description="Most prominent frame type in the article"
    )
    entity_portrayals: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="How entities are portrayed: {entity_name: [roles]}"
    )
    narrative_tension: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall narrative tension/conflict level"
    )
    propaganda_indicators: List[str] = Field(
        default_factory=list,
        description="Detected propaganda techniques if any"
    )


class SpecialistFindings(BaseModel):
    """
    Unified output structure for all Tier2 specialists.

    Only one of the specialist-specific fields will be populated
    based on specialist_type.
    """
    specialist_type: SpecialistType

    # Specialist-specific findings (only one populated)
    topic_classification: Optional[TopicClassification] = None
    entity_enrichment: Optional[EntityEnrichment] = None
    financial_metrics: Optional[FinancialMetrics] = None
    geopolitical_metrics: Optional[GeopoliticalMetrics] = None
    sentiment_metrics: Optional[SentimentMetrics] = None
    political_bias: Optional[PoliticalBiasMetrics] = None
    narrative_frame_metrics: Optional[NarrativeFrameMetrics] = None

    # Metadata
    tokens_used: int = Field(..., ge=0)
    cost_usd: float = Field(..., ge=0.0)
    model: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "specialist_type": "TOPIC_CLASSIFIER",
                "topic_classification": {
                    "topics": [
                        {
                            "topic": "Bitcoin Analysis",
                            "parent_topic": "Economics and Finance",
                            "confidence": 0.95
                        }
                    ]
                },
                "tokens_used": 1200,
                "cost_usd": 0.00004,
                "model": "gemini-2.0-flash-exp"
            }
        }
