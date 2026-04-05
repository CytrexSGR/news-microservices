"""
Admiralty Code configuration models.

Provides configurable thresholds for A-F reliability ratings based on quality scores.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.feed import Base


class AdmiraltyCodeThreshold(Base):
    """
    Admiralty Code threshold configuration.

    Defines min_score thresholds for A-F reliability ratings.
    Example: A=90, B=75, C=60, D=40, E=20, F=0

    Based on NATO Admiralty Code system for intelligence source reliability.
    """
    __tablename__ = "admiralty_code_thresholds"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Admiralty Code (A-F)
    code: Mapped[str] = mapped_column(String(1), unique=True, nullable=False, index=True)

    # Human-readable label
    label: Mapped[str] = mapped_column(String(50), nullable=False)

    # Minimum quality score for this rating (0-100)
    min_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Detailed description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # UI color (for badge display)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<AdmiraltyCodeThreshold(code={self.code}, label={self.label}, min_score={self.min_score})>"


class QualityScoreWeight(Base):
    """
    Quality score category weights configuration.

    Defines weights for different categories in quality score calculation:
    - credibility: Credibility tier assessment
    - editorial: Editorial standards evaluation
    - trust: External trust ratings
    - health: Operational health metrics

    Weights must sum to 1.00 (100%)
    """
    __tablename__ = "quality_score_weights"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Category name (unique)
    category: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Weight value (0.00 - 1.00)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Valid range for this weight
    min_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default='0.00')
    max_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default='1.00')

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('weight >= min_value AND weight <= max_value', name='ck_quality_score_weights_range'),
    )

    def __repr__(self) -> str:
        return f"<QualityScoreWeight(category={self.category}, weight={self.weight})>"
