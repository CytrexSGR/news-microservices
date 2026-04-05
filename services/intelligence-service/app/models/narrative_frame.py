"""
Narrative Frame Models
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class NarrativeFrame(Base):
    """
    Detected narrative frame
    """
    __tablename__ = "narrative_frames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frame = Column(Text, nullable=False)  # "Western defense support"
    description = Column(Text)

    # Metrics
    prevalence = Column(Float)  # 0.0-1.0
    confidence = Column(Float)
    sentiment = Column(Float)

    # Associations
    clusters = Column(ARRAY(UUID(as_uuid=True)))  # Array of cluster IDs
    keywords = Column(ARRAY(Text))

    # Sources
    sources = Column(JSONB)  # [{"name": "Reuters", "count": 87}]

    # Lifecycle
    first_detected = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    event_associations = relationship("NarrativeFrameEvent", back_populates="frame")

    def __repr__(self):
        return f"<NarrativeFrame(id={self.id}, frame='{self.frame}', prevalence={self.prevalence})>"


class NarrativeFrameEvent(Base):
    """
    Association between frames and events (M:N)
    """
    __tablename__ = "narrative_frame_events"

    frame_id = Column(UUID(as_uuid=True), ForeignKey("narrative_frames.id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("intelligence_events.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    frame = relationship("NarrativeFrame", back_populates="event_associations")
    event = relationship("IntelligenceEvent", back_populates="frame_associations")

    def __repr__(self):
        return f"<FrameEvent(frame={self.frame_id}, event={self.event_id})>"
