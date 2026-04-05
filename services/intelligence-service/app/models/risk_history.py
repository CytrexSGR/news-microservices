"""
Risk History Model
"""
from sqlalchemy import Column, Date, TIMESTAMP, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class IntelligenceRiskHistory(Base):
    """
    Weekly risk history for trend analysis
    """
    __tablename__ = "intelligence_risk_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("intelligence_clusters.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time window
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)

    # Metrics
    risk_score = Column(Float)
    article_count = Column(Integer)
    avg_sentiment = Column(Float)
    unique_sources = Column(Integer)

    # Deltas
    risk_delta = Column(Float)  # vs previous week
    article_delta = Column(Float)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    cluster = relationship("IntelligenceCluster", back_populates="risk_history")

    # Constraints
    __table_args__ = (
        UniqueConstraint("cluster_id", "week_start", name="unique_cluster_week"),
    )

    def __repr__(self):
        return f"<RiskHistory(cluster={self.cluster_id}, week={self.week_start}, risk={self.risk_score})>"
