"""
RabbitMQ event tracking models.

Tracks message routing and event processing across all microservices.
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EventType(str, Enum):
    """Types of system events."""
    FEED_FETCHED = "feed.fetched"
    ARTICLE_CREATED = "article.created"
    ARTICLE_SCRAPED = "article.scraped"
    ANALYSIS_REQUESTED = "analysis.requested"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    NOTIFICATION_SENT = "notification.sent"
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"


class EventStatus(str, Enum):
    """Event processing status."""
    PUBLISHED = "published"
    CONSUMED = "consumed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Event log for RabbitMQ message tracking.

    Provides observability into message routing and processing.
    """

    __tablename__ = "events"

    # Event identification
    event_type = Column(String(100), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)

    # Event data
    payload = Column(JSONB, nullable=False)

    # Routing information
    exchange = Column(String(100), nullable=False)
    routing_key = Column(String(200), nullable=False)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Processing status
    status = Column(String(20), default=EventStatus.PUBLISHED.value, nullable=False, index=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Service information
    producer_service = Column(String(100), nullable=False)
    consumer_service = Column(String(100), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_stacktrace = Column(Text, nullable=True)

    # Timestamps
    published_at = Column(String(255), nullable=False, index=True)  # UTC datetime
    consumed_at = Column(String(255), nullable=True)  # UTC datetime

    # Indexes
    __table_args__ = (
        Index('idx_event_type_status', 'event_type', 'status'),
        Index('idx_event_published_at', 'published_at'),
        Index('idx_event_correlation', 'correlation_id'),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.event_type}, status={self.status})>"
