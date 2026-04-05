"""SQLAlchemy models for SITREP reports.

Maps to the sitrep_reports table created by V001 migration.
Uses SQLAlchemy 2.0 declarative patterns with mapped_column.
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4 as generate_uuid

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator


class JSONBCompatible(TypeDecorator):
    """
    Cross-database JSON type.

    Uses JSONB on PostgreSQL for performance, falls back to JSON for SQLite/others.
    This enables using SQLite for fast in-memory tests while PostgreSQL in production.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class UUIDType(TypeDecorator):
    """
    Cross-database UUID type.

    Uses native UUID on PostgreSQL, falls back to String(36) for SQLite/others.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value) if value else None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        from uuid import UUID
        return UUID(value) if isinstance(value, str) else value


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class SitrepReport(Base):
    """
    SQLAlchemy model for SITREP reports.

    Maps to sitrep_reports table from V001 migration.

    Table schema:
    - id: UUID primary key
    - report_date: Date of the report
    - report_type: Type (daily, weekly, breaking)
    - title: Report title
    - content_markdown: Full content in Markdown
    - content_html: Optional HTML version
    - top_stories: JSONB array of story data
    - key_entities: JSONB array of entities
    - sentiment_summary: JSONB sentiment analysis
    - emerging_signals: Optional JSONB signals
    - generation_model: LLM model used
    - generation_time_ms: Generation time in ms
    - articles_analyzed: Count of articles
    - confidence_score: Optional confidence (0-1)
    - human_reviewed: Review status flag
    - created_at: Creation timestamp

    Additional columns (V002 migration):
    - executive_summary: High-level summary
    - prompt_tokens: Tokens used in prompt
    - completion_tokens: Tokens in completion
    """

    __tablename__ = "sitrep_reports"

    # Primary key
    id: Mapped[Any] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=generate_uuid,
    )

    # Report metadata
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(50),
        default="daily",
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured data (cross-database compatible JSON)
    top_stories: Mapped[dict] = mapped_column(JSONBCompatible(), nullable=False)
    key_entities: Mapped[dict] = mapped_column(JSONBCompatible(), nullable=False)
    sentiment_summary: Mapped[dict] = mapped_column(JSONBCompatible(), nullable=False)
    emerging_signals: Mapped[Optional[dict]] = mapped_column(JSONBCompatible(), nullable=True)
    key_developments: Mapped[Optional[dict]] = mapped_column(JSONBCompatible(), nullable=True)

    # Generation metadata
    generation_model: Mapped[str] = mapped_column(String(100), nullable=False)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_analyzed: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quality metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SitrepReport(id={self.id}, "
            f"report_date={self.report_date}, "
            f"type={self.report_type})>"
        )
