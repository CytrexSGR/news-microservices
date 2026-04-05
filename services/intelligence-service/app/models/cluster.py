"""
Intelligence Cluster Model
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class IntelligenceCluster(Base):
    """
    Cluster of related intelligence events
    """
    __tablename__ = "intelligence_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text)

    # Metrics
    event_count = Column(Integer, default=0)
    risk_score = Column(Float)
    risk_delta = Column(Float)  # Change from last week
    confidence = Column(Float)

    # Metadata
    keywords = Column(ARRAY(Text))
    top_sources = Column(JSONB)  # [{"name": "Reuters", "count": 87, "bias": 0.1}]

    # Lifecycle
    first_seen = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)

    # Categories
    category = Column(String(50), index=True)  # geo, finance, tech, security
    region = Column(ARRAY(Text))  # ["Europe", "Middle East"]
    time_window = Column(String(20), index=True)  # 1h, 6h, 12h, 24h, week, month

    # Relationships
    events = relationship("IntelligenceEvent", back_populates="cluster")
    risk_history = relationship("IntelligenceRiskHistory", back_populates="cluster", cascade="all, delete-orphan")
    propaganda_patterns = relationship("NarrativePropagandaPattern", back_populates="cluster")

    def __repr__(self):
        return f"<IntelligenceCluster(id={self.id}, name='{self.name}', events={self.event_count})>"
