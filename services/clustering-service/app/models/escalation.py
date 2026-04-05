"""SQLAlchemy models for escalation tracking.

This module provides ORM models for the Intelligence Interpretation Layer:
- EscalationAnchor: Reference anchor points for escalation level detection
- FMPNewsCorrelation: Correlations between FMP regime states and news escalation

These models map to tables created by migrations 025, 026, and 027.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.cluster import Base


class EscalationDomain(str, Enum):
    """Escalation analysis domains."""

    GEOPOLITICAL = "geopolitical"
    MILITARY = "military"
    ECONOMIC = "economic"


class CorrelationType(str, Enum):
    """Types of FMP-news correlations."""

    CONFIRMATION = "CONFIRMATION"
    DIVERGENCE = "DIVERGENCE"
    EARLY_WARNING = "EARLY_WARNING"


class FMPRegime(str, Enum):
    """FMP market regime states."""

    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    TRANSITIONAL = "TRANSITIONAL"


class EscalationAnchor(Base):
    """Reference anchor points for escalation level detection.

    Used for embedding similarity comparison to determine escalation levels.
    Each anchor represents a known escalation state (e.g., "diplomatic protest",
    "military mobilization") at a specific level (1-5) within a domain.

    Attributes:
        id: Unique identifier (UUID)
        domain: One of 'geopolitical', 'military', 'economic'
        level: Escalation level 1-5 (1=low, 5=critical)
        label: Human-readable label for this anchor
        reference_text: Full reference text describing this escalation state
        embedding: 1536-dimensional vector (OpenAI ada-002 embedding)
        keywords: Array of keywords associated with this anchor
        weight: Weighting factor for this anchor (default 1.0)
        is_active: Whether this anchor is active for matching
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "escalation_anchors"

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=False)
    keywords: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), server_default="{}"
    )
    weight: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), server_default="1.0"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "domain IN ('geopolitical', 'military', 'economic')",
            name="chk_anchor_domain",
        ),
        CheckConstraint("level BETWEEN 1 AND 5", name="chk_anchor_level"),
        UniqueConstraint(
            "domain", "level", "label", name="uq_anchor_domain_level_label"
        ),
        Index(
            "idx_escalation_anchors_lookup",
            "domain",
            "level",
            postgresql_where="is_active = true",
        ),
    )

    def __repr__(self) -> str:
        return f"<EscalationAnchor {self.domain}:{self.level}:{self.label}>"


class FMPNewsCorrelation(Base):
    """Correlations between FMP regime states and news escalation.

    Tracks detected correlations and divergences between market conditions
    (from FMP service) and news escalation levels. Used for generating
    early warning alerts when news and market signals diverge.

    Attributes:
        id: Unique identifier (UUID)
        detected_at: When this correlation was detected
        correlation_type: CONFIRMATION, DIVERGENCE, or EARLY_WARNING
        fmp_regime: Current FMP market regime (RISK_ON, RISK_OFF, TRANSITIONAL)
        escalation_level: News escalation level at time of detection (1-5)
        confidence: Confidence score for this correlation (0.000-1.000)
        related_clusters: Array of cluster IDs related to this correlation
        metadata: Additional JSON metadata (VIX levels, signal details, etc.)
        expires_at: When this correlation alert expires
        is_active: Whether this correlation is still active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "fmp_news_correlations"

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    correlation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    fmp_regime: Mapped[str] = mapped_column(String(20), nullable=False)
    escalation_level: Mapped[Optional[int]] = mapped_column(Integer)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3))
    related_clusters: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True))
    )
    # Note: Using 'extra_metadata' instead of 'metadata' which is reserved by SQLAlchemy
    # The actual database column is named 'metadata' via the migration
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "correlation_type IN ('CONFIRMATION', 'DIVERGENCE', 'EARLY_WARNING')",
            name="chk_fmp_correlation_type",
        ),
        CheckConstraint(
            "fmp_regime IN ('RISK_ON', 'RISK_OFF', 'TRANSITIONAL')",
            name="chk_fmp_regime",
        ),
        CheckConstraint(
            "escalation_level IS NULL OR escalation_level BETWEEN 1 AND 5",
            name="chk_fmp_escalation_level",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="chk_fmp_confidence",
        ),
        Index(
            "idx_fmp_correlations_active_type",
            "correlation_type",
            "detected_at",
            postgresql_where="is_active = true",
        ),
        Index(
            "idx_fmp_correlations_regime",
            "fmp_regime",
            "detected_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<FMPNewsCorrelation {self.correlation_type}:{self.fmp_regime}>"
