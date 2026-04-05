"""
Daily Briefing Model
"""
from sqlalchemy import Column, Date, Text, TIMESTAMP, Float, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base


class IntelligenceBriefing(Base):
    """
    Daily automated briefing (Lagebild)
    """
    __tablename__ = "intelligence_briefings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, unique=True, index=True)

    # Content
    summary = Column(Text)
    global_risk_index = Column(Float)
    risk_delta = Column(Float)

    # Structured Data
    top_clusters = Column(JSONB)  # Array of cluster summaries
    regional_highlights = Column(JSONB)
    market_implications = Column(JSONB)

    # Metadata
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    version = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("date", name="unique_briefing_date"),
    )

    def __repr__(self):
        return f"<Briefing(date={self.date}, risk_index={self.global_risk_index})>"
