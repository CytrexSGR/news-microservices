# Testing Guide - News Microservices

This guide covers testing strategies, best practices, and common patterns for the News Microservices project.

---

## Quick Reference

### Running Tests

**Development (Docker container):**
```bash
# Run all tests in feed-service
docker exec news-feed-service pytest tests/ -v

# Run specific test file
docker exec news-feed-service pytest tests/test_domain_parser.py -v

# Run with coverage
docker exec news-feed-service pytest tests/ -v --cov=app --cov-report=html
```

**Local (host system):**
```bash
cd /home/cytrex/news-microservices/services/feed-service

# Activate virtual environment (if using)
source venv/bin/activate

# Run tests
pytest tests/ -v
```

---

## Test Infrastructure

### Directory Structure

```
services/<service-name>/
├── app/                    # Application code
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Shared fixtures
│   ├── test_*.py          # Unit tests
│   └── integration/       # Integration tests (optional)
└── requirements.txt       # Dependencies (including test deps)
```

### Test Fixtures (conftest.py)

**Purpose:** Shared test setup and teardown logic

**Key Fixtures:**

#### 1. Database Session (Async)
```python
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create isolated test database session."""
    # Use SQLite in-memory for speed
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

#### 2. Test Client
```python
@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """FastAPI test client with overridden dependencies."""
    async def override_get_db() -> AsyncSession:
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

---

## Test Dependencies

### Required in requirements.txt

```python
# Testing
pytest==7.4.4                # Test framework
pytest-asyncio==0.23.3       # Async test support
pytest-cov==4.1.0            # Coverage reports
aiosqlite==0.21.0            # SQLite async driver for in-memory tests
```

**⚠️ Critical:** ALL test dependencies MUST be in requirements.txt, even if only used for testing.

**Why:** Docker containers need these dependencies to run tests in CI/CD pipelines.

---

## Test Categories

### 1. Unit Tests

**Scope:** Single function or class
**Dependencies:** None (or mocked)
**Speed:** Fast (< 0.1s per test)

**Example: Domain Parser**
```python
def test_extract_domain_from_standard_url():
    """Test standard HTTPS URL with path."""
    url = "https://example.com/feed.xml"
    domain = parse_domain_from_url(url)
    assert domain == "example.com"

def test_empty_url_raises_exception():
    """Test that empty URL raises HTTPException."""
    url = ""
    with pytest.raises(HTTPException) as exc_info:
        parse_domain_from_url(url)
    assert exc_info.value.status_code == 400
```

**Best Practices:**
- Test happy path + edge cases + error conditions
- One assertion per test (or related assertions)
- Clear test names describing what is tested
- Use parametrize for multiple similar cases

### 2. Integration Tests

**Scope:** Multiple components working together
**Dependencies:** Database, external services (mocked)
**Speed:** Slower (0.5-2s per test)

**Example: Feed Assessment Flow**
```python
@pytest.mark.asyncio
async def test_create_feed_and_trigger_assessment(
    client: TestClient,
    db_session: AsyncSession
):
    """Test complete feed creation → assessment flow."""

    # 1. Create feed
    response = client.post("/api/v1/feeds", json={
        "url": "https://example.com/rss",
        "name": "Test Feed"
    })
    assert response.status_code == 201
    feed_id = response.json()["id"]

    # 2. Trigger assessment
    response = client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 202
    assert response.json()["assessment_status"] == "pending"

    # 3. Verify database state
    feed = await db_session.get(Feed, feed_id)
    assert feed.assessment_status == "pending"
```

### 3. End-to-End Tests (Future)

**Scope:** Entire system with real services
**Dependencies:** All services, databases, message queues
**Speed:** Slowest (5-10s per test)

**Use Cases:**
- User workflows (register → login → create feed → assess)
- Cross-service communication
- Event-driven flows (RabbitMQ)

---

## Test-Driven Refactoring Pattern

**Proven methodology for improving existing code:**

### Step 1: Extract
```python
# BEFORE: Inline code in API endpoint
from urllib.parse import urlparse
parsed_url = urlparse(str(feed.url))
domain = parsed_url.netloc or parsed_url.path.split('/')[0]
if not domain:
    raise HTTPException(status_code=400, detail="...")
```

**Extract to utility function:**
```python
# app/utils.py
def parse_domain_from_url(url: str) -> str:
    """Extract domain from URL with validation."""
    # ... implementation
```

### Step 2: Test
```python
# tests/test_domain_parser.py
class TestDomainParser:
    def test_extract_domain_from_standard_url(self):
        assert parse_domain_from_url("https://example.com/feed") == "example.com"

    def test_empty_url_raises_exception(self):
        with pytest.raises(HTTPException):
            parse_domain_from_url("")

    # ... 18+ more test cases
```

### Step 3: Refactor
```python
# AFTER: Replace inline code with function call
from app.utils import parse_domain_from_url

domain = parse_domain_from_url(feed.url)  # 1 line, fully tested
```

**Result:**
- ✅ 11 lines → 1 line
- ✅ 0% test coverage → 100% test coverage
- ✅ Reusable across codebase
- ✅ Clear error messages

---

## Docker Testing Challenges

### Issue 1: Tests Not Visible in Container

**Problem:** Created test files on host, but container can't find them.

**Root Cause:** Development Dockerfile uses volume mounts, production Dockerfile copies files explicitly.

**Solution (Development):**
```bash
# Copy tests to running container
docker exec news-feed-service mkdir -p /app/tests
docker cp services/feed-service/tests/test_domain_parser.py news-feed-service:/app/tests/
docker cp services/feed-service/tests/conftest.py news-feed-service:/app/tests/
```

**Solution (Production):**
Update Dockerfile.prod:
```dockerfile
# Copy tests for CI/CD
COPY tests ./tests
```

### Issue 2: Missing Test Dependencies

**Problem:** `ModuleNotFoundError: No module named 'aiosqlite'`

**Root Cause:** Test dependencies not in requirements.txt

**Solution:**
```bash
# Immediate fix (container)
docker exec news-feed-service pip install aiosqlite

# Permanent fix (requirements.txt)
echo "aiosqlite==0.21.0" >> services/feed-service/requirements.txt
docker compose up -d --build feed-service
```

### Issue 3: pytest Not Found

**Problem:** `exec: "pytest": executable file not found in $PATH`

**Alternatives:**
```bash
# Option 1: Use python -m
docker exec news-feed-service python -m pytest tests/ -v

# Option 2: Install pytest temporarily
docker exec news-feed-service pip install pytest

# Option 3: Run tests on host
cd services/feed-service
pytest tests/ -v
```

---

## Common Test Patterns

### Testing HTTP Exceptions

```python
def test_invalid_input_raises_400():
    """Test validation error returns 400."""
    with pytest.raises(HTTPException) as exc_info:
        parse_domain_from_url("")

    assert exc_info.value.status_code == 400
    assert "Could not extract domain" in exc_info.value.detail
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_database_operation(db_session: AsyncSession):
    """Test async database query."""
    feed = Feed(url="https://example.com/rss", name="Test")
    db_session.add(feed)
    await db_session.commit()

    result = await db_session.execute(select(Feed))
    assert result.scalar_one() == feed
```

### Mocking External Services

```python
def test_external_api_call(monkeypatch):
    """Test function that calls external API."""

    async def fake_api_call(*args, **kwargs):
        return {"status": "success"}

    monkeypatch.setattr(
        "app.services.research.ResearchService.create_research_task",
        fake_api_call
    )

    result = await function_under_test()
    assert result["status"] == "success"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("url,expected_domain", [
    ("https://example.com/feed", "example.com"),
    ("https://www.news.org:8080/rss", "www.news.org:8080"),
    ("http://localhost/feed.xml", "localhost"),
])
def test_various_url_formats(url, expected_domain):
    """Test multiple URL formats in single test."""
    assert parse_domain_from_url(url) == expected_domain
```

---

## Test Coverage

### Generating Coverage Reports

```bash
# Run tests with coverage
docker exec news-feed-service pytest tests/ --cov=app --cov-report=html

# View report (copy from container to host)
docker cp news-feed-service:/app/htmlcov ./coverage-report
firefox coverage-report/index.html
```

### Coverage Targets

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| Utilities (utils.py) | 100% | 100% | ✅ |
| API Endpoints | 80%+ | TBD | ⏳ |
| Services | 80%+ | TBD | ⏳ |
| Models | 60%+ | TBD | ⏳ |

---

## Continuous Integration (Future)

### GitHub Actions Workflow

```yaml
name: Test Feed Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker Image
        run: |
          docker build -f services/feed-service/Dockerfile.prod \
            -t feed-service:test services/feed-service

      - name: Run Tests
        run: |
          docker run --rm feed-service:test \
            pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Best Practices

### ✅ DO

1. **Write tests BEFORE refactoring**
   - Extract → Test → Refactor (not Extract → Refactor → Test)

2. **Use descriptive test names**
   - `test_empty_url_raises_exception` ✅
   - `test_error_case` ❌

3. **Test edge cases**
   - Empty strings, None, negative numbers, special characters

4. **Isolate tests**
   - Each test should be independent
   - Use fixtures for setup/teardown

5. **Mock external dependencies**
   - Don't call real APIs in tests
   - Use monkeypatch or unittest.mock

6. **Keep tests fast**
   - Unit tests: < 0.1s
   - Integration tests: < 2s
   - E2E tests: < 10s

### ❌ DON'T

1. **Don't skip test dependencies in requirements.txt**
   - "It works on my machine" is not acceptable

2. **Don't test implementation details**
   - Test public API, not internal logic

3. **Don't share state between tests**
   - Use `scope="function"` for fixtures

4. **Don't commit broken tests**
   - Fix tests before merging

5. **Don't test external services directly**
   - Mock them instead

---

## Troubleshooting

### Tests fail after code changes

**Check:**
1. Did you update test expectations?
2. Did imports change?
3. Did function signatures change?

**Fix:** Update tests to match new behavior

### Tests pass locally but fail in CI

**Check:**
1. Are test dependencies in requirements.txt?
2. Does CI use same Python version?
3. Are environment variables set in CI?

**Fix:** Ensure CI environment matches local

### Tests are slow

**Check:**
1. Are you hitting external APIs?
2. Using real database instead of SQLite?
3. Too many database operations?

**Fix:**
- Mock external calls
- Use in-memory database
- Reduce test scope

---

## Quick Command Reference

```bash
# Run all tests
docker exec news-feed-service pytest tests/ -v

# Run specific test file
docker exec news-feed-service pytest tests/test_domain_parser.py -v

# Run specific test
docker exec news-feed-service pytest tests/test_domain_parser.py::TestDomainParser::test_real_world_rss_feeds -v

# Run with coverage
docker exec news-feed-service pytest tests/ --cov=app --cov-report=html

# Run tests in parallel (faster)
docker exec news-feed-service pytest tests/ -v -n 4

# Stop on first failure
docker exec news-feed-service pytest tests/ -v -x

# Show print statements
docker exec news-feed-service pytest tests/ -v -s

# Run only failed tests from last run
docker exec news-feed-service pytest tests/ -v --lf
```

---

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development (TDD)](https://en.wikipedia.org/wiki/Test-driven_development)

---

**Last Updated:** 2025-10-20
**Status:** Production Ready
**Maintained By:** Development Team
