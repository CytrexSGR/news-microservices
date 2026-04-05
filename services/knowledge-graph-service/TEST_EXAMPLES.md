# Entity Search Endpoint - Test Examples & Patterns

## Overview

Practical examples and patterns used in the comprehensive test suite for the Entity Search Endpoint.

## Basic Test Structure

### Simple Success Test
```python
@pytest.mark.asyncio
async def test_search_with_query_only(self):
    """Test basic search with only required query parameter."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": "Tesla"}
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "results" in data
    assert "total_results" in data
    assert "query_time_ms" in data
```

### Validation Error Test
```python
@pytest.mark.asyncio
async def test_search_query_too_long(self):
    """Test that query longer than 200 characters is rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        long_query = "a" * 201  # 201 characters
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": long_query}
        )

    # Query exceeds max_length=200
    assert response.status_code == 422
```

## Pattern 1: Parameter Variations

### Testing Different Query Types
```python
@pytest.mark.asyncio
async def test_search_with_various_queries(self):
    """Test different query patterns."""
    test_queries = [
        ("Tesla", "Single word"),
        ("Elon Musk", "Two words"),
        ("Tesla Inc.", "Word with punctuation"),
        ("2024", "Numeric"),
        ("test@domain", "With special char"),
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for query, description in test_queries:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": query}
            )

            assert response.status_code == 200, f"Failed for: {description}"
            data = response.json()
            assert data["query"] == query
```

### Testing Limit Boundaries
```python
@pytest.mark.asyncio
async def test_search_limit_boundaries(self):
    """Test limit parameter at valid boundaries."""
    valid_limits = [1, 10, 50, 100]
    invalid_limits = [0, 101, 1000, -1]

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Valid limits
        for limit in valid_limits:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": limit}
            )
            assert response.status_code == 200

        # Invalid limits
        for limit in invalid_limits:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": limit}
            )
            assert response.status_code == 422
```

## Pattern 2: Response Validation

### Complete Response Validation
```python
@pytest.mark.asyncio
async def test_search_response_complete_validation(self):
    """Validate complete response structure."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": "test", "limit": 5}
        )

    assert response.status_code == 200
    data = response.json()

    # Top-level fields
    assert isinstance(data["results"], list)
    assert isinstance(data["total_results"], int)
    assert isinstance(data["query_time_ms"], int)
    assert isinstance(data["query"], str)
    assert data["entity_type_filter"] is None or isinstance(data["entity_type_filter"], str)

    # Metrics validation
    assert data["total_results"] == len(data["results"])
    assert data["query_time_ms"] > 0
    assert data["query"] == "test"

    # Result validation
    for result in data["results"]:
        assert "name" in result
        assert "type" in result
        assert "connection_count" in result
        assert isinstance(result["connection_count"], int)
        assert result["connection_count"] >= 0
```

### Detailed Result Structure Validation
```python
@pytest.mark.asyncio
async def test_search_result_structure_detailed(self):
    """Validate detailed structure of search results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": "a", "limit": 3}
        )

    data = response.json()

    if data["results"]:
        for i, result in enumerate(data["results"]):
            # Required fields
            assert result["name"], f"Result {i}: name is empty"
            assert result["type"], f"Result {i}: type is empty"
            assert "connection_count" in result

            # Field types
            assert isinstance(result["name"], str)
            assert isinstance(result["type"], str)
            assert isinstance(result["connection_count"], int)

            # Optional fields
            if result["last_seen"]:
                # Should be ISO8601 format if present
                assert "T" in result["last_seen"] or result["last_seen"] is None

            # Wikidata ID format if present
            if result["wikidata_id"]:
                assert result["wikidata_id"].startswith("Q")
```

## Pattern 3: Edge Case Testing

### Special Characters Handling
```python
@pytest.mark.asyncio
async def test_search_special_characters_comprehensive(self):
    """Test handling of various special characters."""
    special_chars_queries = [
        "test@domain.com",
        "elon-musk",
        "test_query",
        "c++",
        "#hashtag",
        "$dollar",
        "100%",
        "test/path",
        "test\\path",
        "test|pipe",
        "test&ampersand",
        "test(parenthesis)",
        "test[bracket]",
        "test{brace}",
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for query in special_chars_queries:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": query}
            )

            # Should not crash
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                data = response.json()
                # Query should be preserved exactly
                assert data["query"] == query
```

### Whitespace Handling
```python
@pytest.mark.asyncio
async def test_search_whitespace_variations(self):
    """Test how whitespace is handled."""
    whitespace_queries = [
        ("test", "No whitespace"),
        (" test", "Leading space"),
        ("test ", "Trailing space"),
        (" test ", "Leading and trailing"),
        ("  test  ", "Multiple spaces"),
        ("test test", "Internal space"),
        ("\ttest", "Tab character"),
        ("Elon Musk", "Two words with space"),
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for query, description in whitespace_queries:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": query}
            )

            assert response.status_code == 200
            data = response.json()

            # Whitespace should be preserved in response
            assert data["query"] == query, f"Failed for: {description}"
```

### Unicode and International Characters
```python
@pytest.mark.asyncio
async def test_search_unicode_comprehensive(self):
    """Test Unicode and international character support."""
    unicode_queries = [
        "café",           # French with accent
        "naïve",          # Diaeresis
        "москва",         # Russian (Moscow)
        "北京",            # Chinese (Beijing)
        "مصر",            # Arabic (Egypt)
        "עברית",         # Hebrew
        "日本",           # Japanese (Japan)
        "한국",           # Korean (Korea)
        "emoji🚗test",    # With emoji
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for query in unicode_queries:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": query}
            )

            # Should handle Unicode without errors
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                data = response.json()
                assert data["query"] == query
```

## Pattern 4: Filtering and Ordering

### Entity Type Filtering
```python
@pytest.mark.asyncio
async def test_search_entity_type_filtering(self):
    """Verify entity type filtering works correctly."""
    entity_types = ["PERSON", "ORGANIZATION", "LOCATION"]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for entity_type in entity_types:
            response = await client.get(
                "/api/v1/graph/search",
                params={
                    "query": "test",
                    "entity_type": entity_type
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Verify filter is applied
            assert data["entity_type_filter"] == entity_type

            # All results should match the type
            for result in data["results"]:
                assert result["type"] == entity_type, \
                    f"Expected {entity_type}, got {result['type']}"
```

### Result Ordering
```python
@pytest.mark.asyncio
async def test_search_result_ordering(self):
    """Verify results are ordered by connection count."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/search",
            params={"query": "test", "limit": 20}
        )

    data = response.json()
    results = data["results"]

    if len(results) > 1:
        # Check if ordered by connection count (descending)
        # Note: May have exact matches first (implementation detail)
        for i in range(len(results) - 1):
            current = results[i]
            next_result = results[i + 1]

            # Either connection count is higher or equal
            assert current["connection_count"] >= next_result["connection_count"] or \
                   current["name"].lower() == "test"  # Exact match exception
```

## Pattern 5: Performance Testing

### Query Time Validation
```python
@pytest.mark.asyncio
async def test_search_performance_comprehensive(self):
    """Test performance characteristics."""
    test_cases = [
        ("simple", "Tesla", 1),
        ("multiple", "test", 10),
        ("max_limit", "a", 100),
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for test_name, query, limit in test_cases:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": query, "limit": limit}
            )

            assert response.status_code == 200
            data = response.json()

            # Query time should be positive and reasonable
            assert data["query_time_ms"] > 0
            assert data["query_time_ms"] < 30000  # 30 second threshold

            # Log for performance tracking
            print(f"{test_name}: {data['query_time_ms']}ms for {len(data['results'])} results")
```

## Pattern 6: Model Testing

### Pydantic Model Validation
```python
@pytest.mark.asyncio
async def test_search_models_direct(self):
    """Test Pydantic models directly without HTTP."""
    from datetime import datetime
    from app.models.search import EntitySearchResult, EntitySearchResponse

    # Create test result
    result = EntitySearchResult(
        name="Tesla",
        type="ORGANIZATION",
        connection_count=45,
        last_seen=datetime(2024, 11, 2, 10, 30, 0),
        wikidata_id="Q478214"
    )

    assert result.name == "Tesla"
    assert result.type == "ORGANIZATION"
    assert result.connection_count == 45
    assert isinstance(result.last_seen, datetime)

    # Create response
    response = EntitySearchResponse(
        results=[result],
        total_results=1,
        query_time_ms=150,
        query="Tesla",
        entity_type_filter=None
    )

    # Verify response
    assert len(response.results) == 1
    assert response.total_results == 1
    assert response.query == "Tesla"

    # Test JSON serialization
    json_data = response.model_dump_json()
    assert "Tesla" in json_data
    assert "150" in json_data
```

### Optional Fields
```python
@pytest.mark.asyncio
async def test_search_optional_fields(self):
    """Test handling of optional fields."""
    from app.models.search import EntitySearchResult, EntitySearchResponse

    # Minimum required fields
    result_minimal = EntitySearchResult(
        name="Unknown",
        type="UNKNOWN",
        connection_count=0,
        # last_seen and wikidata_id are optional
    )

    assert result_minimal.last_seen is None
    assert result_minimal.wikidata_id is None

    # With optional fields
    result_full = EntitySearchResult(
        name="Known",
        type="PERSON",
        connection_count=10,
        last_seen=datetime.now(),
        wikidata_id="Q123"
    )

    assert result_full.last_seen is not None
    assert result_full.wikidata_id == "Q123"
```

## Pattern 7: Integration Scenarios

### Realistic Query Sequences
```python
@pytest.mark.asyncio
async def test_search_realistic_sequence(self):
    """Test realistic search workflow."""
    search_sequence = [
        ("Tesla", None, 10),         # Browse main entity
        ("Elon", "PERSON", 5),       # Filter to people
        ("SpaceX", None, 20),        # Different entity
        ("tech", "ORGANIZATION", 10), # Specific type search
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for query, entity_type, limit in search_sequence:
            params = {"query": query, "limit": limit}
            if entity_type:
                params["entity_type"] = entity_type

            response = await client.get(
                "/api/v1/graph/search",
                params=params
            )

            assert response.status_code == 200
            data = response.json()

            assert data["query"] == query
            assert data["entity_type_filter"] == entity_type
            assert len(data["results"]) <= limit
```

## Test Utility Functions

### Helper: Validate Search Response
```python
def validate_search_response(data: dict) -> bool:
    """Helper function to validate search response structure."""
    required_fields = ["results", "total_results", "query_time_ms", "query", "entity_type_filter"]

    # Check all required fields
    for field in required_fields:
        if field not in data:
            return False

    # Validate types
    if not isinstance(data["results"], list):
        return False
    if not isinstance(data["total_results"], int):
        return False
    if not isinstance(data["query_time_ms"], int):
        return False
    if not isinstance(data["query"], str):
        return False

    # Validate metrics
    if data["total_results"] != len(data["results"]):
        return False
    if data["query_time_ms"] <= 0:
        return False

    return True
```

### Helper: Validate Result
```python
def validate_search_result(result: dict) -> bool:
    """Helper function to validate individual result structure."""
    required_fields = ["name", "type", "connection_count"]
    optional_fields = ["last_seen", "wikidata_id"]

    # Check required fields
    for field in required_fields:
        if field not in result:
            return False

    # Validate types
    if not isinstance(result["name"], str) or not result["name"]:
        return False
    if not isinstance(result["type"], str):
        return False
    if not isinstance(result["connection_count"], int) or result["connection_count"] < 0:
        return False

    return True
```

## Running Test Examples

All patterns above are already implemented in `tests/test_search.py`. To run specific patterns:

```bash
# Run success tests (patterns 1, 2)
pytest tests/test_search.py::TestEntitySearchEndpointSuccess -v
pytest tests/test_search.py::TestEntitySearchResponseModel -v

# Run validation tests (pattern 1)
pytest tests/test_search.py::TestEntitySearchValidation -v

# Run edge case tests (pattern 3)
pytest tests/test_search.py::TestEntitySearchEdgeCases -v

# Run integration tests (pattern 7)
pytest tests/test_search.py::TestEntitySearchIntegration -v

# Run all model tests (pattern 6)
pytest tests/test_search.py::TestEntitySearchWithMocking -v

# Run performance tests (pattern 5)
pytest tests/test_search.py::TestEntitySearchPerformance -v
```

---

**For more information, see:**
- `tests/test_search.py` - Full test implementation
- `TEST_SEARCH_COMPREHENSIVE_GUIDE.md` - Detailed documentation
- `QUICK_TEST_REFERENCE.md` - Quick reference guide
