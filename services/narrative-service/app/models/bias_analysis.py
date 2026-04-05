"""
Bias Analysis Model - Source/article bias scores
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class BiasAnalysis(Base):
    """
    Bias analysis for individual events/articles

    Bias labels:
    - left: Strong left bias
    - center-left: Moderate left bias
    - center: Neutral/balanced
    - center-right: Moderate right bias
    - right: Strong right bias
    """
    __tablename__ = "bias_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source = Column(String(255), nullable=True)
    bias_score = Column(Float, nullable=False)  # -1 (left) to +1 (right)
    bias_label = Column(String(20), nullable=True)
    sentiment = Column(Float, nullable=False)  # -1 (negative) to +1 (positive)
    language_indicators = Column(JSONB, nullable=True)  # Emotional words, loaded language
    perspective = Column(String(50), nullable=True)  # pro, con, neutral
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_bias_analysis_event_id', 'event_id'),
        Index('idx_bias_analysis_bias_label', 'bias_label'),
    )

    def __repr__(self):
        return f"<BiasAnalysis(id={self.id}, bias_label={self.bias_label}, bias_score={self.bias_score})>"
