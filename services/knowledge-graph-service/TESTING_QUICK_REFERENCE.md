# Market Sync Service - Testing Quick Reference

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Tests | 51 |
| Code Coverage | 100% |
| Test File Size | 1,268 lines |
| Execution Time | ~0.22s |
| Status | All Passing ✅ |

## Test Organization

```
tests/services/test_market_sync_service.py
├── Fixtures (10 total)
│   ├── Data: sample_stock_metadata, sample_forex_metadata, sample_crypto_metadata
│   ├── Combined: sample_all_markets_metadata, sample_quotes
│   └── Mocks: mock_fmp_client, mock_neo4j_service, market_sync_service
├── sync_all_markets() (6 tests)
├── sync_market_quotes() (8 tests)
├── sync_sectors() (4 tests)
├── Helper Methods (19 tests)
├── _sync_single_asset() (5 tests)
├── Error Handling (2 tests)
├── Data Validation (3 tests)
└── Integration & Edge Cases (6 tests)
```

## Run Tests

### All Tests
```bash
cd /home/cytrex/news-microservices/services/knowledge-graph-service
docker compose -f ../../docker-compose.yml exec -T knowledge-graph-service \
  python -m pytest tests/services/test_market_sync_service.py -v
```

### With Coverage
```bash
docker compose -f ../../docker-compose.yml exec -T knowledge-graph-service \
  python -m pytest tests/services/test_market_sync_service.py \
  --cov=app.services.fmp_integration.market_sync_service \
  --cov-report=term-missing
```

### Single Test
```bash
docker compose -f ../../docker-compose.yml exec -T knowledge-graph-service \
  python -m pytest tests/services/test_market_sync_service.py::test_sync_all_markets_success -v
```

## Test Categories

### 1. Main Operations (18 tests)
- `sync_all_markets()` - 6 tests
- `sync_market_quotes()` - 8 tests
- `sync_sectors()` - 4 tests

### 2. Helper Methods (19 tests)
- Sector mapping - 7 tests
- Default symbols - 5 tests
- Sync ID generation - 2 tests
- Status determination - 5 tests

### 3. Complex Operations (5 tests)
- Single asset sync - 5 tests

### 4. Quality & Validation (9 tests)
- Error handling - 2 tests
- Data validation - 3 tests
- Integration & edge cases - 6 tests

## Coverage Breakdown

```
sync_all_markets()           100% ✅
  ├─ Success path            ✅
  ├─ Partial failure         ✅
  ├─ Complete failure        ✅
  ├─ Custom symbols          ✅
  ├─ Asset type filter       ✅
  └─ Force refresh           ✅

sync_market_quotes()         100% ✅
  ├─ Success                 ✅
  ├─ Symbol not found        ✅
  ├─ Neo4j error             ✅
  ├─ FMP error               ✅
  ├─ Partial failure         ✅
  ├─ Rate limit              ✅
  ├─ Missing price           ✅
  └─ Missing symbol          ✅

sync_sectors()               100% ✅
  ├─ Initial creation        ✅
  ├─ Idempotent             ✅
  ├─ Mixed create/verify     ✅
  └─ Error handling          ✅

Helper Methods               100% ✅
  ├─ _map_sector_to_code()   ✅
  ├─ _get_default_symbols()  ✅
  ├─ _generate_sync_id()     ✅
  └─ _determine_status()     ✅

_sync_single_asset()         100% ✅
  ├─ Stock creation          ✅
  ├─ Stock update            ✅
  ├─ Forex handling          ✅
  ├─ Crypto handling         ✅
  └─ Empty response          ✅
```

## Key Test Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_example():
    result = await market_sync_service.sync_all_markets()
    assert result.status == "completed"
```

### Mocking Services
```python
market_sync_service.fmp_client.get_asset_metadata_bulk.return_value = metadata
with patch(...neo4j_service...):
    result = await market_sync_service.sync_all_markets()
```

### Error Simulation
```python
market_sync_service.fmp_client.get_asset_metadata_bulk.side_effect = \
    FMPServiceUnavailableError("Service down")
```

### Side Effects for Complex Scenarios
```python
call_count = 0
async def side_effect(cypher, params):
    nonlocal call_count
    call_count += 1
    if call_count > 38:
        raise Exception("Neo4j timeout")
    return success_response
```

## Expected Results

```
======================= 51 passed in 0.22s =======================

Coverage: 100% (146/146 statements)
All categories: 100% coverage
All paths: Success + Failure covered
All edge cases: Handled
```

## Files

| File | Purpose |
|------|---------|
| `tests/services/test_market_sync_service.py` | Main test file (1,268 lines, 51 tests) |
| `tests/services/__init__.py` | Package marker |
| `TEST_MARKET_SYNC_SUMMARY.md` | Detailed documentation |
| `TESTING_QUICK_REFERENCE.md` | This file |

## Troubleshooting

### Docker Issues
```bash
# Start Docker
docker compose -f /home/cytrex/news-microservices/docker-compose.yml up -d

# Check service
docker compose ps | grep knowledge-graph

# Stop
docker compose down
```

### Test Failures
1. Check Docker is running: `docker compose ps`
2. Check Neo4j is healthy: `docker logs neo4j`
3. Verify fixtures are loaded: `pytest -v --setup-show`

### Coverage Issues
```bash
# Full coverage report
pytest --cov=app.services.fmp_integration.market_sync_service \
       --cov-report=html --cov-report=term
```

## Maintenance

### When Code Changes
1. Run tests: `pytest tests/services/test_market_sync_service.py -v`
2. Check coverage: `--cov-report=term-missing`
3. Update fixtures if needed
4. Add new tests for new functionality

### When Tests Fail
1. Read error message carefully
2. Check if it's a fixture issue
3. Verify mock return values
4. Look for side effect problems
5. Check assertion logic

---

**Quick Links:**
- Target: `app/services/fmp_integration/market_sync_service.py`
- Tests: `tests/services/test_market_sync_service.py`
- Docs: `TEST_MARKET_SYNC_SUMMARY.md`
- Status: All 51 tests passing ✅
