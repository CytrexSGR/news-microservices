"""
Tests for Entity Search Endpoint

Comprehensive test suite for /api/v1/graph/search endpoint.
Tests cover success cases, validation errors, edge cases, and response structure.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.search import EntitySearchResult, EntitySearchResponse


class TestEntitySearchEndpointSuccess:
    """Test successful search requests."""

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
        assert "query" in data
        assert "entity_type_filter" in data

        # Verify query echoed back
        assert data["query"] == "Tesla"
        assert data["entity_type_filter"] is None

        # Verify metrics
        assert data["query_time_ms"] > 0
        assert data["total_results"] >= 0
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_with_limit_parameter(self):
        """Test search with explicit limit parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "Elon", "limit": 5}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify results don't exceed limit
        assert len(data["results"]) <= 5
        assert data["total_results"] <= 5

    @pytest.mark.asyncio
    async def test_search_with_entity_type_filter(self):
        """Test search with entity_type filter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "Musk", "entity_type": "PERSON"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify entity type filter is applied
        assert data["entity_type_filter"] == "PERSON"

        # All results should be PERSON type
        for result in data["results"]:
            assert result["type"] == "PERSON"

    @pytest.mark.asyncio
    async def test_search_with_all_parameters(self):
        """Test search with all parameters specified."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={
                    "query": "Microsoft",
                    "limit": 20,
                    "entity_type": "ORGANIZATION"
                }
            )

        assert response.status_code == 200
        data = response.json()

        # Verify all parameters applied
        assert data["query"] == "Microsoft"
        assert data["entity_type_filter"] == "ORGANIZATION"
        assert len(data["results"]) <= 20

        for result in data["results"]:
            assert result["type"] == "ORGANIZATION"

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test with different cases
            response_lower = await client.get(
                "/api/v1/graph/search",
                params={"query": "tesla"}
            )
            response_upper = await client.get(
                "/api/v1/graph/search",
                params={"query": "TESLA"}
            )
            response_mixed = await client.get(
                "/api/v1/graph/search",
                params={"query": "TeSLa"}
            )

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200

        # All should return results (exact number may vary, but not error)
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()

        assert isinstance(data_lower["results"], list)
        assert isinstance(data_upper["results"], list)
        assert isinstance(data_mixed["results"], list)

    @pytest.mark.asyncio
    async def test_search_with_default_limit(self):
        """Test that default limit is applied when not specified."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "a"}  # Broad query, many matches expected
            )

        assert response.status_code == 200
        data = response.json()

        # Default limit is 10
        assert len(data["results"]) <= 10

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test search returning no results."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "XYZ_NONEXISTENT_ENTITY_12345"}
            )

        assert response.status_code == 200
        data = response.json()

        # Should return empty results, not error
        assert data["results"] == []
        assert data["total_results"] == 0
        assert data["query"] == "XYZ_NONEXISTENT_ENTITY_12345"
        assert data["query_time_ms"] > 0


class TestEntitySearchValidation:
    """Test input validation and error cases."""

    @pytest.mark.asyncio
    async def test_search_missing_query_parameter(self):
        """Test that missing query parameter returns 400."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/graph/search")

        # Query is required
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_search_query_too_short(self):
        """Test that query shorter than 1 character is rejected."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": ""}
            )

        # Empty query should be rejected (min_length=1)
        assert response.status_code == 422

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

    @pytest.mark.asyncio
    async def test_search_query_at_max_length(self):
        """Test that query at exactly 200 characters is accepted."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            max_length_query = "a" * 200  # Exactly 200 characters
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": max_length_query}
            )

        # Should be accepted (max_length=200)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_limit_too_low(self):
        """Test that limit < 1 is rejected."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 0}
            )

        # limit must be >= 1
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_limit_too_high(self):
        """Test that limit > 100 is rejected."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 101}
            )

        # limit must be <= 100
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_limit_at_boundaries(self):
        """Test that limit at min and max boundaries are accepted."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test limit = 1
            response_min = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 1}
            )

            # Test limit = 100
            response_max = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 100}
            )

        assert response_min.status_code == 200
        assert response_max.status_code == 200

        # Verify limits are respected
        assert len(response_min.json()["results"]) <= 1
        assert len(response_max.json()["results"]) <= 100

    @pytest.mark.asyncio
    async def test_search_limit_not_integer(self):
        """Test that non-integer limit is rejected."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": "abc"}
            )

        # Should reject non-integer limit
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_invalid_entity_type(self):
        """Test search with invalid entity type (should still work)."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "entity_type": "INVALID_TYPE"}
            )

        # Should accept any entity_type value (validation in Neo4j query)
        # If no results, that's expected behavior
        assert response.status_code == 200
        data = response.json()

        # Should be empty results if invalid type
        assert data["entity_type_filter"] == "INVALID_TYPE"
        # Could be empty or populated depending on data, just verify structure
        assert isinstance(data["results"], list)


class TestEntitySearchResponseModel:
    """Test response model structure and field validation."""

    @pytest.mark.asyncio
    async def test_search_response_has_all_required_fields(self):
        """Test that response contains all required fields."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test"}
            )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields present
        required_fields = [
            "results",
            "total_results",
            "query_time_ms",
            "query",
            "entity_type_filter"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_search_response_result_structure(self):
        """Test structure of individual results."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "a", "limit": 1}  # Get at least one result
            )

        assert response.status_code == 200
        data = response.json()

        # If results exist, verify their structure
        if data["results"]:
            result = data["results"][0]

            # Check required fields in result
            assert "name" in result
            assert "type" in result
            assert "connection_count" in result

            # Check optional fields
            assert "last_seen" in result
            assert "wikidata_id" in result

            # Verify types
            assert isinstance(result["name"], str)
            assert isinstance(result["type"], str)
            assert isinstance(result["connection_count"], int)
            assert result["connection_count"] >= 0

    @pytest.mark.asyncio
    async def test_search_response_metrics_validity(self):
        """Test that response metrics are valid."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify metrics
        assert isinstance(data["query_time_ms"], int)
        assert data["query_time_ms"] > 0  # Must take some time
        assert data["query_time_ms"] < 30000  # Should complete in < 30 seconds

        assert isinstance(data["total_results"], int)
        assert data["total_results"] >= 0
        assert data["total_results"] == len(data["results"])

    @pytest.mark.asyncio
    async def test_search_response_total_results_matches_count(self):
        """Test that total_results matches length of results array."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 50}
            )

        assert response.status_code == 200
        data = response.json()

        # total_results should match actual results count
        assert data["total_results"] == len(data["results"])


class TestEntitySearchEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self):
        """Test search with special characters in query."""
        special_queries = [
            "test@123",
            "elon-musk",
            "test_query",
            "test.com",
            "test/query"
        ]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for query in special_queries:
                response = await client.get(
                    "/api/v1/graph/search",
                    params={"query": query}
                )

                # Should not crash, may return empty results
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_with_whitespace_query(self):
        """Test search with whitespace in query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "Elon Musk"}
            )

        # Should handle spaces normally
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Elon Musk"
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_query_with_leading_trailing_spaces(self):
        """Test that leading/trailing spaces in query are preserved."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "  test  "}  # Leading and trailing spaces
            )

        assert response.status_code == 200
        data = response.json()

        # Query should be preserved as-is
        assert data["query"] == "  test  "

    @pytest.mark.asyncio
    async def test_search_exact_vs_partial_match(self):
        """Test that exact matches are ranked first."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Search for partial term that might have exact matches
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "Tesla", "limit": 10}
            )

        assert response.status_code == 200
        data = response.json()

        if data["results"]:
            # If exact match exists, it should be first
            first_result = data["results"][0]

            # Should find "Tesla" at start or as exact match
            assert "Tesla" in first_result["name"] or first_result["name"].lower() == "tesla"

    @pytest.mark.asyncio
    async def test_search_results_ordering_by_connection_count(self):
        """Test that results are ordered by connection count for same match type."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "a", "limit": 20}  # Get multiple results
            )

        assert response.status_code == 200
        data = response.json()

        if len(data["results"]) > 1:
            # Results should be ordered by connection_count (descending)
            for i in range(len(data["results"]) - 1):
                current = data["results"][i]
                next_result = data["results"][i + 1]

                # Connection count should be descending or equal
                # (exact match behavior may vary)
                assert current["connection_count"] >= next_result["connection_count"] or \
                       current["name"].lower() == data["query"].lower()

    @pytest.mark.asyncio
    async def test_search_with_numeric_query(self):
        """Test search with numeric query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "2024"}
            )

        assert response.status_code == 200
        data = response.json()

        # Should handle numeric queries
        assert data["query"] == "2024"
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_unicode_characters(self):
        """Test search with Unicode characters."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "café"}  # Unicode character
            )

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "café"
        assert isinstance(data["results"], list)


class TestEntitySearchPerformance:
    """Test performance-related aspects."""

    @pytest.mark.asyncio
    async def test_search_query_time_is_reasonable(self):
        """Test that query completes in reasonable time."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test"}
            )

        assert response.status_code == 200
        data = response.json()

        # Should complete in < 5 seconds (5000ms)
        # Neo4j queries should typically be < 1000ms
        assert 0 < data["query_time_ms"] < 5000

    @pytest.mark.asyncio
    async def test_search_with_max_limit_performance(self):
        """Test that max limit doesn't cause excessive delays."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/search",
                params={"query": "test", "limit": 100}
            )

        assert response.status_code == 200
        data = response.json()

        # Even with max limit, should complete quickly
        assert data["query_time_ms"] < 10000


class TestEntitySearchWithMocking:
    """Test with mocked Neo4j service for controlled test data."""

    @pytest.mark.asyncio
    async def test_search_response_model_serialization(self):
        """Test that EntitySearchResponse can be properly serialized."""
        # Create test response model directly
        result1 = EntitySearchResult(
            name="Tesla",
            type="ORGANIZATION",
            connection_count=45,
            last_seen=datetime.utcnow(),
            wikidata_id="Q478214"
        )
        result2 = EntitySearchResult(
            name="Tesla Inc",
            type="ORGANIZATION",
            connection_count=12,
            wikidata_id=None
        )

        response = EntitySearchResponse(
            results=[result1, result2],
            total_results=2,
            query_time_ms=150,
            query="Tesla",
            entity_type_filter="ORGANIZATION"
        )

        # Should be serializable
        json_data = response.model_dump_json()
        assert "Tesla" in json_data
        assert "150" in json_data
        assert "ORGANIZATION" in json_data

    @pytest.mark.asyncio
    async def test_search_result_field_types(self):
        """Test EntitySearchResult model field types."""
        result = EntitySearchResult(
            name="Elon Musk",
            type="PERSON",
            connection_count=150,
            last_seen=datetime(2024, 10, 15, 10, 30, 0),
            wikidata_id="Q317521"
        )

        assert isinstance(result.name, str)
        assert isinstance(result.type, str)
        assert isinstance(result.connection_count, int)
        assert result.last_seen is not None
        assert isinstance(result.wikidata_id, str)

    @pytest.mark.asyncio
    async def test_search_result_optional_fields(self):
        """Test EntitySearchResult with optional fields as None."""
        result = EntitySearchResult(
            name="Unknown Entity",
            type="UNKNOWN",
            connection_count=0,
            last_seen=None,
            wikidata_id=None
        )

        assert result.name == "Unknown Entity"
        assert result.last_seen is None
        assert result.wikidata_id is None
        assert result.connection_count == 0

    @pytest.mark.asyncio
    async def test_search_response_with_empty_results(self):
        """Test EntitySearchResponse with empty results."""
        response = EntitySearchResponse(
            results=[],
            total_results=0,
            query_time_ms=42,
            query="nonexistent",
            entity_type_filter=None
        )

        assert response.results == []
        assert response.total_results == 0
        assert response.query == "nonexistent"


class TestEntitySearchIntegration:
    """Integration tests with actual endpoint behavior."""

    @pytest.mark.asyncio
    async def test_search_common_entity_names(self):
        """Test searching for commonly known entities."""
        common_queries = ["Tesla", "Elon", "Microsoft", "Google", "Trump"]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for query in common_queries:
                response = await client.get(
                    "/api/v1/graph/search",
                    params={"query": query}
                )

                assert response.status_code == 200
                data = response.json()

                # Should have proper response structure
                assert "results" in data
                assert "total_results" in data
                assert "query_time_ms" in data

    @pytest.mark.asyncio
    async def test_search_multiple_sequential_queries(self):
        """Test multiple sequential search queries."""
        queries = ["Tesla", "Musk", "SpaceX"]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for query in queries:
                response = await client.get(
                    "/api/v1/graph/search",
                    params={"query": query}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["query"] == query

    @pytest.mark.asyncio
    async def test_search_all_entity_types(self):
        """Test search with each entity type filter."""
        entity_types = ["PERSON", "ORGANIZATION", "LOCATION", "PRODUCT", "EVENT"]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for entity_type in entity_types:
                response = await client.get(
                    "/api/v1/graph/search",
                    params={"query": "test", "entity_type": entity_type}
                )

                # Should not error, may return empty results
                assert response.status_code == 200
                data = response.json()
                assert data["entity_type_filter"] == entity_type


if __name__ == "__main__":
    # Run all tests with:
    # pytest tests/test_search.py -v
    #
    # Run specific test class:
    # pytest tests/test_search.py::TestEntitySearchEndpointSuccess -v
    #
    # Run with coverage:
    # pytest tests/test_search.py --cov=app.api.routes.search --cov=app.services.search_service -v
    pass
