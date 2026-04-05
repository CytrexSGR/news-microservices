"""
Intelligence Event Model
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, Float, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class IntelligenceEvent(Base):
    """
    Normalized RSS event for intelligence analysis
    """
    __tablename__ = "intelligence_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False, index=True)
    description = Column(Text)
    source = Column(Text, nullable=False, index=True)
    source_url = Column(Text)
    published_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    ingested_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Clustering
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("intelligence_clusters.id", ondelete="SET NULL"), index=True)

    # AI Analysis
    confidence = Column(Float)
    bias_score = Column(Float)
    sentiment = Column(Float)

    # Metadata
    entities = Column(JSONB)  # {"persons": [...], "organizations": [...], "locations": [...]}
    keywords = Column(ARRAY(Text))
    language = Column(String(10))
    category = Column(String(50), index=True)  # From v3_analysis.tier0.category

    # Relationships
    cluster = relationship("IntelligenceCluster", back_populates="events")
    propaganda_patterns = relationship("NarrativePropagandaPattern", back_populates="event")
    frame_associations = relationship("NarrativeFrameEvent", back_populates="event")

    # Constraints
    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="valid_confidence"),
        CheckConstraint("bias_score IS NULL OR (bias_score >= -1 AND bias_score <= 1)", name="valid_bias"),
        CheckConstraint("sentiment IS NULL OR (sentiment >= -1 AND sentiment <= 1)", name="valid_sentiment"),
    )

    def __repr__(self):
        return f"<IntelligenceEvent(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"
