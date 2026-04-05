"""
Source Bias Model
"""
from sqlalchemy import Column, Text, TIMESTAMP, Integer, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class NarrativeSourceBias(Base):
    """
    Bias rating for news sources
    """
    __tablename__ = "narrative_source_bias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Text, nullable=False, unique=True, index=True)

    # Bias Metrics
    avg_bias = Column(Float)  # -1.0 (left) to +1.0 (right)
    bias_variance = Column(Float)
    confidence = Column(Float)

    # Metadata
    article_count = Column(Integer, default=0)
    first_analyzed = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Manual overrides (if needed)
    manual_bias = Column(Float)
    manual_rating_date = Column(TIMESTAMP(timezone=True))
    manual_rating_source = Column(Text)

    __table_args__ = (
        UniqueConstraint("source", name="unique_source_bias"),
    )

    def __repr__(self):
        return f"<SourceBias(source='{self.source}', bias={self.avg_bias})>"
