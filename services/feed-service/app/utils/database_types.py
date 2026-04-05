"""
Custom SQLAlchemy types for cross-database compatibility.

Provides types that work with both PostgreSQL and SQLite for testing.
"""
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB


class JSONBType(TypeDecorator):
    """
    Cross-database JSONB type.

    Uses PostgreSQL JSONB in production, JSON for SQLite tests.
    This allows tests to run without PostgreSQL dependency.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load appropriate type based on database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSONB())
        else:
            # Use JSON for SQLite and other databases
            return dialect.type_descriptor(JSON())
