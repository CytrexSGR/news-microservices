"""Pydantic schemas for escalation API responses.

This module defines response schemas for the Intelligence Interpretation Layer
escalation endpoints. Includes domain-level escalation scores, combined metrics,
market regime data, correlation alerts, and cluster-level escalation details.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class DomainEscalationResponse(BaseModel):
    """Escalation data for a single domain.

    Represents the escalation level and score for one of three domains:
    geopolitical, military, or economic.

    Attributes:
        domain: Domain name (geopolitical, military, or economic)
        level: Escalation level 1-5 (1=low, 5=critical)
        score: Normalized score 0.000-1.000
        confidence: Confidence in the assessment (0.0-1.0)
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    domain: str = Field(..., description="Domain: geopolitical, military, or economic")
    level: int = Field(..., ge=1, le=5, description="Escalation level 1-5")
    score: Decimal = Field(..., ge=0, le=1, description="Normalized score 0.000-1.000")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in assessment")

    @field_serializer("score")
    def serialize_score(self, value: Decimal) -> str:
        """Serialize Decimal as string for JSON output."""
        return str(value)


class CorrelationAlertResponse(BaseModel):
    """Active correlation alert.

    Represents a detected correlation between news escalation and market regime.

    Attributes:
        id: Unique alert identifier
        correlation_type: CONFIRMATION, DIVERGENCE, or EARLY_WARNING
        fmp_regime: Current FMP market regime (RISK_ON, RISK_OFF, TRANSITIONAL)
        escalation_level: News escalation level at time of detection (1-5)
        confidence: Confidence score for this correlation
        reasoning: Human-readable explanation of the correlation
        detected_at: When this correlation was detected
        expires_at: When this alert expires
        related_cluster_count: Number of clusters related to this alert
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    correlation_type: str = Field(
        ..., description="CONFIRMATION, DIVERGENCE, or EARLY_WARNING"
    )
    fmp_regime: str = Field(..., description="RISK_ON, RISK_OFF, or TRANSITIONAL")
    escalation_level: int = Field(..., ge=1, le=5)
    confidence: Decimal
    reasoning: Optional[str] = None
    detected_at: datetime
    expires_at: Optional[datetime] = None
    related_cluster_count: int = 0

    @field_serializer("confidence")
    def serialize_confidence(self, value: Decimal) -> str:
        """Serialize Decimal as string for JSON output."""
        return str(value)


class RegimeStateResponse(BaseModel):
    """Current FMP market regime.

    Represents the current state of the market as reported by the FMP service.

    Attributes:
        regime: Current regime (RISK_ON, RISK_OFF, TRANSITIONAL)
        confidence: Confidence in the regime assessment
        vix_level: Current VIX level (if available)
        fear_greed_index: Fear & Greed index 0-100 (if available)
        timestamp: When the regime was last updated
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    regime: str = Field(..., description="RISK_ON, RISK_OFF, or TRANSITIONAL")
    confidence: float = Field(..., ge=0, le=1)
    vix_level: Optional[float] = None
    fear_greed_index: Optional[int] = Field(None, ge=0, le=100)
    timestamp: Optional[datetime] = None


class EscalationSummaryResponse(BaseModel):
    """Complete escalation summary for dashboard.

    Aggregates escalation data across all domains, combined metrics,
    market regime correlation, and active alerts.

    Attributes:
        geopolitical: Geopolitical domain escalation data
        military: Military domain escalation data
        economic: Economic domain escalation data
        combined_level: Maximum of domain levels (1-5)
        combined_score: Average of domain scores
        market_regime: Current FMP market regime (if available)
        correlation_alerts: List of active correlation alerts
        cluster_count: Number of clusters analyzed
        calculated_at: When this summary was calculated
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    # Domain escalation levels
    geopolitical: DomainEscalationResponse
    military: DomainEscalationResponse
    economic: DomainEscalationResponse

    # Combined metrics
    combined_level: int = Field(..., ge=1, le=5, description="Max of domain levels")
    combined_score: Decimal = Field(..., description="Average of domain scores")

    # Market correlation
    market_regime: Optional[RegimeStateResponse] = None
    correlation_alerts: List[CorrelationAlertResponse] = Field(default_factory=list)

    # Metadata
    cluster_count: int = Field(..., description="Number of clusters analyzed")
    calculated_at: datetime

    @field_serializer("combined_score")
    def serialize_combined_score(self, value: Decimal) -> str:
        """Serialize Decimal as string for JSON output."""
        return str(value)


class SignalDetailResponse(BaseModel):
    """Individual signal breakdown for escalation calculation.

    Represents a single signal from one of three sources (embedding, content,
    or keywords) used in the escalation calculation for a cluster.

    Attributes:
        source: Signal source identifier (embedding, content, or keywords)
        level: Escalation level 1-5 contributed by this signal
        confidence: Confidence in this signal's contribution (0.0-1.0)
        matched_anchor_id: UUID of the matched anchor (for embedding/keyword signals)
        matched_keywords: List of matched keywords (for keyword signals)
        reasoning: Human-readable explanation of the signal
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    source: str = Field(..., description="Signal source: embedding, content, or keywords")
    level: int = Field(..., ge=1, le=5, description="Escalation level 1-5")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence 0.0-1.0")
    matched_anchor_id: Optional[UUID] = Field(
        None, description="UUID of matched anchor point"
    )
    matched_keywords: Optional[List[str]] = Field(
        None, description="List of matched keywords"
    )
    reasoning: Optional[str] = Field(None, description="Explanation of signal")


class ClusterEscalationDetailResponse(BaseModel):
    """Detailed escalation data for a single cluster.

    Provides comprehensive escalation information for a specific cluster,
    including domain-level breakdowns and individual signal contributions.

    Attributes:
        cluster_id: UUID of the cluster
        cluster_title: Title/label of the cluster
        article_count: Number of articles in the cluster
        geopolitical: Geopolitical domain escalation
        military: Military domain escalation
        economic: Economic domain escalation
        combined_level: Maximum level across domains (1-5)
        combined_score: Weighted average score
        geopolitical_signals: Signal breakdown for geopolitical domain
        military_signals: Signal breakdown for military domain
        economic_signals: Signal breakdown for economic domain
        escalation_calculated_at: When escalation was last calculated
        created_at: Cluster creation timestamp
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    cluster_id: UUID
    cluster_title: str
    article_count: int

    # Domain breakdowns
    geopolitical: DomainEscalationResponse
    military: DomainEscalationResponse
    economic: DomainEscalationResponse

    # Combined metrics
    combined_level: int = Field(..., ge=1, le=5, description="Max of domain levels")
    combined_score: Decimal = Field(..., description="Average of domain scores")

    # Signal breakdowns per domain
    geopolitical_signals: List[SignalDetailResponse] = Field(default_factory=list)
    military_signals: List[SignalDetailResponse] = Field(default_factory=list)
    economic_signals: List[SignalDetailResponse] = Field(default_factory=list)

    # Metadata
    escalation_calculated_at: Optional[datetime] = None
    created_at: datetime

    @field_serializer("combined_score")
    def serialize_combined_score(self, value: Decimal) -> str:
        """Serialize Decimal as string for JSON output."""
        return str(value)
