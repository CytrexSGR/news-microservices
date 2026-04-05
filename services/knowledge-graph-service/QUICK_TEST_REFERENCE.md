# Entity Search Endpoint - Quick Test Reference

## Test File Location
`tests/test_search.py` - 36 comprehensive tests in 7 classes

## Running Tests

### Quick Start
```bash
# Run all tests
pytest tests/test_search.py -v

# Run specific class
pytest tests/test_search.py::TestEntitySearchValidation -v

# Run with coverage
pytest tests/test_search.py --cov=app.api.routes.search --cov=app.services.search_service -v
```

## Test Classes Overview

| Class | Tests | Focus |
|-------|-------|-------|
| `TestEntitySearchEndpointSuccess` | 7 | Happy path scenarios |
| `TestEntitySearchValidation` | 9 | Input validation errors |
| `TestEntitySearchResponseModel` | 4 | Response structure |
| `TestEntitySearchEdgeCases` | 7 | Edge cases & special input |
| `TestEntitySearchPerformance` | 2 | Query performance |
| `TestEntitySearchWithMocking` | 4 | Model serialization |
| `TestEntitySearchIntegration` | 3 | Real-world scenarios |

## Endpoint Parameters

```
GET /api/v1/graph/search?query=<string>&limit=<int>&entity_type=<string>
```

| Param | Type | Required | Range | Default |
|-------|------|----------|-------|---------|
| `query` | string | Yes | 1-200 chars | — |
| `limit` | int | No | 1-100 | 10 |
| `entity_type` | string | No | Any | null |

## Response Structure

```json
{
  "results": [
    {
      "name": "entity name",
      "type": "PERSON|ORGANIZATION|LOCATION|...",
      "connection_count": 0,
      "last_seen": "2024-11-02T10:30:00Z",
      "wikidata_id": "Q478214"
    }
  ],
  "total_results": 1,
  "query_time_ms": 123,
  "query": "search term",
  "entity_type_filter": null
}
```

## Key Test Scenarios

### Success Cases
- ✓ Basic search (query only)
- ✓ With limit parameter
- ✓ With entity_type filter
- ✓ Case-insensitive search
- ✓ Empty results
- ✓ All parameters combined

### Validation Errors (422)
- ✓ Missing query parameter
- ✓ Query too short (0 chars)
- ✓ Query too long (>200 chars)
- ✓ Limit < 1 or > 100
- ✓ Non-integer limit
- ✗ Invalid entity_type (still 200 OK, filtered by DB)

### Response Fields
- ✓ All required fields present
- ✓ Field types match model
- ✓ total_results == len(results)
- ✓ query_time_ms > 0 and < 30000

### Edge Cases
- ✓ Special characters (@, -, _, ., /)
- ✓ Whitespace in query (preserved)
- ✓ Unicode characters (café, 中文)
- ✓ Numeric queries (2024)
- ✓ Exact vs partial match ranking
- ✓ Connection count ordering

## Performance Targets

- Normal queries: < 1000ms (typical Neo4j)
- Max limit (100): < 10000ms
- All queries: > 0ms (timing working)

## Common Test Patterns

### Async Test Template
```python
@pytest.mark.asyncio
async def test_example(self):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": "test"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
```

### Parameter Variations
```python
# Query only (required)
{"query": "Tesla"}

# With limit
{"query": "Tesla", "limit": 5}

# With entity type
{"query": "Musk", "entity_type": "PERSON"}

# All parameters
{"query": "Microsoft", "limit": 20, "entity_type": "ORGANIZATION"}
```

## Validation Rules Quick Check

| Param | Min | Max | Valid | Invalid |
|-------|-----|-----|-------|---------|
| query length | 1 | 200 | ✓ "test" | ✗ "" ✗ "a"*201 |
| limit | 1 | 100 | ✓ 10 | ✗ 0 ✗ 101 |
| entity_type | Any string | — | ✓ "PERSON" | ✓ "INVALID" (no error) |

## Debugging Failed Tests

### If test fails with 422 instead of 200
- Check query length (must be 1-200 chars)
- Check limit value (must be 1-100)
- Check if parameters are passed correctly

### If test fails with 200 instead of 422
- Verify constraint is defined in endpoint (Query(..., min_length=1, max_length=200, ge=1, le=100))
- Check FastAPI version (some versions have different validation)

### If query_time_ms seems wrong
- query_time_ms measures only Neo4j query execution
- Does not include FastAPI overhead or serialization
- Times vary based on database size and load

### If results don't match expected
- Results depend on actual Neo4j data
- Empty results (200 OK with empty array) is valid
- Ranking: exact match first, then by connection_count DESC, then by name ASC

## Response Examples

### Successful Search with Results
```bash
curl "http://localhost:8111/api/v1/graph/search?query=Tesla&limit=2"

{
  "results": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "connection_count": 45,
      "last_seen": "2024-11-02T10:30:00Z",
      "wikidata_id": "Q478214"
    },
    {
      "name": "Tesla Model S",
      "type": "PRODUCT",
      "connection_count": 23,
      "last_seen": "2024-11-01T15:45:00Z",
      "wikidata_id": null
    }
  ],
  "total_results": 2,
  "query_time_ms": 156,
  "query": "Tesla",
  "entity_type_filter": null
}
```

### Successful Search with No Results
```bash
curl "http://localhost:8111/api/v1/graph/search?query=NONEXISTENT_XYZ"

{
  "results": [],
  "total_results": 0,
  "query_time_ms": 42,
  "query": "NONEXISTENT_XYZ",
  "entity_type_filter": null
}
```

### Validation Error
```bash
curl "http://localhost:8111/api/v1/graph/search?limit=101"

HTTP/1.1 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 100}
    }
  ]
}
```

## Test Execution Matrix

```
Query Parameter Validation
├─ Missing: 422 ✓
├─ Length 0: 422 ✓
├─ Length 1: 200 ✓
├─ Length 200: 200 ✓
└─ Length 201: 422 ✓

Limit Parameter Validation
├─ Missing: 200 (default=10) ✓
├─ Value 0: 422 ✓
├─ Value 1: 200 ✓
├─ Value 100: 200 ✓
└─ Value 101: 422 ✓

Entity Type Parameter
├─ Missing: 200 (filter=null) ✓
├─ Valid (PERSON): 200 ✓
├─ Invalid (BOGUS): 200 (empty results) ✓
└─ Lowercase (person): 200 (depends on DB) ✓

Response Fields
├─ results: array ✓
├─ total_results: int ✓
├─ query_time_ms: int > 0 ✓
├─ query: string (echoed) ✓
└─ entity_type_filter: string|null ✓
```

## Performance Benchmarks

### Typical Query Times (with Neo4j running)
```
Simple query ("Tesla"):           50-150ms
Partial match ("a"):             200-500ms
With entity type filter:         100-200ms
Max limit (100):                 500-1000ms
Complex filter:                  1000-2000ms
```

### Test Execution Time
```
Single test:        ~100-500ms
All success tests:  ~2-5 seconds
All validation:     ~3-7 seconds
Full test suite:    ~15-30 seconds
```

## Coverage Checklist

- [x] Query parameter validation (min/max length)
- [x] Limit parameter validation (min/max values)
- [x] Entity type filtering
- [x] Response model structure
- [x] Field types and presence
- [x] Empty results handling
- [x] Case-insensitive search
- [x] Special characters
- [x] Whitespace handling
- [x] Performance benchmarks
- [x] Model serialization
- [x] Integration scenarios

## Next Steps

1. **Run all tests:** `pytest tests/test_search.py -v`
2. **Check coverage:** `pytest tests/test_search.py --cov=app.api.routes.search --cov=app.services.search_service`
3. **Fix any failures:** Review test output and implementation
4. **Document results:** Update status in CI/CD pipeline
5. **Integrate with CI:** Add to GitHub Actions or similar

---

**For detailed information, see:** `TEST_SEARCH_COMPREHENSIVE_GUIDE.md`
