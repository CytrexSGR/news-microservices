"""
Event Analysis model for OSINT intelligence extraction.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, Text,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from database.models.base import Base, TimestampMixin


class EventAnalysis(Base, TimestampMixin):
    """
    OSINT Event Analysis results.

    Structured event data extracted from news articles for intelligence analysis.
    Only created for fully scraped articles (≥500 words).
    """

    __tablename__ = "event_analyses"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # FK to feed_items
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.id"),
        nullable=False,
        unique=True
    )

    # Basic event information
    headline = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    publisher_url = Column(String(1000), nullable=True)

    # Primary event classification
    primary_event = Column(Text, nullable=False)
    location = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=True)

    # Actors (JSONB)
    # Format: {
    #   "alleged_attacker": "Russian forces",
    #   "victim": "Ukrainian civilian infrastructure",
    #   "reporting_party": "Kyiv regional administration"
    # }
    actors = Column(JSONB, nullable=False, server_default='{}')

    # Means/Methods (ARRAY)
    # Format: ["drones", "artillery", "missiles"]
    means = Column(ARRAY(Text), nullable=True)

    # Impact (JSONB)
    # Format: {
    #   "trucks_destroyed": 5,
    #   "fatalities": 2,
    #   "injured": 7,
    #   "affected_civilians": 1000,
    #   "infrastructure_damage": "severe"
    # }
    impact = Column(JSONB, nullable=True)

    # Claims (JSONB array)
    # Format: [
    #   {
    #     "statement": "15 trucks were destroyed",
    #     "confidence": "high",
    #     "evidence_ref": "UN official statement",
    #     "attribution": "UN spokesperson"
    #   }
    # ]
    claims = Column(JSONB, nullable=False, server_default='[]')

    # Status/Comments (JSONB)
    # Format: {
    #   "un_comment": "investigating reports",
    #   "russian_comment": "denies attack occurred",
    #   "ukrainian_comment": "confirms attack, provides casualty count"
    # }
    status = Column(JSONB, nullable=True)

    # Risk tags (ARRAY)
    # Format: ["ihl_sensitive", "needs_corroboration", "high_casualty"]
    risk_tags = Column(ARRAY(Text), nullable=False, server_default='{}')

    # Publisher context (JSONB)
    # Format: {
    #   "publisher_bias": "center",
    #   "source_type": "independent_media",
    #   "reliability_score": 0.85
    # }
    publisher_context = Column(JSONB, nullable=True)

    # Summary
    summary = Column(Text, nullable=False)

    # Overall confidence assessment
    confidence_overall = Column(String(20), nullable=False, index=True)
    # Values: "low", "medium", "high"

    # Confidence dimension breakdown (JSONB)
    # Format: {
    #   "source_credibility": "high",
    #   "specificity": "medium",
    #   "counter_statements": "medium",
    #   "corroboration": "high",
    #   "weighted_score": 0.825
    # }
    confidence_dimensions = Column(JSONB, nullable=True)

    # Evidence (JSONB array)
    # Format: [
    #   {
    #     "type": "quote",
    #     "text": "We confirm 15 casualties",
    #     "source": "Regional governor",
    #     "position": 1234
    #   },
    #   {
    #     "type": "photo",
    #     "url": "https://example.com/image.jpg",
    #     "description": "Damaged infrastructure"
    #   }
    # ]
    evidence = Column(JSONB, nullable=True)

    # Relationship to main analysis result
    analysis_result = relationship("AnalysisResult", foreign_keys=[analysis_id])

    # Indexes
    __table_args__ = (
        Index('idx_event_analyses_article_id', 'article_id'),
        Index('idx_event_analyses_risk_tags', 'risk_tags', postgresql_using='gin'),
        Index('idx_event_analyses_confidence', 'confidence_overall'),
        Index('idx_event_analyses_created_at', 'created_at'),
        Index('idx_event_analyses_confidence_created', 'confidence_overall', 'created_at'),
        Index('idx_event_analyses_actors', 'actors', postgresql_using='gin'),
        Index('idx_event_analyses_claims', 'claims', postgresql_using='gin'),
    )

    def has_risk_tag(self, tag: str) -> bool:
        """Check if event has a specific risk tag."""
        return tag in (self.risk_tags or [])

    def get_actor(self, role: str) -> Optional[str]:
        """Get actor by role (alleged_attacker, victim, reporting_party)."""
        return (self.actors or {}).get(role)

    def get_impact_value(self, key: str) -> Optional[Any]:
        """Get impact value by key."""
        return (self.impact or {}).get(key)

    def get_claim_count(self) -> int:
        """Get number of claims."""
        return len(self.claims or [])

    def get_evidence_count(self) -> int:
        """Get number of evidence items."""
        return len(self.evidence or [])

    def is_high_confidence(self) -> bool:
        """Check if event has high confidence."""
        return self.confidence_overall == "high"

    def is_ihl_sensitive(self) -> bool:
        """Check if event is IHL-sensitive (requires special handling)."""
        return self.has_risk_tag("ihl_sensitive")

    def needs_analyst_review(self) -> bool:
        """
        Check if event requires analyst review.

        Criteria:
        - Critical risk tags (ALWAYS require review)
        - High-priority risk tags + low confidence

        Tag categories:
        - Critical: ihl_sensitive, high_casualty, war_crime_allegation, chemical_use, nuclear_facility
        - High-priority: needs_corroboration, mass_displacement, infrastructure_collapse
        - Thematic: drone_strike, missile_attack, etc. (informational only, no review)
        - Compliance: un_statement_required, etc. (procedural only, no review)
        """
        # Critical tags ALWAYS require review (regardless of confidence)
        critical_tags = {
            "ihl_sensitive",
            "high_casualty",
            "war_crime_allegation",
            "chemical_use",
            "nuclear_facility"
        }

        has_critical_tag = any(
            self.has_risk_tag(tag) for tag in critical_tags
        )

        if has_critical_tag:
            return True

        # High-priority risk tags require review when confidence is low
        high_priority_risk_tags = {
            "needs_corroboration",
            "mass_displacement",
            "infrastructure_collapse"
        }

        if self.confidence_overall == "low" and self.risk_tags:
            has_high_priority_tag = any(
                self.has_risk_tag(tag) for tag in high_priority_risk_tags
            )
            return has_high_priority_tag

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "article_id": str(self.article_id),
            "headline": self.headline,
            "source": self.source,
            "publisher_url": self.publisher_url,
            "primary_event": self.primary_event,
            "location": self.location,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "actors": self.actors,
            "means": self.means,
            "impact": self.impact,
            "claims": self.claims,
            "status": self.status,
            "risk_tags": self.risk_tags,
            "publisher_context": self.publisher_context,
            "summary": self.summary,
            "confidence_overall": self.confidence_overall,
            "confidence_dimensions": self.confidence_dimensions,
            "evidence": self.evidence,
            "claim_count": self.get_claim_count(),
            "evidence_count": self.get_evidence_count(),
            "needs_analyst_review": self.needs_analyst_review(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
