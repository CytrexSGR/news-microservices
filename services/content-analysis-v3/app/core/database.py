"""
Database connection management for Content-Analysis-V3
"""

import asyncpg
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database pool
_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> asyncpg.Pool:
    """
    Initialize database connection pool.

    Returns:
        asyncpg.Pool connection pool
    """
    global _db_pool

    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=2,
            max_size=10,
            command_timeout=60
        )

    return _db_pool


async def close_db_pool():
    """Close database connection pool."""
    global _db_pool

    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None


async def get_db_pool() -> asyncpg.Pool:
    """
    FastAPI dependency for database pool.

    Returns:
        asyncpg.Pool connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    global _db_pool

    if _db_pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")

    return _db_pool


async def check_db_health() -> dict:
    """
    Check database connection health.

    Returns:
        dict with status, latency_ms, pool_size, pool_free
    """
    global _db_pool
    import time

    if _db_pool is None:
        return {
            "status": "unhealthy",
            "error": "Pool not initialized",
            "pool_size": 0,
            "pool_free": 0
        }

    try:
        start = time.monotonic()
        async with _db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        latency_ms = (time.monotonic() - start) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "pool_size": _db_pool.get_size(),
            "pool_free": _db_pool.get_idle_size()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_size": _db_pool.get_size() if _db_pool else 0,
            "pool_free": _db_pool.get_idle_size() if _db_pool else 0
        }
