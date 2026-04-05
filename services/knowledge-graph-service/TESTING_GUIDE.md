# Knowledge-Graph Service - Testing Guide

## Quick Start

Run all tests:
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -v
```

Expected output: **145 passed** in ~4 seconds

## Test Files Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_neo4j_service.py` | 13 | Neo4j connection, queries, health checks |
| `test_entity_creation.py` | 20 | Entity model creation and validation |
| `test_relationship_queries.py` | 24 | Relationship models and filtering |
| `test_graph_traversal.py` | 19 | Graph traversal and path finding |
| `test_cypher_building.py` | 32 | Cypher query construction |
| `test_ingestion_service.py` | 16 | Triplet ingestion and batch processing |
| `test_entity_deduplication.py` | 33 | Entity deduplication strategies |
| `test_relationship_normalization.py` | 5 | Relationship type normalization (original) |
| **TOTAL** | **145** | **70%+ coverage** |

## Running Tests

### All Tests
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -v
```

### Specific File
```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_creation.py -v
```

### Specific Test Class
```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_creation.py::TestEntityCreation -v
```

### Specific Test
```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_creation.py::TestEntityCreation::test_entity_creation_basic -v
```

### Quick Output (No Warnings)
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -q
```

### With Coverage Report
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --cov=app --cov-report=html
```

### Matching Test Pattern
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -k "entity" -v
```

### Only Failed Tests
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --lf
```

### Exit on First Failure
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -x
```

### Show Print Statements
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -v -s
```

## Test Categories

### 1. Neo4j Integration (13 tests)
Tests Neo4j connection and basic operations.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_neo4j_service.py -v
```

**Tests:**
- Connection lifecycle
- Query execution
- Write operations
- Index creation
- Health checks
- Retry logic

### 2. Entity Creation (20 tests)
Tests Entity model validation and properties.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_creation.py -v
```

**Tests:**
- Basic creation
- Type variations
- Properties handling
- Timestamp management
- Serialization
- Unicode support

### 3. Relationship Queries (24 tests)
Tests Relationship model and filtering.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_relationship_queries.py -v
```

**Tests:**
- Creation and validation
- Confidence validation (0.0-1.0)
- Filtering by confidence/type
- Sorting operations
- Sentiment fields

### 4. Graph Traversal (19 tests)
Tests graph navigation and path finding.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_graph_traversal.py -v
```

**Tests:**
- Neighbor discovery
- Path finding (BFS)
- Multi-hop traversal
- Bidirectional detection
- Distance calculation

### 5. Cypher Building (32 tests)
Tests dynamic Cypher query construction.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_cypher_building.py -v
```

**Tests:**
- MERGE/MATCH patterns
- Query parameterization
- Injection prevention
- Aggregation queries
- Index creation

### 6. Ingestion Service (16 tests)
Tests triplet ingestion and batch processing.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_ingestion_service.py -v
```

**Tests:**
- Single triplet ingestion
- Batch processing
- Error handling
- Idempotency
- Metric tracking

### 7. Entity Deduplication (33 tests)
Tests entity merging and duplicate detection.

```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_deduplication.py -v
```

**Tests:**
- Exact matching
- Property merging
- Relationship merging
- Conflict resolution
- Whitespace handling

## Test Structure

### Fixtures (conftest.py)
Reusable test components:

```python
# Use fixtures in tests
def test_something(sample_entity_person, mock_neo4j_driver):
    pass

# Available fixtures:
# - mock_neo4j_driver          # Async Neo4j driver mock
# - neo4j_service_with_mock    # Pre-configured service
# - sample_entity_*            # Sample entities (person, org, location)
# - sample_relationship        # Sample relationship
# - sample_triplet             # Complete triplet
# - mock_neo4j_*_result        # Mock query results
```

### Async Tests
All async operations are properly tested:

```python
@pytest.mark.asyncio
async def test_async_operation(neo4j_service_with_mock):
    result = await neo4j_service_with_mock.health_check()
    assert result is True
```

### Error Handling
Tests validate exception paths:

```python
def test_error_handling():
    with pytest.raises(RuntimeError, match="error message"):
        some_operation()
```

## Key Test Patterns

### Testing Neo4j Operations
```python
@pytest.mark.asyncio
async def test_query(neo4j_service_with_mock):
    # No real database connection needed
    await neo4j_service_with_mock.health_check()
```

### Testing Entity Creation
```python
def test_entity():
    entity = Entity(name="Tesla", type="ORGANIZATION")
    assert entity.name == "Tesla"
```

### Testing Graph Operations
```python
def test_graph_traversal(sample_triplet):
    # sample_triplet fixture provides ready-to-use test data
    assert sample_triplet.subject.name == "Elon Musk"
```

### Testing Deduplication
```python
def test_dedup():
    entities = [Entity(name="Tesla", type="ORG"), Entity(name="Tesla", type="ORG")]
    unique = {(e.name, e.type): e for e in entities}
    assert len(unique) == 1
```

## Coverage Analysis

### Generate Coverage Report
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --cov=app --cov-report=html
```

Then open `htmlcov/index.html` in browser.

### Coverage by Module
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --cov=app --cov-report=term-missing
```

Shows which lines are not covered.

## Performance

### Fast Tests (< 1 second)
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -q --tb=no
```

### Slow Tests (if any)
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --durations=10
```

Show slowest 10 tests.

### Full Test Suite
```bash
# Total time: ~4.2 seconds
docker compose exec knowledge-graph-service pytest /app/tests/ -v
```

## Debugging

### Show Debug Output
```bash
docker compose exec knowledge-graph-service pytest /app/tests/test_entity_creation.py -v -s
```

### Stop on First Failure
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -x
```

### Show Local Variables on Failure
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ -l
```

### Drop to PDB on Failure
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --pdb
```

### Show Full Traceback
```bash
docker compose exec knowledge-graph-service pytest /app/tests/ --tb=long
```

## Common Issues

### Tests Timeout
Increase timeout in `pytest.ini` (if created):
```ini
[pytest]
timeout = 30
```

### Import Errors
Ensure `/app` is in Python path (handled by conftest.py):
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Async Test Issues
Use `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_async():
    pass
```

### Mock Not Working
Verify mock is set before calling:
```python
service.driver = AsyncMock()  # Set mock before operation
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: docker compose exec -T knowledge-graph-service pytest /app/tests/ -v
```

### Jenkins Example
```groovy
stage('Test') {
    steps {
        sh 'docker compose exec -T knowledge-graph-service pytest /app/tests/ -v'
    }
}
```

## Best Practices

1. **Run Tests Frequently**
   - Before committing code
   - After any model changes
   - Before deploying

2. **Use Fixtures**
   - Avoid test duplication
   - Keep tests DRY
   - Reuse sample data

3. **Test Error Paths**
   - Don't just test happy path
   - Validate exception handling
   - Test edge cases

4. **Keep Tests Fast**
   - Use mocks instead of real DB
   - Avoid sleep() calls
   - Parallelize independent tests

5. **Write Descriptive Tests**
   - Clear test names
   - Docstrings for context
   - One assertion per test (mostly)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Pydantic Validation](https://docs.pydantic.dev/)

## Documentation

- **TEST_COVERAGE_REPORT.md** - Detailed coverage analysis
- **TESTS_SUMMARY.txt** - Complete test summary
- **conftest.py** - Fixture definitions and test utilities

---

**Last Updated:** 2025-10-30
**Total Tests:** 145
**Pass Rate:** 100%
**Execution Time:** ~4.2 seconds
