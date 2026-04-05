"""Database utilities and session management for News MCP microservices."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import MetaData, create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

# Naming convention for database constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class BaseModel(DeclarativeBase):
    """Base model class for all database models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Common attributes for all models can be added here
    __abstract__ = True

    def dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Log SQL statements
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections above pool_size
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
        """
        self.database_url = database_url or settings.postgres_url
        self.echo = echo or settings.postgres_echo_sql

        # Async engine for async operations
        self.async_engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
        )

        # Async session factory
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Sync engine for migrations and sync operations
        sync_url = self.database_url.replace("+asyncpg", "")
        self.sync_engine = create_engine(
            sync_url,
            echo=self.echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )

        # Sync session factory
        self.sync_session_factory = sessionmaker(
            self.sync_engine,
            expire_on_commit=False,
        )

    async def create_all(self) -> None:
        """Create all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Database tables created")

    async def drop_all(self) -> None:
        """Drop all database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.drop_all)
            logger.warning("Database tables dropped")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_sync_session(self) -> Session:
        """Get sync database session."""
        return self.sync_session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connections."""
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        logger.info("Database connections closed")

    async def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            async with self.async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def init_db(
    database_url: Optional[str] = None,
    service_name: Optional[str] = None,
    **kwargs
) -> DatabaseManager:
    """Initialize database manager.

    Args:
        database_url: Database connection URL
        service_name: Service name to use service-specific database
        **kwargs: Additional arguments for DatabaseManager
    """
    global _db_manager

    # Use service-specific database if service_name provided
    if service_name and not database_url:
        db_name = settings.get_service_database(service_name)
        database_url = settings.postgres_url.rsplit("/", 1)[0] + f"/{db_name}"

    _db_manager = DatabaseManager(database_url=database_url, **kwargs)
    logger.info(f"Database manager initialized for: {database_url}")
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


# Connection pool monitoring
def setup_pool_monitoring(engine: Any) -> None:
    """Setup connection pool monitoring."""

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new connection."""
        logger.debug(f"New database connection: {id(dbapi_conn)}")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout."""
        logger.debug(f"Connection checked out: {id(dbapi_conn)}")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection checkin."""
        logger.debug(f"Connection checked in: {id(dbapi_conn)}")


# Transaction utilities
class TransactionManager:
    """Manage database transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.savepoint_counter = 0

    async def begin(self) -> None:
        """Begin transaction."""
        await self.session.begin()

    async def commit(self) -> None:
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.session.rollback()

    async def savepoint(self, name: Optional[str] = None) -> str:
        """Create savepoint."""
        if not name:
            self.savepoint_counter += 1
            name = f"sp_{self.savepoint_counter}"
        await self.session.execute(f"SAVEPOINT {name}")
        return name

    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to savepoint."""
        await self.session.execute(f"ROLLBACK TO SAVEPOINT {name}")

    async def release_savepoint(self, name: str) -> None:
        """Release savepoint."""
        await self.session.execute(f"RELEASE SAVEPOINT {name}")


# Export convenience items
__all__ = [
    "BaseModel",
    "DatabaseManager",
    "init_db",
    "get_db_manager",
    "get_db_session",
    "TransactionManager",
    "setup_pool_monitoring",
]