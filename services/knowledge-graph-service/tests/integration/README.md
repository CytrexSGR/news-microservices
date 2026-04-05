# Integration Tests - Knowledge-Graph Service

End-to-end integration tests for FMP Service → Knowledge-Graph → Neo4j data pipeline.

## Overview

These tests validate complete workflows across multiple services:

1. **Service-to-Service Communication**: HTTP requests between Knowledge-Graph and FMP Service
2. **Data Transformation**: FMP metadata → Neo4j graph structure
3. **Database Operations**: Node/relationship creation in Neo4j
4. **Idempotency**: MERGE operations don't create duplicates
5. **Error Handling**: Graceful handling of partial failures
6. **Performance**: Sync and query performance benchmarks

## Prerequisites

### Running Services

All tests require the Docker Compose stack to be running:

```bash
cd /home/cytrex/news-microservices
docker compose up -d

# Verify services are healthy
docker compose ps
curl http://localhost:8109/health  # FMP Service
curl http://localhost:8111/health  # Knowledge-Graph Service
```

Required services:
- **FMP Service** (port 8109): Provides asset metadata
- **Knowledge-Graph Service** (port 8111): Main service under test
- **Neo4j** (port 7687): Graph database
- **PostgreSQL** (port 5432): Optional, for FMP cache

### Python Dependencies

Install test dependencies:

```bash
cd services/knowledge-graph-service
pip install -r requirements.txt

# Additional test dependencies (if not in requirements.txt)
pip install pytest pytest-asyncio httpx
```

## Test Structure

```
tests/integration/
├── __init__.py                     # Package initialization
├── README.md                       # This file
└── test_fmp_kg_integration.py      # Main integration tests (10 scenarios)
```

## Running Tests

### All Integration Tests

```bash
# From service root
cd /home/cytrex/news-microservices/services/knowledge-graph-service

# Run all integration tests
pytest tests/integration/ -v -m integration

# With detailed logging
pytest tests/integration/ -v -m integration --log-cli-level=INFO
```

### Specific Test Scenarios

```bash
# Test 1: Service connectivity
pytest tests/integration/test_fmp_kg_integration.py::test_fmp_service_connectivity -v

# Test 2: Small sync (4 symbols)
pytest tests/integration/test_fmp_kg_integration.py::test_e2e_market_sync_small -v

# Test 3: Full sync (40 symbols)
pytest tests/integration/test_fmp_kg_integration.py::test_e2e_market_sync_full -v

# Test 4: Idempotency
pytest tests/integration/test_fmp_kg_integration.py::test_sync_idempotency -v

# Test 7: Performance benchmarks
pytest tests/integration/test_fmp_kg_integration.py::test_sync_performance -v -m performance
```

### Filter by Markers

```bash
# Run only fast tests (exclude slow tests)
pytest tests/integration/ -v -m "integration and not slow"

# Run only performance tests
pytest tests/integration/ -v -m performance

# Exclude performance tests
pytest tests/integration/ -v -m "integration and not performance"
```

### Coverage Report

```bash
# Run with coverage
pytest tests/integration/ -v -m integration --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest tests/integration/ -v -m integration --cov=app --cov-report=html
open htmlcov/index.html
```

## Test Scenarios

### Test 1: Service Connectivity ✅

**Purpose**: Verify FMP Service is reachable and returns valid data.

**Validates**:
- HTTP connectivity to FMP Service
- Health endpoint returns 200
- Metadata endpoint returns valid asset data
- Response contains required fields

**Duration**: <1 second

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_fmp_service_connectivity -v
```

---

### Test 2: E2E Market Sync (Small) ✅

**Purpose**: Test complete sync flow with 4 symbols (one per asset type).

**Workflow**:
1. POST `/api/v1/graph/markets/sync` with 4 symbols
2. Knowledge-Graph fetches from FMP Service
3. Knowledge-Graph creates MARKET nodes in Neo4j
4. Knowledge-Graph creates SECTOR nodes
5. Knowledge-Graph creates BELONGS_TO_SECTOR relationships
6. Verify data via GET `/api/v1/graph/markets`

**Symbols**: `["AAPL", "EURUSD", "GCUSD", "BTCUSD"]`

**Expected**:
- sync_id returned
- status: "completed" or "partial"
- 3-4 markets synced (allow 1 failure)
- 3-4 MARKET nodes in Neo4j
- 3-4 SECTOR nodes in Neo4j

**Duration**: 2-5 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_e2e_market_sync_small -v
```

---

### Test 3: E2E Market Sync (Full) ✅

**Purpose**: Test complete sync flow with all 40 default symbols.

**Validates**:
- Large batch sync performance
- All 4 asset types handled correctly
- 14 SECTOR nodes created (11 GICS + 3 asset-specific)
- All 40 BELONGS_TO_SECTOR relationships created
- Query performance on larger dataset

**Expected**:
- 35-40 markets synced (allow 5 failures)
- Duration: <10 seconds
- 4 asset types present
- 10+ sectors created

**Duration**: 5-10 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_e2e_market_sync_full -v -m slow
```

**Marker**: `@pytest.mark.slow`

---

### Test 4: Idempotency ✅

**Purpose**: Verify MERGE operations don't create duplicates.

**Workflow**:
1. Sync symbols (first time)
2. Count markets in Neo4j
3. Sync same symbols again
4. Count markets again
5. Verify counts are identical

**Validates**:
- MERGE operations are idempotent
- No duplicate MARKET nodes
- No duplicate relationships
- `updated_at` timestamp changes

**Duration**: 3-5 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_sync_idempotency -v
```

---

### Test 5: Partial Failure Handling ✅

**Purpose**: Test graceful handling of invalid symbols.

**Scenario**: Mix of valid and invalid symbols
- Valid: `AAPL`, `EURUSD`, `BTCUSD`
- Invalid: `INVALID1`, `NOTFOUND`

**Validates**:
- status: "partial" (some succeeded, some failed)
- Valid symbols are synced to Neo4j
- Invalid symbols don't corrupt database
- Errors are tracked in response

**Duration**: 2-4 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_partial_failure_handling -v
```

---

### Test 6: Neo4j Data Integrity ✅

**Purpose**: Validate synced data structure and types.

**Validates**:
- MARKET nodes have all required properties
- Data types are correct (strings, floats, booleans, timestamps)
- Timestamps are ISO format
- SECTOR relationships are correct
- Related markets are returned

**Duration**: 2-4 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_neo4j_data_integrity -v
```

---

### Test 7: Performance Benchmarks ✅

**Purpose**: Ensure sync and query operations meet performance targets.

**Benchmarks**:
- Small sync (4 symbols): <5 seconds
- Full sync (40 symbols): <10 seconds
- Query response: <100ms (p95)

**Measures**:
- Sync duration
- Query duration (5 iterations)
- Throughput (symbols/second)
- p95 latency

**Duration**: 5-8 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_sync_performance -v -m performance
```

**Marker**: `@pytest.mark.performance`

---

### Test 8: Error Recovery (FMP Service Down) ⏭️

**Purpose**: Test graceful handling when FMP Service is unavailable.

**Status**: ⚠️ **SKIPPED** (requires service orchestration)

**Note**: This test requires ability to stop/start FMP Service container.
Implement in CI/CD environment using docker-compose profiles.

**Expected Behavior** (when implemented):
- HTTP 503 returned
- Error message includes retry information
- No partial data corruption in Neo4j

**Command** (when implemented):
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_error_recovery_fmp_service_down -v
```

---

### Test 9: Market Detail Query ✅

**Purpose**: Test detailed market endpoint with relationships.

**Validates**:
- Market detail endpoint returns comprehensive data
- Sector information is included (if available)
- Related markets are returned (same sector)
- Organizations linked via TICKER relationship (if any)

**Duration**: 2-4 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_market_detail_query -v
```

---

### Test 10: Pagination and Filtering ✅

**Purpose**: Test market list endpoint features.

**Validates**:
- Pagination (page, page_size)
- Asset type filter
- Sector filter
- Search filter
- Total count accuracy

**Duration**: 5-8 seconds

**Command**:
```bash
pytest tests/integration/test_fmp_kg_integration.py::test_market_list_pagination_and_filtering -v -m slow
```

**Marker**: `@pytest.mark.slow`

---

## Environment Configuration

### Environment Variables

Override default service URLs using environment variables:

```bash
# Custom service URLs (default: localhost)
export KNOWLEDGE_GRAPH_URL="http://knowledge-graph:8111"
export FMP_SERVICE_URL="http://fmp-service:8109"
export NEO4J_URL="bolt://neo4j:7687"

# Run tests with custom config
pytest tests/integration/ -v -m integration
```

### Docker Compose Test Profile

For CI/CD environments, create a test-specific compose file:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  knowledge-graph-test:
    build: ./services/knowledge-graph-service
    environment:
      - NEO4J_URI=bolt://neo4j-test:7687
      - FMP_SERVICE_URL=http://fmp-service-test:8109
    depends_on:
      - neo4j-test
      - fmp-service-test
    networks:
      - test_network

  neo4j-test:
    image: neo4j:5.12
    environment:
      - NEO4J_AUTH=neo4j/testpassword
    networks:
      - test_network

  fmp-service-test:
    build: ./services/fmp-service
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@postgres-test/test_db
    networks:
      - test_network

networks:
  test_network:
    driver: bridge
```

**Usage**:
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
sleep 10

# Run tests
pytest tests/integration/ -v -m integration

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Debugging Failed Tests

### View Logs

```bash
# Service logs
docker compose logs knowledge-graph-service
docker compose logs fmp-service
docker compose logs neo4j

# Pytest log (detailed)
cat services/knowledge-graph-service/tests/pytest.log
```

### Enable Debug Logging

```bash
# Run tests with verbose logging
pytest tests/integration/ -v -m integration --log-cli-level=DEBUG

# Or set in pytest.ini
log_cli = true
log_cli_level = DEBUG
```

### Check Service Health

```bash
# FMP Service
curl http://localhost:8109/health | jq

# Knowledge-Graph Service
curl http://localhost:8111/health | jq

# Neo4j (via Knowledge-Graph)
curl http://localhost:8111/health | jq '.neo4j'
```

### Inspect Neo4j Database

```bash
# Connect to Neo4j browser
open http://localhost:7474

# Or use Cypher queries via Knowledge-Graph
curl http://localhost:8111/api/v1/graph/markets/stats | jq
```

### Common Issues

**1. Connection Refused**
```
httpx.ConnectError: Connection refused
```
**Solution**: Ensure Docker Compose stack is running:
```bash
docker compose up -d
docker compose ps
```

**2. Neo4j Not Connected**
```
AssertionError: Neo4j not connected
```
**Solution**: Check Neo4j container health:
```bash
docker compose logs neo4j
docker compose restart neo4j
```

**3. Test Timeout**
```
asyncio.TimeoutError
```
**Solution**: Increase timeout or check service performance:
```bash
# Check service response times
time curl http://localhost:8109/api/v1/metadata/bulk?symbols=AAPL
time curl http://localhost:8111/api/v1/graph/markets
```

**4. FMP Service Errors**
```
FMPServiceError: Rate limit exceeded
```
**Solution**: FMP API has 300 calls/day limit. Use `force_refresh=False` in tests
or implement response caching in FMP Service.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      neo4j:
        image: neo4j:5.12
        env:
          NEO4J_AUTH: neo4j/testpassword
        ports:
          - 7687:7687

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd services/knowledge-graph-service
          pip install -r requirements.txt

      - name: Start FMP Service
        run: |
          docker compose up -d fmp-service
          sleep 10

      - name: Run integration tests
        run: |
          cd services/knowledge-graph-service
          pytest tests/integration/ -v -m "integration and not slow"

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: always()
```

## Test Data Cleanup

### Manual Cleanup

```bash
# Clear all MARKET and SECTOR nodes
curl -X POST http://localhost:8111/api/v1/admin/clear-markets

# Or via Neo4j Cypher
docker compose exec neo4j cypher-shell -u neo4j -p your_password \
  "MATCH (m:MARKET) DETACH DELETE m"
docker compose exec neo4j cypher-shell -u neo4j -p your_password \
  "MATCH (s:SECTOR) DETACH DELETE s"
```

### Automated Cleanup (Future)

Implement cleanup fixtures:
```python
@pytest.fixture(scope="function", autouse=True)
async def cleanup_neo4j_after_test():
    yield
    # Cleanup after each test
    async with Neo4jService() as neo4j:
        await neo4j.execute_query("MATCH (m:MARKET) DETACH DELETE m")
```

## Performance Baselines

Expected performance on standard hardware (4 cores, 8GB RAM):

| Test Scenario | Duration | Throughput |
|---------------|----------|------------|
| Service connectivity | <1s | N/A |
| Small sync (4 symbols) | 2-5s | 0.8-2 symbols/s |
| Full sync (40 symbols) | 5-10s | 4-8 symbols/s |
| Idempotency test | 3-5s | N/A |
| Query p95 latency | <100ms | 10+ req/s |
| Market detail query | <50ms | 20+ req/s |

**Note**: Performance varies based on:
- FMP API response time (external dependency)
- Neo4j write performance (disk I/O)
- Network latency (service-to-service)

## Contributing

When adding new integration tests:

1. **Follow naming convention**: `test_<scenario>_<description>`
2. **Add docstrings**: Explain purpose, workflow, expected results
3. **Use markers**: `@pytest.mark.integration`, `@pytest.mark.slow`, etc.
4. **Update this README**: Add test to scenarios section
5. **Verify on clean DB**: Test should work on empty Neo4j database

## Support

For issues with integration tests:

1. Check service logs: `docker compose logs`
2. Verify prerequisites: Services running, dependencies installed
3. Review test output: `pytest -v --log-cli-level=DEBUG`
4. Consult main README: `/services/knowledge-graph-service/README.md`
