"""
Scheduler models for task management and job queuing.

Used by scheduler-service to orchestrate fetch and analysis jobs.
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobType(str, Enum):
    """Analysis job types."""
    CATEGORIZATION = "categorization"
    FINANCE_SENTIMENT = "finance_sentiment"
    GEOPOLITICAL_SENTIMENT = "geopolitical_sentiment"
    STANDARD_SENTIMENT = "standard_sentiment"
    FULL_ANALYSIS = "full_analysis"


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FeedScheduleState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks scheduler state for each feed.

    Prevents duplicate processing and maintains last-checked timestamps.
    """

    __tablename__ = "feed_schedule_state"

    feed_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    last_checked_at = Column(String(255), nullable=True)  # UTC datetime
    last_article_processed_at = Column(String(255), nullable=True)  # UTC datetime
    total_articles_processed = Column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<FeedScheduleState feed_id={self.feed_id} last_checked={self.last_checked_at}>"


class AnalysisJobQueue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Queue for analysis jobs.

    Supports prioritization, retries, and concurrent processing.
    """

    __tablename__ = "analysis_job_queue"

    feed_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default=JobStatus.PENDING.value, nullable=False, index=True)

    priority = Column(Integer, default=5, index=True)  # 1-10, higher = more important
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    error_message = Column(Text, nullable=True)

    started_at = Column(String(255), nullable=True)  # UTC datetime
    completed_at = Column(String(255), nullable=True)  # UTC datetime

    # Indexes
    __table_args__ = (
        Index('idx_job_status_priority', 'status', 'priority'),
        Index('idx_job_article', 'article_id', 'job_type'),
    )

    def __repr__(self) -> str:
        return f"<AnalysisJobQueue {self.job_type} article={self.article_id} status={self.status}>"
