# Database Circuit Breaker Integration Guide

**Task 406: Circuit Breaker Pattern (Phase 4)**

This guide shows how to integrate the database circuit breaker into microservices for PostgreSQL connection pool protection.

---

## Table of Contents

1. [Why Use Database Circuit Breaker](#why-use-database-circuit-breaker)
2. [Quick Start](#quick-start)
3. [Integration Patterns](#integration-patterns)
4. [Configuration](#configuration)
5. [Monitoring & Metrics](#monitoring--metrics)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Why Use Database Circuit Breaker

### Problem Without Circuit Breaker

When PostgreSQL is down or connection pool is exhausted:

```
Request 1 → Wait 30s for connection → Timeout → Error
Request 2 → Wait 30s for connection → Timeout → Error
Request 3 → Wait 30s for connection → Timeout → Error
...
10 requests × 30s = 300s of blocking → Service crashes (OOM/timeout)
```

**Issues:**
- Connections queue up consuming memory
- Service becomes unresponsive
- Cascades to dependent services
- Recovery is slow even after database comes back

### Solution With Circuit Breaker

```
Request 1 → Timeout → Circuit records failure (1/5)
Request 2 → Timeout → Circuit records failure (2/5)
Request 3 → Timeout → Circuit records failure (3/5)
Request 4 → Timeout → Circuit records failure (4/5)
Request 5 → Timeout → Circuit records failure (5/5) → CIRCUIT OPENS
Request 6 → Instant rejection (CircuitBreakerOpenError) → No timeout
Request 7 → Instant rejection → No timeout
...
After 60s → Circuit HALF_OPEN → Test single request
If success → Circuit CLOSED → Normal operation resumes
```

**Benefits:**
- Fast-fail instead of timeout (0s vs 30s)
- Service remains responsive (returns 503 to clients)
- Prevents connection pool exhaustion
- Automatic recovery when database comes back
- No cascading failures to dependent services

---

## Quick Start

### 1. Install Circuit Breaker

The circuit breaker is already included in `news-mcp-common` package.

```python
from news_mcp_common.resilience import (
    ResilientDatabaseManager,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)
```

### 2. Replace DatabaseManager

**Before (without circuit breaker):**

```python
from news_mcp_common.database import DatabaseManager

db_manager = DatabaseManager(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,
    max_overflow=10,
)

async def get_db():
    async with db_manager.session() as session:
        yield session
```

**After (with circuit breaker):**

```python
from news_mcp_common.resilience import (
    ResilientDatabaseManager,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)

# Configure circuit breaker
cb_config = CircuitBreakerConfig(
    failure_threshold=5,      # Open after 5 consecutive failures
    success_threshold=2,      # Close after 2 successes in HALF_OPEN
    timeout_seconds=60,       # Wait 60s before retry
    enable_metrics=True,      # Expose Prometheus metrics
)

# Create resilient database manager
db_manager = ResilientDatabaseManager(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    circuit_breaker_config=cb_config,
    name="feed-db",  # Circuit breaker name for metrics
    pool_size=20,
    max_overflow=10,
)

# FastAPI dependency with circuit breaker protection
async def get_db():
    try:
        async with db_manager.session() as session:
            yield session
    except CircuitBreakerOpenError:
        # Circuit is open - database is down
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable - circuit breaker is open"
        )
```

### 3. Use in FastAPI Endpoints

```python
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/articles")
async def create_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new article.

    Returns:
        - 201: Article created successfully
        - 503: Database unavailable (circuit breaker open)
    """
    db_article = Article(**article.dict())
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    return db_article
```

---

## Integration Patterns

### Pattern 1: New Service (Recommended)

For new services, use `ResilientDatabaseManager` from the start:

```python
# app/core/database.py
from news_mcp_common.resilience import (
    ResilientDatabaseManager,
    CircuitBreakerConfig,
)

# Initialize at startup
db_manager = ResilientDatabaseManager(
    database_url=settings.DATABASE_URL,
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=60,
        enable_metrics=True,
    ),
    name="my-service-db",
    pool_size=20,
    max_overflow=10,
)

# Export dependency
async def get_db():
    async with db_manager.session() as session:
        yield session
```

### Pattern 2: Existing Service Migration

For existing services with custom database session management:

**Step 1: Keep existing code, add circuit breaker wrapper**

```python
# app/db/session.py (existing code)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Original dependency (keep for backward compatibility)
async def get_async_db_legacy():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Step 2: Add resilient version**

```python
# app/db/session.py (add circuit breaker version)
from news_mcp_common.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)

# Create circuit breaker for database operations
_db_circuit_breaker = CircuitBreaker(
    name="feed-db",
    config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=60,
        enable_metrics=True,
    )
)

# New resilient dependency
async def get_async_db():
    """Get database session with circuit breaker protection."""

    # Check circuit state first (fail-fast)
    if _db_circuit_breaker.state == CircuitBreakerState.OPEN:
        raise CircuitBreakerOpenError(
            "Database circuit breaker is OPEN - refusing to acquire session"
        )

    # Acquire session with circuit breaker protection
    try:
        async with _db_circuit_breaker():
            async with AsyncSessionLocal() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

    except CircuitBreakerOpenError:
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
```

**Step 3: Gradually migrate endpoints**

```python
# Old endpoint (no circuit breaker)
@app.get("/feeds/legacy")
async def get_feeds_legacy(db: AsyncSession = Depends(get_async_db_legacy)):
    return await db.execute(select(Feed)).scalars().all()

# New endpoint (with circuit breaker)
@app.get("/feeds")
async def get_feeds(db: AsyncSession = Depends(get_async_db)):
    try:
        return await db.execute(select(Feed)).scalars().all()
    except CircuitBreakerOpenError:
        raise HTTPException(503, "Database temporarily unavailable")
```

### Pattern 3: Service-Specific Configuration

Different services may need different circuit breaker settings:

```python
# Feed service (high-traffic, quick recovery)
feed_db_manager = ResilientDatabaseManager(
    database_url=settings.DATABASE_URL,
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=3,      # Open quickly (3 failures)
        success_threshold=1,      # Close quickly (1 success)
        timeout_seconds=30,       # Short timeout (30s)
    ),
    name="feed-db",
)

# Analytics service (batch processing, slow recovery)
analytics_db_manager = ResilientDatabaseManager(
    database_url=settings.DATABASE_URL,
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=10,     # Open slowly (10 failures)
        success_threshold=3,      # Close cautiously (3 successes)
        timeout_seconds=120,      # Long timeout (2 minutes)
    ),
    name="analytics-db",
)
```

---

## Configuration

### Circuit Breaker Settings

```python
from news_mcp_common.resilience import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      # Open circuit after N consecutive failures
    success_threshold=2,      # Close circuit after N consecutive successes (in HALF_OPEN)
    timeout_seconds=60,       # Wait N seconds before attempting recovery (OPEN → HALF_OPEN)
    enable_metrics=True,      # Expose Prometheus metrics (default: True)
)
```

**Recommended Settings by Service Type:**

| Service Type | failure_threshold | success_threshold | timeout_seconds | Rationale |
|--------------|-------------------|-------------------|-----------------|-----------|
| **High-Traffic API** | 3-5 | 1-2 | 30-60 | Quick detection, fast recovery |
| **Background Worker** | 5-10 | 2-3 | 60-120 | Tolerate more failures, slower recovery |
| **Admin Panel** | 2-3 | 1 | 30 | Very sensitive, quick recovery |
| **Analytics/Batch** | 10-15 | 3-5 | 120-180 | Tolerate failures, slow recovery |

### Database Pool Settings

```python
db_manager = ResilientDatabaseManager(
    database_url="postgresql+asyncpg://...",
    circuit_breaker_config=config,

    # Connection pool settings
    pool_size=20,             # Base connection pool size
    max_overflow=10,          # Additional connections above pool_size
    pool_timeout=30,          # Timeout for acquiring connection (seconds)
    pool_recycle=3600,        # Recycle connections after N seconds

    # Logging
    echo=False,               # Log SQL statements (use for debugging only)
)
```

**Recommended Pool Settings:**

| Service Load | pool_size | max_overflow | pool_timeout | Rationale |
|--------------|-----------|--------------|--------------|-----------|
| **Low (< 10 req/s)** | 10 | 5 | 30 | Small pool, quick timeout |
| **Medium (10-100 req/s)** | 20 | 10 | 30 | Default settings |
| **High (100-1000 req/s)** | 50 | 20 | 30 | Large pool for concurrency |
| **Background Worker** | 5 | 2 | 60 | Small pool, long timeout |

---

## Monitoring & Metrics

### Prometheus Metrics

The circuit breaker automatically exposes Prometheus metrics:

```prometheus
# Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
circuit_breaker_state{name="feed-db"} 0

# Total successful operations
circuit_breaker_successes_total{name="feed-db"} 12450

# Total failed operations
circuit_breaker_failures_total{name="feed-db"} 23

# Total rejected operations (circuit was open)
circuit_breaker_rejections_total{name="feed-db"} 156
```

### Querying Metrics

```bash
# Check circuit breaker state
curl http://localhost:8101/metrics | grep 'circuit_breaker_state{name="feed-db"}'

# Check failure rate
curl http://localhost:8101/metrics | grep 'circuit_breaker_failures_total{name="feed-db"}'

# Check rejection count
curl http://localhost:8101/metrics | grep 'circuit_breaker_rejections_total{name="feed-db"}'
```

### Application Logging

```python
import logging

logger = logging.getLogger(__name__)

# Get circuit breaker stats
stats = db_manager.get_stats()

logger.info(
    f"Database circuit breaker stats: "
    f"state={stats['state']}, "
    f"successes={stats['total_successes']}, "
    f"failures={stats['total_failures']}, "
    f"rejections={stats['total_rejections']}, "
    f"failure_rate={stats['failure_rate']:.2%}"
)
```

### Health Check Endpoint

```python
@app.get("/health/db")
async def health_check_db():
    """
    Check database connection health.

    Returns:
        - 200: Database is healthy
        - 503: Database is down or circuit breaker is open
    """
    try:
        if await db_manager.check_connection():
            stats = db_manager.get_stats()
            return {
                "status": "healthy",
                "circuit_state": stats["state"].name,
                "success_rate": 1.0 - stats["failure_rate"],
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Database connection check failed"
                }
            )
    except CircuitBreakerOpenError:
        stats = db_manager.get_stats()
        return JSONResponse(
            status_code=503,
            content={
                "status": "circuit_open",
                "circuit_state": stats["state"].name,
                "message": "Circuit breaker is open - database unavailable"
            }
        )
```

---

## Testing

### Unit Test Example

```python
import pytest
from news_mcp_common.resilience import (
    ResilientDatabaseManager,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)

@pytest.fixture
async def db_manager():
    """Create database manager with circuit breaker for testing."""
    manager = ResilientDatabaseManager(
        database_url="postgresql+asyncpg://localhost/test_db",
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout_seconds=1,  # Short timeout for tests
        ),
        name="test-db",
    )
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_database_circuit_breaker_opens_on_failures(db_manager):
    """Test that circuit breaker opens after consecutive failures."""

    # Simulate 3 consecutive failures
    for i in range(3):
        with pytest.raises(Exception):
            async with db_manager.session() as session:
                # Force failure by executing invalid SQL
                await session.execute("INVALID SQL")

    # Circuit should be open now
    stats = db_manager.get_stats()
    assert stats["state"] == CircuitBreakerState.OPEN
    assert stats["total_failures"] == 3

    # Next session attempt should fail immediately
    with pytest.raises(CircuitBreakerOpenError):
        async with db_manager.session() as session:
            pass


@pytest.mark.asyncio
async def test_database_circuit_breaker_recovery(db_manager):
    """Test that circuit breaker recovers after successful operations."""

    # 1. Force circuit to open (3 failures)
    for i in range(3):
        try:
            async with db_manager.session() as session:
                await session.execute("INVALID SQL")
        except:
            pass

    # 2. Wait for timeout (circuit moves to HALF_OPEN)
    await asyncio.sleep(1.1)  # timeout_seconds=1

    # 3. Successful operation should close circuit
    async with db_manager.session() as session:
        result = await session.execute("SELECT 1")
        assert result.scalar() == 1

    # 4. Circuit should be closed
    stats = db_manager.get_stats()
    assert stats["state"] == CircuitBreakerState.CLOSED
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_endpoint_with_circuit_breaker(client, db_manager):
    """Test that API endpoint handles circuit breaker properly."""

    # 1. Normal operation (circuit closed)
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200

    # 2. Force circuit to open by simulating database outage
    # (In real test, you'd stop PostgreSQL container)
    for _ in range(5):
        try:
            async with db_manager.session() as session:
                # Simulate connection failure
                raise Exception("Connection refused")
        except:
            pass

    # 3. Verify circuit is open
    stats = db_manager.get_stats()
    assert stats["state"] == CircuitBreakerState.OPEN

    # 4. API should return 503
    response = await client.get("/api/v1/articles")
    assert response.status_code == 503
    assert "circuit breaker" in response.json()["detail"].lower()
```

---

## Troubleshooting

### Problem: Circuit Breaker Opens Too Often

**Symptoms:**
- Circuit frequently opens even when database is healthy
- High `circuit_breaker_rejections_total` metric

**Solutions:**
1. **Increase `failure_threshold`:**
   ```python
   CircuitBreakerConfig(
       failure_threshold=10,  # Was: 5
       ...
   )
   ```

2. **Increase connection pool size:**
   ```python
   ResilientDatabaseManager(
       pool_size=50,       # Was: 20
       max_overflow=20,    # Was: 10
       ...
   )
   ```

3. **Check for slow queries:**
   ```sql
   -- In PostgreSQL
   SELECT query, state, wait_event_type, wait_event
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY query_start;
   ```

### Problem: Circuit Stays Open Too Long

**Symptoms:**
- Circuit doesn't recover even after database comes back
- Low `success_threshold` but still open

**Solutions:**
1. **Reduce `timeout_seconds`:**
   ```python
   CircuitBreakerConfig(
       timeout_seconds=30,  # Was: 60
       ...
   )
   ```

2. **Reduce `success_threshold`:**
   ```python
   CircuitBreakerConfig(
       success_threshold=1,  # Was: 2
       ...
   )
   ```

3. **Manually reset circuit breaker:**
   ```python
   await db_manager.reset()
   ```

### Problem: Service Still Crashes During Database Outage

**Symptoms:**
- Service crashes with OOM even with circuit breaker
- High memory usage during outages

**Cause:**
- Circuit breaker protects database layer but requests still queue
- Need request-level timeout/backpressure

**Solution:**
Add request timeout middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=30.0  # 30s request timeout
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )

app.add_middleware(TimeoutMiddleware)
```

---

## Best Practices

### 1. Use Different Circuit Breakers for Different Databases

```python
# Main database
main_db = ResilientDatabaseManager(
    database_url=settings.MAIN_DB_URL,
    name="main-db",
)

# Analytics database (separate circuit breaker)
analytics_db = ResilientDatabaseManager(
    database_url=settings.ANALYTICS_DB_URL,
    name="analytics-db",
)
```

### 2. Log Circuit Breaker State Changes

```python
@app.on_event("startup")
async def startup():
    # Monitor circuit breaker state
    asyncio.create_task(monitor_circuit_breaker())

async def monitor_circuit_breaker():
    last_state = None
    while True:
        stats = db_manager.get_stats()
        current_state = stats["state"]

        if current_state != last_state:
            logger.warning(
                f"Circuit breaker state changed: {last_state} → {current_state}"
            )
            last_state = current_state

        await asyncio.sleep(5)
```

### 3. Handle CircuitBreakerOpenError Gracefully

```python
@app.get("/articles")
async def get_articles(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Article))
        return result.scalars().all()
    except CircuitBreakerOpenError:
        # Return cached data or degraded response
        return await get_cached_articles()
```

### 4. Test Circuit Breaker in Staging

```bash
# Simulate database outage
docker stop news-postgres

# Verify circuit breaker opens
curl http://localhost:8101/api/v1/articles
# Expected: 503 Service Unavailable

# Check metrics
curl http://localhost:8101/metrics | grep circuit_breaker_state
# Expected: circuit_breaker_state{name="feed-db"} 1  (OPEN)

# Bring database back
docker start news-postgres

# Wait for recovery (timeout_seconds)
sleep 60

# Verify circuit closes
curl http://localhost:8101/api/v1/articles
# Expected: 200 OK
```

---

## Summary

The database circuit breaker provides:
- ✅ Fast-fail behavior during database outages (0s vs 30s)
- ✅ Connection pool exhaustion protection
- ✅ Service remains responsive during DB downtime
- ✅ Automatic recovery when database comes back
- ✅ Prometheus metrics for monitoring
- ✅ No cascading failures to dependent services

**Integration is simple:**
1. Replace `DatabaseManager` with `ResilientDatabaseManager`
2. Add `CircuitBreakerOpenError` handling in endpoints
3. Monitor circuit breaker metrics
4. Test in staging before production

For questions or issues, see:
- Circuit Breaker source code: `news_mcp_common/resilience/circuit_breaker.py`
- External documentation: `/home/cytrex/userdocs/task-406-circuit-breaker-progress.md`

---

## See Also

- **[ADR-035: Circuit Breaker Pattern](../../../docs/decisions/ADR-035-circuit-breaker-pattern.md)** - Overall architecture
- **[CLAUDE.backend.md - Circuit Breaker](../../../CLAUDE.backend.md#-resilience-patterns)** - Quick reference
- **[Grafana Dashboard Guide](../../../docs/guides/grafana-circuit-breaker-dashboard.md)** - Monitoring setup

---
