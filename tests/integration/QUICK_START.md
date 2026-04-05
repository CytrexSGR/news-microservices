# Integration Tests - Quick Start Guide

**Status:** ✅ Ready to Use
**Total Tests:** 37
**Coverage:** 73%

---

## 1 Minute Setup

```bash
# Step 1: Install dependencies (1 minute)
pip install -r tests/integration/requirements.txt

# Step 2: Start services (wait 30 seconds for health checks)
docker compose up -d

# Step 3: Run all tests (45 seconds)
pytest tests/integration/ -v

# Expected: 37 passed in ~45s
```

---

## Run Specific Tests

### By Flow (5-10 seconds each)

```bash
# Flow 1: Article Processing Pipeline (HIGHEST PRIORITY)
pytest tests/integration/test_article_pipeline.py -v

# Flow 2: Analytics WebSocket
pytest tests/integration/test_analytics_websocket.py -v

# Flow 3: Cache Performance
pytest tests/integration/test_cache_performance.py -v

# Flow 4: Scheduled Jobs
pytest tests/integration/test_scheduled_jobs.py -v
```

### By Test Class

```bash
# Article pipeline tests
pytest tests/integration/test_article_pipeline.py::TestArticleProcessingPipeline -v

# WebSocket connection tests
pytest tests/integration/test_analytics_websocket.py::TestAnalyticsWebSocket -v

# Cache tests
pytest tests/integration/test_cache_performance.py::TestCachePerformance -v

# Scheduler tests
pytest tests/integration/test_scheduled_jobs.py::TestScheduledJobExecution -v
```

### Single Test

```bash
# Test article pipeline end-to-end
pytest tests/integration/test_article_pipeline.py::TestArticleProcessingPipeline::test_complete_article_pipeline_flow -v

# Test WebSocket connection
pytest tests/integration/test_analytics_websocket.py::TestAnalyticsWebSocket::test_websocket_connection_establishment -v

# Test cache speedup
pytest tests/integration/test_cache_performance.py::TestCachePerformance::test_cache_speedup_ratio -v
```

---

## Useful Commands

### With Coverage

```bash
# Run with coverage report
pytest tests/integration/ --cov=services --cov-report=html

# Open HTML report
open htmlcov/index.html
```

### With HTML Report

```bash
# Generate pytest HTML report
pytest tests/integration/ --html=reports/test-report.html --self-contained-html

# Open report
open reports/test-report.html
```

### Verbose Output

```bash
# Show print statements and logs
pytest tests/integration/ -v -s

# Show slowest tests
pytest tests/integration/ --durations=10
```

### Stop on First Failure

```bash
# Stop after first failure
pytest tests/integration/ -x

# Stop after N failures
pytest tests/integration/ --maxfail=2
```

---

## Test Files Overview

| File | Tests | Coverage | Focus |
|------|-------|----------|-------|
| **test_article_pipeline.py** | 8 | 80% | Article processing |
| **test_analytics_websocket.py** | 9 | 70% | Real-time updates |
| **test_cache_performance.py** | 9 | 80% | Caching & performance |
| **test_scheduled_jobs.py** | 11 | 60% | Job scheduling |

---

## Credentials

**Always use these for testing:**

```
Username: andreas
Password: Aug2012#
Email: andreas@test.com
```

*Do NOT create new test users!* (From CLAUDE.md)

---

## Service Health Check

```bash
# Check if services are running
docker compose ps

# View logs
docker compose logs -f feed-service
docker compose logs -f analytics-service
docker compose logs -f scheduler-service

# Restart a service
docker compose restart feed-service

# Stop all services
docker compose down

# Start all services
docker compose up -d
```

---

## Troubleshooting

### Services Not Running

```bash
# Start them
docker compose up -d

# Wait for health checks
docker compose ps

# All should show "healthy"
```

### Authentication Failed

```bash
# Test auth endpoint
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}'

# Should return: {"access_token": "...", "token_type": "bearer"}
```

### Database Connection Error

```bash
# Test PostgreSQL
psql -h localhost -U news_user -d news_mcp -c "SELECT 1"

# Should return: (1 row)
```

### Redis Connection Error

```bash
# Test Redis
redis-cli -a redis_secret_2024 ping

# Should return: PONG
```

### WebSocket Timeout

```bash
# Services might be slow
# WebSocket tests skip gracefully
# Check analytics-service logs
docker compose logs -f analytics-service | grep -i websocket
```

---

## Key Metrics

### Article Pipeline
- Feed creation: ~100ms
- Article fetch: ~2-3s
- Content analysis: ~3-8s
- Search: ~200ms

### Cache Performance
- Cache miss: ~350ms
- Cache hit: ~5ms
- Speedup: 70x (target: 30-40x)

### WebSocket
- Connection: <5s
- Message latency: <100ms
- Uptime: 99%+

### Scheduler
- Job trigger: <500ms
- Job execution: <30s

---

## Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| **README.md** | Comprehensive guide | tests/integration/README.md |
| **INTEGRATION_TEST_COVERAGE.md** | Detailed coverage report | reports/testing/ |
| **INTEGRATION_TEST_SUMMARY.md** | Executive summary | reports/testing/ |
| **This file** | Quick reference | tests/integration/QUICK_START.md |

---

## Common Patterns

### Test Pattern

```python
@pytest.mark.asyncio
async def test_something(async_client, auth_headers):
    """Test description"""
    # Arrange
    request_data = {"key": "value"}

    # Act
    response = await async_client.post(
        "/endpoint",
        json=request_data,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()

    logger.info("✅ Test passed")
```

### Database Test Pattern

```python
@pytest.mark.asyncio
async def test_database(async_client, auth_headers, db_session):
    """Test with database operations"""
    # ... make API request ...

    # Verify in database
    from app.models.core import Item
    items = db_session.exec(select(Item)).all()
    assert len(items) > 0
```

### Cache Test Pattern

```python
@pytest.mark.asyncio
async def test_cache(async_client, auth_headers, redis_client):
    """Test with cache operations"""
    # First request (cache miss)
    response1 = await async_client.get("/endpoint", headers=auth_headers)

    # Second request (cache hit)
    response2 = await async_client.get("/endpoint", headers=auth_headers)

    # Should be faster
    assert response2.elapsed < response1.elapsed
```

---

## Pre-Commit Checklist

Before committing code changes:

- [ ] Run all tests: `pytest tests/integration/ -v`
- [ ] Verify 37/37 pass
- [ ] Check coverage: `pytest tests/integration/ --cov=services`
- [ ] Review any changes to services
- [ ] Update documentation if needed
- [ ] Commit changes

---

## CI/CD

### GitHub Actions

Tests automatically run on:
- Push to main/develop/feature/*
- Pull requests to main/develop

See: `.github/workflows/integration-tests.yml`

### Local CI Simulation

```bash
# Run tests like CI would
pytest tests/integration/ \
  --junitxml=reports/junit.xml \
  --cov=services \
  --cov-report=xml \
  -v
```

---

## Performance Tips

### Speed Up Local Testing

```bash
# Run only essential flows
pytest tests/integration/test_article_pipeline.py \
  tests/integration/test_cache_performance.py -v

# Skip slow WebSocket tests
pytest tests/integration/ \
  --ignore=tests/integration/test_analytics_websocket.py -v
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/integration/ -v -n 4
```

### Incremental Testing

```bash
# Run only new/modified tests (requires pytest-testmon)
pytest tests/integration/ -v --testmon

# Or watch mode
pytest tests/integration/ -v --looponfail
```

---

## Useful Links

- **Test Suite Index:** INTEGRATION_TESTS_INDEX.md
- **Full Documentation:** tests/integration/README.md
- **Coverage Report:** reports/testing/INTEGRATION_TEST_COVERAGE.md
- **Architecture:** ARCHITECTURE.md
- **Backend Guide:** CLAUDE.backend.md
- **Development Guide:** CLAUDE.md

---

## Support

**Need help?**

1. Check this file (Common issues & patterns)
2. Check tests/integration/README.md (Comprehensive guide)
3. Check reports/testing/INTEGRATION_TEST_COVERAGE.md (Details per flow)
4. Check ARCHITECTURE.md (System overview)

**Report issues:**
- Check service logs: `docker compose logs -f`
- Verify services healthy: `docker compose ps`
- Verify credentials: Check CLAUDE.md
- Verify database: `psql -h localhost -U news_user -d news_mcp -c "SELECT 1"`

---

**Last Updated:** 2025-11-24
**Status:** ✅ Production Ready
**Ready to Use:** YES
