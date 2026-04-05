# Research Service - Test Suite Documentation

## Overview

Comprehensive test suite for the Research Service with **>80% code coverage** target.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration (265 lines)
├── test_research.py         # Research API endpoint tests (347 lines)
├── test_templates.py        # Template API endpoint tests (375 lines)
├── test_perplexity.py       # Perplexity client tests (298 lines)
├── test_research_service.py # Service layer tests (335 lines)
├── test_tasks.py            # Celery task tests (189 lines)
├── test_models.py           # Database model tests (250 lines)
├── test_cost_optimizer.py   # Cost optimization tests (453 lines)
└── test_health.py           # Health check tests (91 lines)
```

**Total Lines**: 2,603 lines of test code

## Running Tests

### Prerequisites

```bash
# Install dependencies
cd /home/cytrex/news-microservices/services/research-service
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_research.py -v

# Run specific test class
pytest tests/test_research.py::TestCreateResearchTask -v

# Run specific test
pytest tests/test_research.py::TestCreateResearchTask::test_create_research_task_success -v
```

### Run Tests by Marker

```bash
# Run only async tests
pytest tests/ -m asyncio

# Run integration tests
pytest tests/ -m integration

# Run slow tests
pytest tests/ -m slow
```

## Test Coverage

### 1. Research API Tests (`test_research.py`)

**Coverage**: Research API endpoints

- ✅ Create research task (success, validation, authentication)
- ✅ Get research task (by ID, not found, auth required)
- ✅ List research tasks (pagination, filtering by status/feed)
- ✅ Batch research tasks
- ✅ Research history
- ✅ Usage statistics
- ✅ Error handling (Perplexity API errors, cost limits)

**Test Classes**:
- `TestCreateResearchTask` (7 tests)
- `TestGetResearchTask` (3 tests)
- `TestListResearchTasks` (4 tests)
- `TestBatchResearchTasks` (2 tests)
- `TestResearchHistory` (1 test)
- `TestUsageStatistics` (1 test)

### 2. Template API Tests (`test_templates.py`)

**Coverage**: Template API endpoints

- ✅ Create template (success, public/private, validation)
- ✅ List templates (user's templates, public templates)
- ✅ Get template (by ID, access control)
- ✅ Update template (success, ownership check)
- ✅ Delete template (success, soft delete)
- ✅ Preview template (variable substitution, cost estimation)
- ✅ Apply template (create research task from template)

**Test Classes**:
- `TestCreateTemplate` (4 tests)
- `TestListTemplates` (3 tests)
- `TestGetTemplate` (3 tests)
- `TestUpdateTemplate` (3 tests)
- `TestDeleteTemplate` (2 tests)
- `TestPreviewTemplate` (2 tests)
- `TestApplyTemplate` (3 tests)

### 3. Perplexity Client Tests (`test_perplexity.py`)

**Coverage**: Perplexity AI client

- ✅ Client initialization
- ✅ Research query (success, custom parameters)
- ✅ Error handling (no API key, rate limits, retries)
- ✅ Health check
- ✅ Response parsing
- ✅ Source extraction
- ✅ Temperature selection
- ✅ Recency filter
- ✅ Exponential backoff

**Tests**: 13 unit tests

### 4. Service Layer Tests (`test_research_service.py`)

**Coverage**: Business logic

- ✅ Research service (create task, caching, cost limits, get/list tasks, usage stats)
- ✅ Template service (create, get, list, apply templates)
- ✅ Cache management
- ✅ Cost tracking
- ✅ Cache key generation

**Test Classes**:
- `TestResearchService` (9 tests)
- `TestTemplateService` (7 tests)

### 5. Celery Task Tests (`test_tasks.py`)

**Coverage**: Asynchronous tasks

- ✅ Process research task (success, error handling)
- ✅ Batch research tasks
- ✅ Cache cleanup
- ✅ Task configuration

**Test Classes**:
- `TestProcessResearchTask` (3 tests)
- `TestBatchResearchTasks` (2 tests)
- `TestCleanupExpiredCache` (3 tests)
- `TestCeleryConfiguration` (2 tests)

### 6. Model Tests (`test_models.py`)

**Coverage**: Database models

- ✅ ResearchTask model (create, with results, with feed/article)
- ✅ ResearchTemplate model (create, usage tracking, public templates)
- ✅ ResearchCache model (create, hit tracking)
- ✅ CostTracking model (create, with task)
- ✅ Model indexes

**Test Classes**:
- `TestResearchTaskModel` (3 tests)
- `TestResearchTemplateModel` (3 tests)
- `TestResearchCacheModel` (2 tests)
- `TestCostTrackingModel` (2 tests)
- `TestModelIndexes` (2 tests)

### 7. Health Check Tests (`test_health.py`)

**Coverage**: Service health

- ✅ Health check endpoint
- ✅ Root endpoint
- ✅ API documentation
- ✅ OpenAPI schema
- ✅ 404 handling
- ✅ Authentication requirements
- ✅ CORS headers

**Tests**: 8 tests

## Fixtures

### Database Fixtures

- `db_session`: In-memory SQLite database for each test
- `client`: FastAPI test client with DB override

### Authentication Fixtures

- `test_user_id`: Mock user ID (1)
- `auth_headers`: Mock JWT token headers
- `mock_auth`: Mock authentication dependency

### Data Fixtures

- `sample_research_task`: Pre-created research task
- `sample_template`: Pre-created template
- `sample_cache_entry`: Pre-created cache entry
- `sample_cost_tracking`: Pre-created cost entries

### Mock Fixtures

- `mock_perplexity_response`: Mock Perplexity API response
- `mock_perplexity_client`: Mock Perplexity client
- `mock_redis`: Mock Redis client
- `mock_celery`: Mock Celery tasks

### Configuration Fixtures

- `disable_cost_tracking`: Temporarily disable cost tracking
- `disable_cache`: Temporarily disable caching

## Test Patterns

### Unit Tests

```python
def test_create_template(db_session, test_user_id):
    """Test successful template creation."""
    service = TemplateService()
    
    template = await service.create_template(
        db=db_session,
        user_id=test_user_id,
        template_data={
            "name": "Test Template",
            "query_template": "Research {{topic}}"
        }
    )
    
    assert template.id is not None
    assert template.name == "Test Template"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_create_research_task_success(
    client, mock_auth, mock_perplexity_client
):
    """Test successful research task creation."""
    response = client.post(
        "/api/v1/research/",
        headers={"Authorization": "Bearer mock.jwt.token"},
        json={
            "query": "What is AI?",
            "model_name": "sonar"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
```

### Error Handling Tests

```python
@pytest.mark.asyncio
async def test_create_task_cost_limit_exceeded(
    db_session, test_user_id
):
    """Test task creation when cost limit exceeded."""
    # Add high cost entries for today
    for i in range(5):
        entry = CostTracking(
            user_id=test_user_id,
            cost=10.0
        )
        db_session.add(entry)
    db_session.commit()
    
    service = ResearchService()
    
    with pytest.raises(ValueError, match="Daily cost limit exceeded"):
        await service.create_research_task(...)
```

## Coverage Goals

| Component | Target | Achieved |
|-----------|--------|----------|
| API Endpoints | >90% | ✅ |
| Service Layer | >85% | ✅ |
| Models | >80% | ✅ |
| Perplexity Client | >90% | ✅ |
| Celery Tasks | >80% | ✅ |
| **Overall** | **>80%** | ✅ |

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    cd services/research-service
    pytest tests/ --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Best Practices

1. **Use Fixtures**: Reuse common setup via pytest fixtures
2. **Mock External APIs**: Always mock Perplexity, Redis, Celery
3. **Test Edge Cases**: Invalid input, cost limits, rate limits
4. **Clear Descriptions**: Use descriptive test names and docstrings
5. **Async Tests**: Mark async tests with `@pytest.mark.asyncio`
6. **Database Isolation**: Each test gets fresh database
7. **Authentication**: Mock auth for all protected endpoints

## Common Issues

### 1. Async Tests Not Running

```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### 2. Database Errors

```python
# Ensure db_session is used, not get_db()
def test_something(db_session):  # ✅ Correct
    ...

def test_something(get_db):  # ❌ Wrong
    ...
```

### 3. Mock Not Applied

```python
# Patch at the right location
with patch("app.services.perplexity.perplexity_client"):  # ✅ Where it's used
    ...

with patch("app.perplexity_client"):  # ❌ Import location
    ...
```

## Next Steps

- [ ] Add performance tests
- [ ] Add load tests for batch operations
- [ ] Add integration tests with real Perplexity API (optional)
- [ ] Add mutation testing
- [ ] Set up continuous monitoring

## Maintainers

- QA Team
- Research Service Developers

---

**Last Updated**: 2025-10-11
