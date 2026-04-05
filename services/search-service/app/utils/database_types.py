"""
Database type decorators for cross-database compatibility.

Provides types that work with both PostgreSQL (production) and SQLite (tests).
"""
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import TSVECTOR


class TSVectorType(TypeDecorator):
    """
    Database-agnostic TSVECTOR type.

    Uses TSVECTOR for PostgreSQL (full-text search support)
    and TEXT for SQLite (testing compatibility).

    Note: SQLite doesn't support PostgreSQL's full-text search,
    but this allows tests to run. Production uses PostgreSQL.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load appropriate type based on database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(TSVECTOR())
        else:
            # For SQLite and other databases, use TEXT
            return dialect.type_descriptor(Text())
