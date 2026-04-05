"""
Scheduler service models.
"""

import enum
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class JobType(str, enum.Enum):
    """Analysis job types"""
    CATEGORIZATION = "categorization"
    FINANCE_SENTIMENT = "finance_sentiment"
    GEOPOLITICAL_SENTIMENT = "geopolitical_sentiment"
    SUMMARY = "summary"
    ENTITIES = "entities"
    TOPICS = "topics"
    STANDARD_SENTIMENT = "standard_sentiment"
    OSINT_ANALYSIS = "osint_analysis"  # Only for scraped content (item_scraped events)


class JobStatus(str, enum.Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedScheduleState(Base):
    """
    Tracks scheduler state for each feed.

    Prevents duplicate processing and maintains last-checked timestamps.
    """

    __tablename__ = "feed_schedule_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_article_processed_at = Column(DateTime(timezone=True), nullable=True)
    total_articles_processed = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FeedScheduleState feed_id={self.feed_id} last_checked={self.last_checked_at}>"


class AnalysisJobQueue(Base):
    """
    Queue for analysis jobs.

    Supports prioritization, retries, and concurrent processing.
    """

    __tablename__ = "analysis_job_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)

    priority = Column(Integer, default=5, index=True)  # 1-10, higher = more important
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AnalysisJob {self.job_type} article={self.article_id} status={self.status}>"
