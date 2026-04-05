"""
Base models and database configuration for central database.
"""

from datetime import datetime
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import MetaData, create_engine, Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.dialects.postgresql import UUID

import os

# Database connection configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://news_user:news_password@localhost:5433/news_mcp"
)

# Connection pool settings
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    echo=DATABASE_ECHO,
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
metadata = MetaData()
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_db() -> SQLAlchemySession:
    """
    Get database session for dependency injection.

    Usage in FastAPI:
        @router.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.

    Usage:
        with get_db_session() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
