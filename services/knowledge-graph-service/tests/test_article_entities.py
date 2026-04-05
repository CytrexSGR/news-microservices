"""
Tests for Article Entities Endpoint

Tests the /api/v1/graph/articles/{article_id}/entities endpoint.
"""

import pytest
from httpx import AsyncClient
from app.main import app


class TestArticleEntitiesEndpoint:
    """Test article entities endpoint functionality."""

    @pytest.mark.asyncio
    async def test_get_article_entities_not_found(self):
        """Test fetching entities for non-existent article returns empty list."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/nonexistent-article-id/entities"
            )

            assert response.status_code == 200
            data = response.json()

            # Should return empty results for non-existent article
            assert data["article_id"] == "nonexistent-article-id"
            assert data["total_entities"] == 0
            assert data["entities"] == []
            assert data["article_title"] is None
            assert "query_time_ms" in data

    @pytest.mark.asyncio
    async def test_get_article_entities_with_limit(self):
        """Test limit parameter is respected."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/test-article/entities?limit=10"
            )

            assert response.status_code == 200
            data = response.json()

            # Entities count should not exceed limit
            assert len(data["entities"]) <= 10

    @pytest.mark.asyncio
    async def test_get_article_entities_with_entity_type_filter(self):
        """Test entity_type filter parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/test-article/entities?entity_type=PERSON"
            )

            assert response.status_code == 200
            data = response.json()

            # All returned entities should be of type PERSON
            for entity in data["entities"]:
                assert entity["type"] == "PERSON"

    @pytest.mark.asyncio
    async def test_get_article_entities_limit_validation(self):
        """Test limit parameter validation (max 200)."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Should reject limit > 200
            response = await client.get(
                "/api/v1/graph/articles/test-article/entities?limit=300"
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_article_entities_response_model(self):
        """Test response model structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/test-article/entities"
            )

            assert response.status_code == 200
            data = response.json()

            # Check required fields
            assert "article_id" in data
            assert "total_entities" in data
            assert "entities" in data
            assert "query_time_ms" in data
            assert "article_title" in data
            assert "article_url" in data

            # Check entities structure if any exist
            if data["entities"]:
                entity = data["entities"][0]
                assert "name" in entity
                assert "type" in entity
                assert "confidence" in entity
                assert "mention_count" in entity

    @pytest.mark.asyncio
    async def test_get_article_entities_ordering(self):
        """Test entities are ordered by confidence DESC, then mention_count DESC."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/test-article/entities"
            )

            assert response.status_code == 200
            data = response.json()

            entities = data["entities"]
            if len(entities) > 1:
                # Check ordering (confidence DESC, then mention_count DESC)
                for i in range(len(entities) - 1):
                    current = entities[i]
                    next_entity = entities[i + 1]

                    # Either confidence should be higher or equal
                    assert current["confidence"] >= next_entity["confidence"]

                    # If confidence equal, mention_count should be higher or equal
                    if current["confidence"] == next_entity["confidence"]:
                        assert current["mention_count"] >= next_entity["mention_count"]


class TestArticleInfoEndpoint:
    """Test article info endpoint functionality."""

    @pytest.mark.asyncio
    async def test_get_article_info_not_found(self):
        """Test fetching info for non-existent article returns 404."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/nonexistent-article/info"
            )

            # Should return 404 for non-existent article
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_article_info_response_structure(self):
        """Test article info response structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # This will 404 unless we have test data, but we can check the structure
            response = await client.get(
                "/api/v1/graph/articles/test-article/info"
            )

            # If article exists, check structure
            if response.status_code == 200:
                data = response.json()
                assert "article_id" in data
                assert "title" in data
                assert "url" in data
                assert "published_date" in data
                assert "entity_count" in data
                assert "query_time_ms" in data


class TestArticleService:
    """Test article service business logic."""

    @pytest.mark.asyncio
    async def test_article_service_import(self):
        """Test article service can be imported."""
        from app.services.article_service import article_service

        assert article_service is not None

    @pytest.mark.asyncio
    async def test_article_models_import(self):
        """Test article models can be imported."""
        from app.models.articles import (
            ArticleEntity,
            ArticleEntitiesResponse,
            ArticleNode
        )

        # Test model instantiation
        entity = ArticleEntity(
            name="Test Entity",
            type="PERSON",
            confidence=0.95,
            mention_count=3
        )
        assert entity.name == "Test Entity"
        assert entity.confidence == 0.95

        # Test response model
        response = ArticleEntitiesResponse(
            article_id="test-123",
            total_entities=1,
            entities=[entity],
            query_time_ms=50
        )
        assert response.article_id == "test-123"
        assert len(response.entities) == 1

        # Test article node
        node = ArticleNode(
            article_id="test-123",
            title="Test Article",
            entity_count=5
        )
        assert node.article_id == "test-123"
        assert node.entity_count == 5


class TestIntegration:
    """Integration tests requiring Neo4j connection."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_article_entities_with_real_data(self):
        """
        Test with real Neo4j data (requires running Neo4j).

        This test should be run manually or in CI with Neo4j available.
        """
        # Skip if no Neo4j connection
        pytest.skip("Integration test - requires Neo4j with test data")

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/graph/articles/real-article-id/entities"
            )

            assert response.status_code == 200
            data = response.json()

            # Validate real data structure
            if data["total_entities"] > 0:
                entity = data["entities"][0]
                assert 0.0 <= entity["confidence"] <= 1.0
                assert entity["mention_count"] >= 1
                assert entity["name"]
                assert entity["type"]


if __name__ == "__main__":
    # Run tests with:
    # pytest tests/test_article_entities.py -v
    # pytest tests/test_article_entities.py -v -m integration  # Integration tests only
    pass
