"""
Narrative Frame Model - Individual frame instances
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class NarrativeFrame(Base):
    """
    Individual narrative frame detected in an event

    Frame types:
    - victim: Entity portrayed as victim
    - hero: Entity portrayed as hero/savior
    - threat: Entity portrayed as threat/danger
    - solution: Entity/action portrayed as solution
    - conflict: Conflict framing
    - economic: Economic impact framing
    """
    __tablename__ = "narrative_frames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    frame_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0-1
    text_excerpt = Column(Text, nullable=True)
    entities = Column(JSONB, nullable=True)  # {"persons": [], "organizations": [], "locations": []}
    frame_metadata = Column(JSONB, nullable=True)  # Additional metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_narrative_frames_event_id', 'event_id'),
        Index('idx_narrative_frames_frame_type', 'frame_type'),
        Index('idx_narrative_frames_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NarrativeFrame(id={self.id}, frame_type={self.frame_type}, confidence={self.confidence})>"
