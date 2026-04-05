"""Tests for API endpoints."""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_main(self, client: AsyncClient):
        """Test main health endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "entity-canonicalization-service"

    @pytest.mark.asyncio
    async def test_health_check_router(self, client: AsyncClient):
        """Test router health endpoint."""
        response = await client.get("/api/v1/canonicalization/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "entity-canonicalization-service"


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns service info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "entity-canonicalization-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"


class TestCanonicalizeEndpoint:
    """Tests for single entity canonicalization endpoint."""

    @pytest.mark.asyncio
    async def test_canonicalize_new_entity(self, client: AsyncClient):
        """Test canonicalizing a new entity."""
        request_data = {
            "entity_name": "Test Entity",
            "entity_type": "TEST",
            "language": "en"
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Test Entity"
        assert data["entity_type"] == "TEST"
        assert data["source"] in ["exact", "fuzzy", "semantic", "wikidata", "new"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_canonicalize_exact_match(self, client: AsyncClient, sample_entity_alias):
        """Test canonicalizing entity with exact match."""
        request_data = {
            "entity_name": "USA",
            "entity_type": "LOCATION",
            "language": "en"
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "United States"
        assert data["source"] == "exact"
        assert data["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_canonicalize_invalid_request_missing_fields(self, client: AsyncClient):
        """Test canonicalize with missing required fields."""
        request_data = {
            "entity_type": "TEST"
            # Missing entity_name
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            json=request_data
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_canonicalize_empty_entity_name(self, client: AsyncClient):
        """Test canonicalize with empty entity name."""
        request_data = {
            "entity_name": "",
            "entity_type": "TEST",
            "language": "en"
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            json=request_data
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_canonicalize_response_structure(self, client: AsyncClient):
        """Test canonicalize response has correct structure."""
        request_data = {
            "entity_name": "Test Entity",
            "entity_type": "TEST",
            "language": "en"
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        required_fields = [
            "canonical_name",
            "aliases",
            "confidence",
            "source",
            "entity_type"
        ]
        for field in required_fields:
            assert field in data

        # Check types
        assert isinstance(data["canonical_name"], str)
        assert isinstance(data["aliases"], list)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["source"], str)
        assert isinstance(data["entity_type"], str)


class TestBatchCanonicalizeEndpoint:
    """Tests for batch canonicalization endpoint."""

    @pytest.mark.asyncio
    async def test_batch_canonicalize_success(self, client: AsyncClient):
        """Test batch canonicalization with multiple entities."""
        request_data = {
            "entities": [
                {"entity_name": "Entity 1", "entity_type": "TEST", "language": "en"},
                {"entity_name": "Entity 2", "entity_type": "TEST", "language": "en"},
                {"entity_name": "Entity 3", "entity_type": "TEST", "language": "en"}
            ]
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize/batch",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 3
        assert len(data["results"]) == 3
        assert "total_time_ms" in data
        assert data["total_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_batch_canonicalize_empty_list(self, client: AsyncClient):
        """Test batch canonicalization with empty list."""
        request_data = {
            "entities": []
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize/batch",
            json=request_data
        )

        assert response.status_code == 422  # Validation error (min_length=1)

    @pytest.mark.asyncio
    async def test_batch_canonicalize_max_limit(self, client: AsyncClient):
        """Test batch canonicalization respects max limit (100)."""
        # Create 101 entities (exceeds limit)
        entities = [
            {"entity_name": f"Entity {i}", "entity_type": "TEST", "language": "en"}
            for i in range(101)
        ]
        request_data = {"entities": entities}

        response = await client.post(
            "/api/v1/canonicalization/canonicalize/batch",
            json=request_data
        )

        assert response.status_code == 422  # Validation error (max_length=100)

    @pytest.mark.asyncio
    async def test_batch_canonicalize_mixed_types(self, client: AsyncClient):
        """Test batch canonicalization with different entity types."""
        request_data = {
            "entities": [
                {"entity_name": "Person", "entity_type": "PERSON", "language": "en"},
                {"entity_name": "Organization", "entity_type": "ORGANIZATION", "language": "en"},
                {"entity_name": "Location", "entity_type": "LOCATION", "language": "en"}
            ]
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize/batch",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

        # Check entity types are preserved
        entity_types = [r["entity_type"] for r in data["results"]]
        assert "PERSON" in entity_types
        assert "ORGANIZATION" in entity_types
        assert "LOCATION" in entity_types


class TestGetAliasesEndpoint:
    """Tests for get aliases endpoint."""

    @pytest.mark.asyncio
    async def test_get_aliases_existing_entity(self, client: AsyncClient, sample_canonical_entity, sample_entity_alias):
        """Test getting aliases for existing entity."""
        response = await client.get(
            "/api/v1/canonicalization/aliases/United States?entity_type=LOCATION"
        )

        assert response.status_code == 200
        aliases = response.json()
        assert isinstance(aliases, list)
        assert "USA" in aliases

    @pytest.mark.asyncio
    async def test_get_aliases_nonexistent_entity(self, client: AsyncClient):
        """Test getting aliases for non-existent entity."""
        response = await client.get(
            "/api/v1/canonicalization/aliases/NonExistent?entity_type=LOCATION"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_aliases_wrong_type(self, client: AsyncClient, sample_canonical_entity):
        """Test getting aliases with wrong entity type."""
        response = await client.get(
            "/api/v1/canonicalization/aliases/United States?entity_type=PERSON"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_aliases_missing_entity_type(self, client: AsyncClient):
        """Test getting aliases without entity_type parameter."""
        response = await client.get(
            "/api/v1/canonicalization/aliases/United States"
        )

        assert response.status_code == 422  # Missing query parameter


class TestStatsEndpoint:
    """Tests for statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats_basic(self, client: AsyncClient, sample_canonical_entity, sample_entity_alias):
        """Test getting basic statistics."""
        response = await client.get("/api/v1/canonicalization/stats")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "total_canonical_entities" in data
        assert "total_aliases" in data
        assert "wikidata_linked" in data
        assert "coverage_percentage" in data

        # Check values
        assert data["total_canonical_entities"] >= 1
        assert data["total_aliases"] >= 1

    @pytest.mark.asyncio
    async def test_get_detailed_stats(self, client: AsyncClient, sample_canonical_entity, sample_entity_alias):
        """Test getting detailed statistics."""
        response = await client.get("/api/v1/canonicalization/stats/detailed")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        required_fields = [
            "total_canonical_entities",
            "total_aliases",
            "wikidata_linked",
            "wikidata_coverage_percent",
            "deduplication_ratio",
            "source_breakdown",
            "entity_type_distribution",
            "top_entities_by_aliases",
            "entities_without_qid",
            "avg_cache_hit_time_ms",
            "total_api_calls_saved",
            "estimated_cost_savings_monthly"
        ]

        for field in required_fields:
            assert field in data

        # Check structure
        assert isinstance(data["source_breakdown"], dict)
        assert isinstance(data["entity_type_distribution"], dict)
        assert isinstance(data["top_entities_by_aliases"], list)

    @pytest.mark.asyncio
    async def test_get_stats_empty_database(self, client: AsyncClient):
        """Test statistics with empty database."""
        response = await client.get("/api/v1/canonicalization/stats")

        assert response.status_code == 200
        data = response.json()
        # Should return zeros, not error
        assert data["total_canonical_entities"] >= 0
        assert data["total_aliases"] >= 0


class TestAsyncBatchEndpoints:
    """Tests for async batch processing endpoints."""

    @pytest.mark.asyncio
    async def test_start_async_batch_job(self, client: AsyncClient):
        """Test starting async batch canonicalization job."""
        request_data = {
            "entities": [
                {"entity_name": "Entity 1", "entity_type": "TEST", "language": "en"},
                {"entity_name": "Entity 2", "entity_type": "TEST", "language": "en"}
            ]
        }

        response = await client.post(
            "/api/v1/canonicalization/canonicalize/batch/async",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert data["total_entities"] == 2

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, client: AsyncClient):
        """Test getting status of non-existent job."""
        response = await client.get(
            "/api/v1/canonicalization/jobs/nonexistent-job-id/status"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_result_not_found(self, client: AsyncClient):
        """Test getting result of non-existent job."""
        response = await client.get(
            "/api/v1/canonicalization/jobs/nonexistent-job-id/result"
        )

        assert response.status_code == 404


class TestReprocessingEndpoints:
    """Tests for batch reprocessing endpoints."""

    @pytest.mark.asyncio
    async def test_get_reprocessing_status_idle(self, client: AsyncClient):
        """Test getting reprocessing status when idle."""
        response = await client.get("/api/v1/canonicalization/reprocess/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"

    @pytest.mark.asyncio
    async def test_stop_reprocessing_when_not_running(self, client: AsyncClient):
        """Test stopping reprocessing when not running."""
        response = await client.post("/api/v1/canonicalization/reprocess/stop")

        assert response.status_code == 404


class TestTrendsEndpoint:
    """Tests for trends analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_entity_type_trends_default(self, client: AsyncClient):
        """Test getting entity type trends with default parameters."""
        response = await client.get("/api/v1/canonicalization/trends/entity-types")

        assert response.status_code == 200
        data = response.json()

        assert "trends" in data
        assert "days" in data
        assert "total_entities" in data
        assert isinstance(data["trends"], list)
        assert data["days"] == 30  # Default

    @pytest.mark.asyncio
    async def test_get_entity_type_trends_custom_days(self, client: AsyncClient):
        """Test getting entity type trends with custom days."""
        response = await client.get(
            "/api/v1/canonicalization/trends/entity-types?days=7"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 7

    @pytest.mark.asyncio
    async def test_get_entity_type_trends_max_days_limit(self, client: AsyncClient):
        """Test entity type trends respects max limit (365 days)."""
        response = await client.get(
            "/api/v1/canonicalization/trends/entity-types?days=500"
        )

        assert response.status_code == 200
        data = response.json()
        # Should be capped at 365
        assert data["days"] == 365

    @pytest.mark.asyncio
    async def test_get_entity_type_trends_min_days_limit(self, client: AsyncClient):
        """Test entity type trends respects min limit (1 day)."""
        response = await client.get(
            "/api/v1/canonicalization/trends/entity-types?days=0"
        )

        assert response.status_code == 200
        data = response.json()
        # Should be at least 1
        assert data["days"] == 1

    @pytest.mark.asyncio
    async def test_get_entity_type_trends_structure(self, client: AsyncClient):
        """Test entity type trends response structure."""
        response = await client.get(
            "/api/v1/canonicalization/trends/entity-types?days=7"
        )

        assert response.status_code == 200
        data = response.json()

        # Check trends structure
        if len(data["trends"]) > 0:
            trend = data["trends"][0]
            required_fields = [
                "date", "PERSON", "ORGANIZATION", "LOCATION",
                "EVENT", "PRODUCT", "OTHER", "MISC", "NOT_APPLICABLE"
            ]
            for field in required_fields:
                assert field in trend


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json(self, client: AsyncClient):
        """Test handling of invalid JSON."""
        response = await client.post(
            "/api/v1/canonicalization/canonicalize",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test handling of wrong HTTP method."""
        response = await client.get("/api/v1/canonicalization/canonicalize")

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_not_found_endpoint(self, client: AsyncClient):
        """Test handling of non-existent endpoint."""
        response = await client.get("/api/v1/canonicalization/nonexistent")

        assert response.status_code == 404
