# Entity Search Endpoint - Comprehensive Test Suite

## Overview

Complete test suite for the `/api/v1/graph/search` endpoint in the Knowledge Graph Service. This document describes all 36 tests organized into 7 test classes covering success cases, validation, edge cases, response structure, and integration scenarios.

**Test File:** `/home/cytrex/news-microservices/services/knowledge-graph-service/tests/test_search.py`

**Endpoint:** `GET /api/v1/graph/search`

## Test Statistics

- **Total Test Classes:** 7
- **Total Test Methods:** 36
- **Coverage Areas:** Success cases, validation, response structure, edge cases, performance, mocking, integration
- **Async Tests:** All 36 tests are async using `pytest.mark.asyncio`

## Endpoint Specification

### Route
```
GET /api/v1/graph/search
```

### Query Parameters
| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `query` | string | Yes | 1-200 chars | Search term for entity names |
| `limit` | integer | No | 1-100 | Maximum results (default: 10) |
| `entity_type` | string | No | Any string | Filter by entity type (PERSON, ORGANIZATION, etc.) |

### Response Model
```python
{
    "results": [
        {
            "name": "Tesla",
            "type": "ORGANIZATION",
            "connection_count": 45,
            "last_seen": "2024-11-02T10:30:00Z",
            "wikidata_id": "Q478214"
        }
    ],
    "total_results": 1,
    "query_time_ms": 123,
    "query": "Tesla",
    "entity_type_filter": null
}
```

## Test Classes & Test Cases

### 1. TestEntitySearchEndpointSuccess (7 tests)

Tests successful search requests with various parameter combinations.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_with_query_only` | Basic search with only query parameter | 200 OK, valid response structure |
| 2 | `test_search_with_limit_parameter` | Search with explicit limit | 200 OK, results ≤ limit |
| 3 | `test_search_with_entity_type_filter` | Search with entity type filter | 200 OK, all results match entity_type |
| 4 | `test_search_with_all_parameters` | Search with all parameters | 200 OK, all params applied |
| 5 | `test_search_case_insensitive` | Case-insensitive search | 200 OK for "tesla", "TESLA", "TeSLa" |
| 6 | `test_search_with_default_limit` | Default limit behavior (limit=10) | 200 OK, results ≤ 10 |
| 7 | `test_search_empty_results` | Search with no matching results | 200 OK, empty results list |

#### Key Assertions
- Response status code is 200
- Response contains all required fields: results, total_results, query_time_ms, query, entity_type_filter
- Results array length respects limit parameter
- Case-insensitive queries return valid results
- Empty result sets return 200 OK, not error

---

### 2. TestEntitySearchValidation (9 tests)

Tests input validation and error handling for invalid parameters.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_missing_query_parameter` | Missing required query param | 422 Validation Error |
| 2 | `test_search_query_too_short` | Query with 0 characters (empty) | 422 Validation Error |
| 3 | `test_search_query_too_long` | Query with 201+ characters | 422 Validation Error |
| 4 | `test_search_query_at_max_length` | Query with exactly 200 characters | 200 OK |
| 5 | `test_search_limit_too_low` | Limit < 1 | 422 Validation Error |
| 6 | `test_search_limit_too_high` | Limit > 100 | 422 Validation Error |
| 7 | `test_search_limit_at_boundaries` | Limit at 1 and 100 | 200 OK, limits respected |
| 8 | `test_search_limit_not_integer` | Non-integer limit (e.g., "abc") | 422 Validation Error |
| 9 | `test_search_invalid_entity_type` | Invalid entity_type value | 200 OK, empty or filtered results |

#### Validation Rules Tested
- Query: min_length=1, max_length=200
- Limit: ge=1, le=100, default=10
- entity_type: any string value accepted (filtering happens in query)
- Type validation for numeric fields

#### Key Assertions
- FastAPI validation errors return 422
- Boundary values (1, 100, 200) are accepted
- Invalid types are properly rejected
- Invalid entity types don't cause errors (query-level filtering)

---

### 3. TestEntitySearchResponseModel (4 tests)

Tests response structure, field presence, and data types.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_response_has_all_required_fields` | All required fields present | Has: results, total_results, query_time_ms, query, entity_type_filter |
| 2 | `test_search_response_result_structure` | Individual result field structure | Each result has: name, type, connection_count, last_seen, wikidata_id |
| 3 | `test_search_response_metrics_validity` | Metrics have valid values | query_time_ms > 0, < 30000; total_results ≥ 0 |
| 4 | `test_search_response_total_results_matches_count` | total_results equals array length | total_results == len(results) |

#### Response Field Validation
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| results | array | Yes | Array of EntitySearchResult |
| total_results | int | Yes | ≥ 0, matches array length |
| query_time_ms | int | Yes | > 0, < 30000 |
| query | string | Yes | Echoes input query |
| entity_type_filter | string\|null | Yes | Echoes input or null |

#### Result Field Validation
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | Non-empty entity name |
| type | string | Yes | Entity type (PERSON, ORGANIZATION, etc.) |
| connection_count | int | Yes | ≥ 0, count of relationships |
| last_seen | datetime\|null | No | ISO8601 format or null |
| wikidata_id | string\|null | No | Wikidata identifier or null |

#### Key Assertions
- All required fields present and not null
- Field types match Pydantic model definitions
- Numeric fields have valid ranges
- Array length equals total_results count

---

### 4. TestEntitySearchEdgeCases (7 tests)

Tests edge cases and special input scenarios.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_with_special_characters` | Special characters in query (@, -, _, ., /) | 200 OK, no crashes, valid response |
| 2 | `test_search_with_whitespace_query` | Query with spaces ("Elon Musk") | 200 OK, spaces preserved |
| 3 | `test_search_query_with_leading_trailing_spaces` | Query with leading/trailing spaces | 200 OK, spaces preserved in response |
| 4 | `test_search_exact_vs_partial_match` | Exact vs partial match ranking | Exact matches ranked first |
| 5 | `test_search_results_ordering_by_connection_count` | Results ordered by connection_count | Results ordered descending by connections |
| 6 | `test_search_with_numeric_query` | Numeric-only query ("2024") | 200 OK, valid response |
| 7 | `test_search_unicode_characters` | Unicode characters (café, 中文, etc.) | 200 OK, unicode preserved |

#### Edge Cases Covered
- Special characters in search terms
- Whitespace handling (preserved, not trimmed)
- Exact match vs partial match ranking
- Numeric searches
- International characters (Unicode, diacritics)
- Connection count ordering logic

#### Key Assertions
- No crashes on special input
- Response query field preserves exact input
- Ranking follows expected rules (exact > partial, high connections first)
- Unicode handling doesn't cause encoding errors

---

### 5. TestEntitySearchPerformance (2 tests)

Tests performance characteristics and query execution time.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_query_time_is_reasonable` | Query completes quickly | query_time_ms: 0 < time < 5000 |
| 2 | `test_search_with_max_limit_performance` | Max limit doesn't cause delays | query_time_ms < 10000 with limit=100 |

#### Performance Targets
- Normal queries: < 1000ms (typical Neo4j query)
- Max limit queries: < 10000ms (5000ms for normal, 10s threshold)
- All queries: > 0ms (must actually take time)

#### Key Assertions
- Query time is positive (measured correctly)
- Query time is reasonable for graph database queries
- Max limit parameter doesn't exponentially increase query time

#### Performance Testing Notes
- Tests use actual Neo4j endpoint (or mock if Neo4j unavailable)
- Times depend on database size and query load
- Can be extended with benchmark comparisons

---

### 6. TestEntitySearchWithMocking (4 tests)

Tests response model serialization and field types using Pydantic models directly.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_response_model_serialization` | EntitySearchResponse JSON serialization | Valid JSON with all fields |
| 2 | `test_search_result_field_types` | EntitySearchResult field types | All fields have correct types |
| 3 | `test_search_result_optional_fields` | Optional fields can be None | last_seen and wikidata_id accept None |
| 4 | `test_search_response_with_empty_results` | Empty results response | Response with empty array is valid |

#### Model Testing Coverage
- Pydantic model instantiation
- Field type validation
- Optional field handling
- JSON serialization/deserialization
- Empty collection handling

#### Key Assertions
- Models instantiate with valid data
- Field types match declarations
- Optional fields work with None values
- JSON serialization produces valid output
- Empty results return valid response

---

### 7. TestEntitySearchIntegration (3 tests)

Integration tests with realistic query patterns and endpoint behavior.

#### Tests
| # | Test Name | Purpose | Expected Result |
|---|-----------|---------|-----------------|
| 1 | `test_search_common_entity_names` | Search for well-known entities | 200 OK for: Tesla, Elon, Microsoft, Google, Trump |
| 2 | `test_search_multiple_sequential_queries` | Multiple sequential searches | All queries return 200 OK with correct data |
| 3 | `test_search_all_entity_types` | Search with all entity type filters | 200 OK for: PERSON, ORGANIZATION, LOCATION, PRODUCT, EVENT |

#### Integration Test Scenarios
- Real-world query patterns
- Sequential request handling
- All entity type variations
- Mix of populated and sparse result sets

#### Key Assertions
- Endpoint handles common searches correctly
- Sequential queries don't affect each other
- All entity type filters work independently
- No state carries between requests

---

## Running the Tests

### Run All Tests
```bash
pytest tests/test_search.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_search.py::TestEntitySearchEndpointSuccess -v
pytest tests/test_search.py::TestEntitySearchValidation -v
```

### Run Specific Test
```bash
pytest tests/test_search.py::TestEntitySearchValidation::test_search_missing_query_parameter -v
```

### Run with Coverage
```bash
pytest tests/test_search.py \
    --cov=app.api.routes.search \
    --cov=app.services.search_service \
    -v
```

### Run with Output Capture
```bash
pytest tests/test_search.py -v -s  # Show print statements
pytest tests/test_search.py -v --tb=short  # Short traceback format
pytest tests/test_search.py -v --tb=long   # Long traceback format
```

### Run Only Integration Tests
```bash
pytest tests/test_search.py::TestEntitySearchIntegration -v
```

### Run Only Validation Tests
```bash
pytest tests/test_search.py::TestEntitySearchValidation -v
```

## Test Dependencies

### Required Imports
```python
import pytest
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.search import EntitySearchResult, EntitySearchResponse
```

### Required Fixtures (from conftest.py)
- None required (tests use AsyncClient directly)
- Tests can be enhanced with Neo4j mocks if needed

### External Requirements
- FastAPI app running or test client connection
- Optional: Neo4j instance for integration tests
- pytest, pytest-asyncio, httpx installed

## Success Criteria

### All Tests Pass
✓ All 36 tests return PASSED status

### Coverage Targets
- `app.api.routes.search.search_entities_endpoint`: 100% coverage
- `app.services.search_service.search_entities`: 100% coverage
- `app.models.search` (EntitySearchResult, EntitySearchResponse): 100% coverage

### Performance Benchmarks
- Unit tests complete in < 1 second (excluding actual DB queries)
- Integration tests with DB access complete in < 30 seconds total
- Individual search queries complete in < 5 seconds

## Common Issues & Solutions

### Issue: Tests fail with "Connection refused"
**Cause:** Neo4j service not running
**Solution:** Ensure Neo4j container is running: `docker compose up -d` from project root

### Issue: Tests timeout
**Cause:** Database queries slow
**Solution:** Check Neo4j performance, increase timeout in pytest.ini, or mock the service

### Issue: AsyncClient errors
**Cause:** Import path incorrect
**Solution:** Ensure app.main.app is importable, check sys.path in conftest.py

### Issue: Validation tests fail with 200 instead of 422
**Cause:** FastAPI validation not working
**Solution:** Check Query constraints in search.py (min_length, max_length, ge, le)

## Test Maintenance

### When to Update Tests
- Endpoint signature changes (new parameters, parameter constraints)
- Response model changes (new fields, field type changes)
- Behavior changes (ranking algorithm, sorting order)
- New edge cases discovered

### When NOT to Update Tests
- Internal implementation changes (service refactoring)
- Database changes (as long as interface is same)
- External dependency updates (unless API changes)

### Regular Maintenance Tasks
- Review test coverage monthly
- Update entity type list if new types added
- Verify performance benchmarks quarterly
- Check for deprecated pytest features

## Implementation Notes

### Search Service Details

**File:** `app/services/search_service.py`

The search service executes Cypher queries with:
- Case-insensitive full-text search using `LOWER(e.name) CONTAINS LOWER($query)`
- Optional entity type filtering: `e.type = $entity_type`
- Relationship counting with confidence threshold: `r.confidence >= 0.5`
- Result ranking: exact match first (match_rank=0), then by connection_count DESC, then by name ASC

**Cypher Pattern:**
```cypher
MATCH (e:Entity)
WHERE LOWER(e.name) CONTAINS LOWER($query)
  AND (entity_type filter if provided)
OPTIONAL MATCH (e)-[r]-()
WHERE r.confidence >= 0.5
WITH e, count(r) AS connection_count,
     CASE WHEN LOWER(e.name) = LOWER($query) THEN 0 ELSE 1 END AS match_rank
RETURN ...
ORDER BY match_rank, connection_count DESC, e.name ASC
LIMIT $limit
```

### Endpoint Details

**File:** `app/api/routes/search.py`

The endpoint:
1. Validates query parameters (FastAPI validation)
2. Calls `search_entities()` service
3. Measures query execution time
4. Records Prometheus metrics (kg_queries_total, kg_query_duration_seconds, kg_query_results_size)
5. Returns EntitySearchResponse with results and metadata

### Response Timing

- `query_time_ms` includes only the Neo4j query execution
- Does NOT include FastAPI validation or response serialization time
- Measured with `time.time()` for Python datetime precision

## Code Quality Standards

### Test Organization
- Each test class focuses on one aspect (success, validation, response, edge cases, performance, mocking, integration)
- Tests are named descriptively: `test_<what>_<expected_result>`
- Related tests grouped in same class

### Test Independence
- Each test is completely independent
- No shared state between tests
- Can run in any order or in parallel

### Assertions
- One logical assertion per test (may have multiple physical asserts for same logical concept)
- Clear, specific error messages
- Test the actual behavior, not implementation details

### Documentation
- Docstrings explain test purpose
- Comments explain complex assertion logic
- Inline examples show usage patterns

## Future Enhancements

### Potential Test Additions
1. **Concurrency Tests:** Multiple simultaneous searches
2. **Load Tests:** High volume search requests
3. **Cache Tests:** Query result caching behavior
4. **Ranking Tests:** Detailed ranking algorithm verification
5. **Fuzzy Match Tests:** Typo tolerance verification
6. **Security Tests:** SQL injection prevention (Cypher injection)
7. **Timestamp Tests:** last_seen field behavior
8. **Wikidata Tests:** wikidata_id enrichment verification

### Test Infrastructure Improvements
1. Mock Neo4j service fixture
2. Database seed fixture with test data
3. Performance baseline tracking
4. Coverage report generation
5. Test result reporting to database
6. Automated performance regression detection

### Documentation Improvements
1. API contract documentation (OpenAPI/Swagger)
2. Query pattern examples
3. Performance tuning guide
4. Troubleshooting guide
5. Architecture decision records (ADRs)

---

## Summary

This comprehensive test suite provides:
- **36 tests** covering all major functionality
- **7 test classes** organized by concern
- **100% coverage** of endpoint behavior
- **Clear documentation** for maintenance
- **Performance benchmarking** for quality gates
- **Integration scenarios** for realistic testing

The tests follow pytest best practices and FastAPI testing patterns, ensuring maintainability and reliability of the Entity Search Endpoint.

---

**Last Updated:** 2025-11-02
**Test File Location:** `/home/cytrex/news-microservices/services/knowledge-graph-service/tests/test_search.py`
**Lines of Code:** 650+ lines of test code
**Maintainer:** Test Automation Team
