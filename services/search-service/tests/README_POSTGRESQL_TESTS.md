# PostgreSQL Integration Tests

## Overview

The search-service test suite supports both **SQLite** (default, fast) and **PostgreSQL** (full features) testing modes.

## Current Status

**✅ SQLite Tests:** Fully functional (6 passed)
- Fast execution (~0.14s)
- No external dependencies
- Sufficient for Admin API endpoints
- **Default mode** - just run `pytest`

**⚠️ PostgreSQL Tests:** Infrastructure ready, requires AsyncClient migration
- Full PostgreSQL features (Full-Text Search, TSVECTOR)
- Requires Docker access on host
- Event-loop compatibility issue with FastAPI TestClient
- **Run with:** `pytest --postgresql` (requires host execution)

## Quick Start

### SQLite Tests (Recommended)
```bash
# Inside Docker container
docker exec news-search-service pytest tests/

# All tests use SQLite by default - fast and reliable
```

### PostgreSQL Tests (Future)
```bash
# On HOST system (not in container)
cd /home/cytrex/news-microservices/services/search-service
pytest tests/test_admin_integration.py --postgresql -v

# Note: Currently fails due to TestClient/AsyncClient incompatibility
# See "Known Issues" below
```

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures (SQLite + PostgreSQL)
├── test_search.py              # SQLite tests (6 passed)
├── test_admin_integration.py   # PostgreSQL-ready tests (7 tests)
└── README_POSTGRESQL_TESTS.md  # This file
```

## PostgreSQL Infrastructure

### Fixtures (in conftest.py)

**Session-scoped:**
- `postgres_container` - Starts PostgreSQL 16 Alpine container via testcontainers
- `postgres_url` - Async connection URL (postgresql+asyncpg://)
- `postgres_engine` - SQLAlchemy async engine
- `postgres_session` - Fresh session per test

**Test-scoped:**
- `setup_test_data` - Creates test articles, search history, analytics
- `cleanup_postgres` - Cleans database after each test

### Configuration

**pytest.ini:**
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = session  # Required for PostgreSQL
```

**Markers:**
```python
@pytest.mark.postgresql  # Mark tests requiring PostgreSQL
```

## Known Issues

### 1. Event-Loop Incompatibility

**Problem:**
```
RuntimeError: Task got Future attached to a different loop
```

**Cause:**
- FastAPI `TestClient` is synchronous
- PostgreSQL with `asyncpg` requires async
- pytest-asyncio runs in separate event loop

**Solution (Future):**
Migrate tests to `httpx.AsyncClient`:

```python
# Current (sync):
client = TestClient(app)
response = client.get('/api/v1/admin/stats/index')

# Required (async):
async with AsyncClient(app=app, base_url="http://test") as ac:
    response = await ac.get('/api/v1/admin/stats/index')
```

### 2. Docker-in-Docker Limitation

**Problem:**
testcontainers cannot access Docker daemon from inside container

**Solution:**
Run PostgreSQL tests on **host system**, not inside Docker container

## When to Use PostgreSQL Tests

Use PostgreSQL tests when you need:
- ✅ Full-Text Search (TSVECTOR, to_tsquery)
- ✅ PostgreSQL-specific functions (pg_size_pretty, etc.)
- ✅ Production-like database behavior
- ✅ Performance testing with realistic data

Use SQLite tests (default) for:
- ✅ Admin API endpoints (current use case)
- ✅ Fast CI/CD pipelines
- ✅ Development workflow
- ✅ Coverage metrics

## Migration Guide

To enable PostgreSQL tests in the future:

1. **Convert TestClient to AsyncClient:**
   ```python
   # In test_admin_integration.py
   @pytest.fixture
   async def async_client():
       async with AsyncClient(app=app, base_url="http://test") as ac:
           yield ac

   # Update all tests
   async def test_get_index_statistics(async_client, setup_test_data):
       response = await async_client.get("/api/v1/admin/stats/index")
       assert response.status_code == 200
   ```

2. **Mark all tests as async:**
   ```python
   @pytest.mark.asyncio
   @pytest.mark.postgresql
   async def test_something(...):
       ...
   ```

3. **Run on host:**
   ```bash
   pytest tests/test_admin_integration.py --postgresql -v
   ```

## Resources

- testcontainers-python: https://testcontainers-python.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- httpx AsyncClient: https://www.python-httpx.org/async/

## Authors

Created: 2025-11-02
Status: Infrastructure ready, AsyncClient migration pending
