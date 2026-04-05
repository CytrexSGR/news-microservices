"""
Propaganda Pattern Model
"""
from sqlalchemy import Column, Text, TIMESTAMP, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class NarrativePropagandaPattern(Base):
    """
    Detected propaganda pattern in an event
    """
    __tablename__ = "narrative_propaganda_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    technique = Column(Text, nullable=False, index=True)  # "Loaded Language", "Appeal to Fear"
    event_id = Column(UUID(as_uuid=True), ForeignKey("intelligence_events.id", ondelete="CASCADE"), index=True)

    # Detection
    text_snippet = Column(Text)
    confidence = Column(Float)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Metadata
    source = Column(Text)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("intelligence_clusters.id", ondelete="SET NULL"), index=True)

    # Relationships
    event = relationship("IntelligenceEvent", back_populates="propaganda_patterns")
    cluster = relationship("IntelligenceCluster", back_populates="propaganda_patterns")

    def __repr__(self):
        return f"<PropagandaPattern(technique='{self.technique}', confidence={self.confidence})>"
