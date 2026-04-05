# services/clustering-service/app/schemas/events.py
"""Pydantic schemas for RabbitMQ events."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class Tier0Data(BaseModel):
    """Tier0 triage results from content-analysis-v3."""
    keep: Optional[bool] = None
    priority_score: Optional[int] = None
    category: Optional[str] = None  # CONFLICT, FINANCE, POLITICS, etc.
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    model: Optional[str] = None


class Tier1Data(BaseModel):
    """Tier1 analysis results from content-analysis-v3."""
    impact_score: Optional[float] = None
    credibility_score: Optional[float] = None
    urgency_score: Optional[float] = None
    entities: Optional[List[Dict[str, Any]]] = None
    relations: Optional[List[Dict[str, Any]]] = None
    topics: Optional[List[Dict[str, Any]]] = None


class AnalysisCompletedPayload(BaseModel):
    """Payload from analysis.v3.completed event."""
    article_id: UUID
    title: Optional[str] = None  # Can be missing from some producers
    embedding: Optional[List[float]] = None  # Can be None if embedding generation failed
    entities: Optional[List[Dict[str, Any]]] = None
    sentiment: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    tension_level: Optional[float] = None  # Legacy field (rarely sent)
    tier0: Optional[Tier0Data] = None  # Tier0 triage results (includes category)
    tier1: Optional[Tier1Data] = None  # Tier1 scores from content-analysis-v3
    published_at: Optional[datetime] = None
    simhash_fingerprint: Optional[int] = None

    @field_validator('entities', mode='before')
    @classmethod
    def convert_empty_dict_to_list(cls, v):
        """Convert empty dict {} to empty list [] for entities field."""
        if isinstance(v, dict) and len(v) == 0:
            return []
        return v

    def calculate_tension(self) -> Optional[float]:
        """
        Calculate tension level from available scores.

        Tension is computed as weighted average of urgency and impact:
        - urgency_score (60% weight) - time sensitivity
        - impact_score (40% weight) - significance

        Returns:
            Float 0-10 if scores available, None otherwise
        """
        # Use explicit tension_level if provided
        if self.tension_level is not None:
            return self.tension_level

        # Calculate from tier1 scores if available
        if self.tier1:
            urgency = self.tier1.urgency_score
            impact = self.tier1.impact_score

            if urgency is not None and impact is not None:
                # Weighted average: urgency is more indicative of tension
                return round(0.6 * urgency + 0.4 * impact, 2)

            # Fallback to single score if only one available
            if urgency is not None:
                return urgency
            if impact is not None:
                return impact

        return None


class ClusterCreatedPayload(BaseModel):
    """Payload for cluster.created event."""
    cluster_id: UUID
    title: str
    article_id: UUID
    article_count: int = 1


class ClusterUpdatedPayload(BaseModel):
    """Payload for cluster.updated event."""
    cluster_id: UUID
    article_id: UUID
    article_count: int
    tension_score: Optional[float] = None
    is_breaking: bool = False
    primary_entities: Optional[List[Dict[str, Any]]] = None
    similarity_score: float


class ClusterBurstPayload(BaseModel):
    """Payload for cluster.burst_detected event."""
    cluster_id: UUID
    title: str
    article_count: int
    growth_rate: float
    tension_score: float
    detection_method: str = "frequency_spike"
    top_entities: Optional[List[str]] = None
    recommended_action: str = "immediate_alert"
