"""
CrawlSession model for web crawler support.

Tracks crawl operations: seed URL, visited pages, status, and metadata.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.feed import Base
from app.utils.database_types import JSONBType


class CrawlSession(Base):
    """
    Tracks a single web crawl session.

    A crawl session starts from a seed_url, optionally guided by a topic,
    and tracks all visited URLs and scraped pages.
    """
    __tablename__ = "crawl_sessions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Link to feed (optional — ad-hoc crawls may not have a feed)
    feed_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feeds.id", ondelete="CASCADE"),
        nullable=True
    )

    # Crawl configuration
    seed_url: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), server_default="active", nullable=False)
    pages_scraped: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    visited_urls: Mapped[Optional[dict]] = mapped_column(JSONBType, server_default="[]")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Flexible metadata (config, stats, errors, etc.)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONBType, server_default="{}")

    # Relationships
    feed: Mapped[Optional["Feed"]] = relationship("Feed")

    def __repr__(self) -> str:
        return f"<CrawlSession(id={self.id}, seed_url={self.seed_url[:50]}, status={self.status})>"
