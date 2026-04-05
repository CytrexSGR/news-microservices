"""
Narrative Cluster Model - Grouped narrative frames
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class NarrativeCluster(Base):
    """
    Cluster of related narrative frames
    Tracks dominant narrative patterns over time
    """
    __tablename__ = "narrative_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    dominant_frame = Column(String(50), nullable=False)  # Most common frame type
    frame_count = Column(Integer, default=0)
    bias_score = Column(Float, nullable=True)  # -1 (left) to +1 (right)
    keywords = Column(ARRAY(String), nullable=True)
    entities = Column(JSONB, nullable=True)
    sentiment = Column(Float, nullable=True)  # -1 (negative) to +1 (positive)
    perspectives = Column(JSONB, nullable=True)  # Different viewpoints
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_narrative_clusters_dominant_frame', 'dominant_frame'),
    )

    def __repr__(self):
        return f"<NarrativeCluster(id={self.id}, name={self.name}, dominant_frame={self.dominant_frame})>"
