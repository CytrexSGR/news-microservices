"""
Database session management for Feed Service
"""
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.models.feed import Base


# Synchronous engine for migrations and some operations
engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

# Lazy-initialized async engine (avoids creating connection pool in Celery fork workers)
_async_engine = None
_async_session_factory = None


def _get_async_engine():
    """Get or create async engine (lazy initialization for fork-safety)"""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )
    return _async_engine


def _get_async_session_factory():
    """Get or create async session factory (lazy initialization)"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


class _AsyncEngineProxy:
    """Proxy that lazily initializes the async engine"""
    def __getattr__(self, name):
        return getattr(_get_async_engine(), name)

    def begin(self):
        return _get_async_engine().begin()

    def dispose(self):
        return _get_async_engine().dispose()


class _AsyncSessionProxy:
    """Proxy that lazily initializes the async session factory"""
    def __call__(self, *args, **kwargs):
        return _get_async_session_factory()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(_get_async_session_factory(), name)


# Backwards-compatible: lazily initialized
async_engine = _AsyncEngineProxy()
AsyncSessionLocal = _AsyncSessionProxy()

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for synchronous database sessions.

    Usage in FastAPI:
        @app.get("/feeds")
        def get_feeds(db: Session = Depends(get_db)):
            return db.query(Feed).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for asynchronous database sessions.

    Usage in FastAPI:
        @app.get("/feeds")
        async def get_feeds(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Feed))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db() -> None:
    """
    Initialize database tables.

    This should be called during application startup to ensure
    all tables exist. In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


async def init_async_db() -> None:
    """
    Initialize database tables asynchronously.

    This should be called during application startup to ensure
    all tables exist. In production, use Alembic migrations instead.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)