"""
Database models for Search Service
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Index, func, Float
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.utils.database_types import TSVectorType


class ArticleIndex(Base):
    """
    Article index for full-text search.

    Stores indexed article data with tsvector for fast full-text search.
    """
    __tablename__ = "article_indexes"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String, unique=True, nullable=False, index=True)

    # Article data
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String)
    source = Column(String, index=True)
    url = Column(String)
    published_at = Column(DateTime, index=True)

    # Search metadata
    sentiment = Column(String, index=True)  # positive, negative, neutral
    entities = Column(Text)  # JSON string of entities

    # Full-text search vector
    search_vector = Column(TSVectorType)

    # Metadata
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_article_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_article_published_at', 'published_at'),
        Index('idx_article_source', 'source'),
        Index('idx_article_sentiment', 'sentiment'),
    )


class SearchHistory(Base):
    """
    User search history.

    Tracks user searches for analytics and suggestions.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Search details
    query = Column(String, nullable=False)
    filters = Column(Text)  # JSON string of filters
    results_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_search_history_user_id', 'user_id'),
        Index('idx_search_history_created_at', 'created_at'),
    )


class SavedSearch(Base):
    """
    Saved search queries.

    Allows users to save and manage search queries with notifications.
    """
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Search details
    name = Column(String, nullable=False)
    query = Column(String, nullable=False)
    filters = Column(Text)  # JSON string of filters

    # Notification settings
    notifications_enabled = Column(Boolean, default=False)
    last_notified_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_saved_searches_user_id', 'user_id'),
    )


class SearchAnalytics(Base):
    """
    Search analytics.

    Tracks popular queries and click patterns for suggestions.
    """
    __tablename__ = "search_analytics"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False, index=True)

    # Analytics data
    hits = Column(Integer, default=1)
    avg_position = Column(Float)  # Average position of clicked results

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_search_analytics_query', 'query'),
        Index('idx_search_analytics_hits', 'hits'),
    )
