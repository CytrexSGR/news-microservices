"""
Database Circuit Breaker for PostgreSQL Connection Pool Protection

Wraps SQLAlchemy DatabaseManager with circuit breaker pattern to prevent cascading
failures during database outages or connection pool exhaustion.

Task 406: Circuit Breaker Pattern (Phase 4)

Key Features:
- Circuit breaker protection for session acquisition
- Connection pool exhaustion protection
- Fast-fail behavior during database outages
- Prometheus metrics for monitoring
- Graceful degradation

Problem Solved:
    When PostgreSQL is down or connection pool is exhausted, services would:
    1. Timeout waiting for connections (30s each)
    2. Queue up requests consuming memory
    3. Eventually crash with OOM or timeout errors
    4. Cascade to dependent services

Circuit Breaker Solution:
    - CLOSED: Normal operation, acquire sessions from pool
    - OPEN: Database down (5+ failures), reject immediately (fail-fast)
    - HALF_OPEN: Test recovery with single session attempt

Before:
    Database down → 10 requests × 30s timeout = 300s blocking
    All connections exhausted → Service crash

After:
    Database down → 5 failures → Circuit OPEN → Instant rejection
    Service remains responsive, returns 503 to clients

Usage:
    from news_mcp_common.resilience import ResilientDatabaseManager, CircuitBreakerConfig

    # Create resilient database manager
    cb_config = CircuitBreakerConfig(
        failure_threshold=5,      # Open after 5 failures
        success_threshold=2,      # Close after 2 successes
        timeout_seconds=60,       # Wait 60s before retry
        enable_metrics=True,
    )

    db_manager = ResilientDatabaseManager(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        circuit_breaker_config=cb_config,
    )

    # Use in FastAPI dependency
    async def get_db():
        try:
            async with db_manager.session() as session:
                yield session
        except CircuitBreakerOpenError:
            raise HTTPException(503, "Database temporarily unavailable")
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .exceptions import CircuitBreakerOpenError
from .types import CircuitBreakerState

logger = logging.getLogger(__name__)


class DatabaseCircuitBreakerError(Exception):
    """Base exception for database circuit breaker errors."""

    pass


class ResilientDatabaseManager:
    """
    Database manager with circuit breaker protection.

    Wraps news_mcp_common.database.DatabaseManager to provide circuit breaker
    protection for session acquisition and connection health checks.

    Circuit Breaker States:
        - CLOSED: Normal operation, sessions acquired from pool
        - OPEN: Database down (5+ failures), sessions rejected immediately
        - HALF_OPEN: Testing recovery with single session attempt

    Protected Operations:
        1. Session Acquisition: `session()` context manager
        2. Connection Health Check: `check_connection()`
        3. Session Generator: `get_session()` (FastAPI dependency)

    Connection Pool Protection:
        - Prevents pool exhaustion during database outages
        - Fast-fail instead of timeout (30s → instant)
        - Maintains service responsiveness during DB downtime

    Example:
        >>> from news_mcp_common.resilience import ResilientDatabaseManager
        >>>
        >>> db_manager = ResilientDatabaseManager(
        ...     database_url="postgresql+asyncpg://localhost/news",
        ...     pool_size=20,
        ...     circuit_breaker_config=CircuitBreakerConfig(
        ...         failure_threshold=5,
        ...         timeout_seconds=60,
        ...     ),
        ... )
        >>>
        >>> # In FastAPI endpoint
        >>> async def create_article(db: AsyncSession = Depends(db_manager.get_session)):
        ...     article = Article(title="Test")
        ...     db.add(article)
        ...     await db.commit()
        ...     return article
        >>>
        >>> # Circuit breaker stats
        >>> stats = db_manager.get_stats()
        >>> print(f"Circuit state: {stats['state']}")
        >>> print(f"Success rate: {1.0 - stats['failure_rate']:.2%}")
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        name: str = "database",
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        """
        Initialize resilient database manager.

        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql+asyncpg://...)
            circuit_breaker_config: Circuit breaker configuration
            circuit_breaker: Existing circuit breaker instance (overrides config)
            name: Circuit breaker name for metrics (e.g., "database", "analytics-db")
            pool_size: SQLAlchemy connection pool size (default: 20)
            max_overflow: Maximum overflow connections (default: 10)
            pool_timeout: Timeout for acquiring connection from pool (default: 30s)
            pool_recycle: Recycle connections after this many seconds (default: 3600s)
            echo: Enable SQLAlchemy query logging (default: False)

        Circuit Breaker Configuration (if not provided):
            - failure_threshold: 5 (open after 5 consecutive failures)
            - success_threshold: 2 (close after 2 successes in HALF_OPEN)
            - timeout_seconds: 60 (wait 60s before attempting recovery)
            - enable_metrics: True (expose Prometheus metrics)
        """
        from news_mcp_common.database import DatabaseManager

        self.name = name
        self.database_url = database_url

        # Circuit breaker setup
        if circuit_breaker:
            self.circuit_breaker = circuit_breaker
        else:
            cb_config = circuit_breaker_config or CircuitBreakerConfig(
                failure_threshold=5,  # Open after 5 consecutive failures
                success_threshold=2,  # Close after 2 successes in HALF_OPEN
                timeout_seconds=60,  # Wait 60s before retry (DB recovery time)
                enable_metrics=True,  # Track circuit state in Prometheus
            )
            self.circuit_breaker = CircuitBreaker(name=name, config=cb_config)

        # Create underlying database manager (from news-mcp-common)
        self._db_manager = DatabaseManager(
            database_url=database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )

        logger.info(
            f"Resilient database manager initialized: {name} "
            f"(pool_size={pool_size}, max_overflow={max_overflow})"
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with circuit breaker protection.

        Context manager for acquiring AsyncSession from connection pool.
        Protected by circuit breaker to prevent pool exhaustion during outages.

        Circuit Breaker Behavior:
            - CLOSED: Acquires session from pool normally
            - OPEN: Raises CircuitBreakerOpenError immediately (fail-fast)
            - HALF_OPEN: Attempts single session acquisition to test recovery

        Returns:
            AsyncSession: SQLAlchemy async session (auto-commit/rollback)

        Raises:
            CircuitBreakerOpenError: If circuit is open (database down)
            Exception: Database connection or query errors

        Example:
            >>> async with db_manager.session() as session:
            ...     result = await session.execute(select(Article))
            ...     articles = result.scalars().all()
            ...     await session.commit()

        FastAPI Integration:
            >>> async def get_db():
            ...     try:
            ...         async with db_manager.session() as session:
            ...             yield session
            ...     except CircuitBreakerOpenError:
            ...         raise HTTPException(503, "Database unavailable")
        """
        # Check circuit breaker state first (fail-fast)
        if self.circuit_breaker.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(
                f"Database circuit breaker is OPEN for '{self.name}' - "
                "refusing to acquire session to prevent pool exhaustion"
            )

        # Attempt to acquire session with circuit breaker protection
        try:
            async with self.circuit_breaker():
                async with self._db_manager.session() as session:
                    yield session
                    # Circuit breaker records success if we reach here

        except CircuitBreakerOpenError:
            # Circuit breaker opened during operation
            logger.error(
                f"Circuit breaker opened for '{self.name}' during session operation"
            )
            raise

        except Exception as e:
            # Database error (connection timeout, query error, etc.)
            # Circuit breaker automatically records failure
            logger.error(f"Database session error for '{self.name}': {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session generator (FastAPI dependency compatible).

        Async generator that yields AsyncSession for use in FastAPI dependencies.
        Equivalent to session() context manager but works with Depends().

        Returns:
            AsyncSession: SQLAlchemy async session

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Database errors

        Example:
            >>> # FastAPI dependency
            >>> async def get_db():
            ...     async for session in db_manager.get_session():
            ...         yield session
            >>>
            >>> # In endpoint
            >>> @app.post("/articles")
            >>> async def create_article(
            ...     article: ArticleCreate,
            ...     db: AsyncSession = Depends(get_db)
            ... ):
            ...     db_article = Article(**article.dict())
            ...     db.add(db_article)
            ...     await db.commit()
            ...     return db_article
        """
        async with self.session() as session:
            yield session

    async def check_connection(self) -> bool:
        """
        Check database connection health with circuit breaker protection.

        Verifies database connectivity by executing simple query (SELECT 1).
        Protected by circuit breaker to avoid timeout storms during outages.

        Returns:
            bool: True if connection works, False if circuit open or connection fails

        Example:
            >>> if await db_manager.check_connection():
            ...     print("Database is healthy")
            ... else:
            ...     print("Database is down or circuit is open")

        Health Check Endpoint:
            >>> @app.get("/health/db")
            >>> async def health_check():
            ...     if await db_manager.check_connection():
            ...         return {"status": "healthy"}
            ...     return {"status": "unhealthy"}, 503
        """
        # Check circuit state first
        if self.circuit_breaker.state == CircuitBreakerState.OPEN:
            logger.warning(
                f"Circuit breaker is OPEN for '{self.name}' - "
                "skipping connection check to prevent timeout"
            )
            return False

        try:
            async with self.circuit_breaker():
                return await self._db_manager.check_connection()

        except CircuitBreakerOpenError:
            logger.error(
                f"Circuit breaker opened for '{self.name}' during health check"
            )
            return False

        except Exception as e:
            logger.error(f"Database health check failed for '{self.name}': {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics for monitoring.

        Returns detailed metrics about circuit breaker state, failure rates,
        and connection pool health. Use for Prometheus metrics, dashboards,
        or operational monitoring.

        Returns:
            dict: Statistics including:
                - state: Current circuit breaker state (CLOSED/OPEN/HALF_OPEN)
                - total_successes: Cumulative successful session acquisitions
                - total_failures: Cumulative failed session acquisitions
                - total_rejections: Sessions rejected due to open circuit
                - failure_rate: Current failure rate (0.0-1.0)
                - last_failure_time: Timestamp of last failure
                - last_state_change_time: When circuit breaker last changed state
                - name: Circuit breaker name

        Example:
            >>> stats = db_manager.get_stats()
            >>> print(f"Circuit state: {stats['state']}")
            >>> # CircuitBreakerState.CLOSED
            >>>
            >>> print(f"Success rate: {1.0 - stats['failure_rate']:.2%}")
            >>> # Success rate: 99.50%
            >>>
            >>> print(f"Total rejections: {stats['total_rejections']}")
            >>> # Total rejections: 0

        Prometheus Integration:
            >>> from prometheus_client import Gauge
            >>>
            >>> # Expose as metrics
            >>> stats = db_manager.get_stats()
            >>> circuit_state_gauge.labels(name=stats['name']).set(
            ...     1 if stats['state'] == CircuitBreakerState.CLOSED else 0
            ... )
        """
        stats = self.circuit_breaker.get_stats()
        stats["name"] = self.name
        return stats

    async def reset(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        Forces circuit breaker to CLOSED state, allowing session acquisition
        attempts to resume. Use after fixing database issues or for
        administrative overrides.

        Use Cases:
            - After resolving database outage
            - After scaling up database resources
            - Emergency override for critical operations
            - Testing/debugging

        Warning:
            Resetting circuit breaker during actual database outage will
            cause failure spike until circuit opens again naturally.

        Example:
            >>> # After fixing database issues
            >>> await db_manager.reset()
            >>> logger.info("Database circuit breaker manually reset")
            >>>
            >>> # Verify connection works
            >>> if await db_manager.check_connection():
            ...     logger.info("Database connection restored")

        Admin Endpoint:
            >>> @app.post("/admin/circuit-breaker/reset")
            >>> async def reset_circuit_breaker(admin: User = Depends(require_admin)):
            ...     await db_manager.reset()
            ...     return {"message": "Circuit breaker reset to CLOSED"}
        """
        await self.circuit_breaker.reset()
        logger.info(f"Circuit breaker manually reset to CLOSED for '{self.name}'")

    async def close(self) -> None:
        """
        Close database connections and dispose engine.

        Gracefully shuts down connection pool and disposes SQLAlchemy engine.
        Call during application shutdown to release database connections.

        Example:
            >>> # In FastAPI lifespan
            >>> @app.on_event("shutdown")
            >>> async def shutdown_event():
            ...     await db_manager.close()
            ...     logger.info("Database connections closed")
        """
        await self._db_manager.close()
        logger.info(f"Database connections closed for '{self.name}'")

    # Delegate other methods to underlying DatabaseManager

    async def create_all(self) -> None:
        """Create all database tables (delegated to underlying manager)."""
        await self._db_manager.create_all()

    async def drop_all(self) -> None:
        """Drop all database tables (delegated to underlying manager)."""
        await self._db_manager.drop_all()

    @property
    def async_engine(self):
        """Get underlying async engine (for advanced operations)."""
        return self._db_manager.async_engine

    @property
    def sync_engine(self):
        """Get underlying sync engine (for migrations)."""
        return self._db_manager.sync_engine


def create_resilient_database_manager(
    database_url: Optional[str] = None,
    name: str = "database",
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    **kwargs,
) -> ResilientDatabaseManager:
    """
    Factory function to create resilient database manager.

    Convenience function for creating ResilientDatabaseManager with
    sensible defaults. Use when you need circuit breaker protection
    for database operations.

    Args:
        database_url: PostgreSQL connection URL
        name: Circuit breaker name for metrics
        circuit_breaker_config: Circuit breaker configuration
        **kwargs: Additional DatabaseManager arguments

    Returns:
        ResilientDatabaseManager: Configured database manager

    Example:
        >>> from news_mcp_common.resilience import create_resilient_database_manager
        >>>
        >>> db_manager = create_resilient_database_manager(
        ...     database_url="postgresql+asyncpg://localhost/news",
        ...     name="news-db",
        ...     pool_size=30,
        ...     max_overflow=20,
        ... )
        >>>
        >>> async with db_manager.session() as session:
        ...     result = await session.execute(select(Article))
        ...     articles = result.scalars().all()
    """
    return ResilientDatabaseManager(
        database_url=database_url,
        name=name,
        circuit_breaker_config=circuit_breaker_config,
        **kwargs,
    )


__all__ = [
    "ResilientDatabaseManager",
    "DatabaseCircuitBreakerError",
    "create_resilient_database_manager",
]
