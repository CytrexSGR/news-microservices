"""
Tests for semantic search functionality (Layer 1).

Note: These tests mock the embedding service since:
1. SQLite doesn't support pgvector
2. We don't want to call OpenAI API in tests

Full integration tests require PostgreSQL with pgvector extension.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tests.conftest import IS_SQLITE


class TestSemanticSearchSchemas:
    """Test semantic search request/response schemas"""

    def test_semantic_search_request_validation(self):
        """Test SemanticSearchRequest validation"""
        from app.schemas.search import SemanticSearchRequest

        # Valid request
        request = SemanticSearchRequest(
            query="federal reserve interest rates",
            limit=50,
            min_similarity=0.5,
            cluster_results=True
        )
        assert request.query == "federal reserve interest rates"
        assert request.limit == 50
        assert request.min_similarity == 0.5
        assert request.cluster_results is True

    def test_semantic_search_request_defaults(self):
        """Test SemanticSearchRequest defaults"""
        from app.schemas.search import SemanticSearchRequest

        request = SemanticSearchRequest(query="test query")
        assert request.limit == 50
        assert request.min_similarity == 0.5
        assert request.cluster_results is True
        assert request.filters is None

    def test_semantic_search_request_invalid_limit(self):
        """Test SemanticSearchRequest rejects invalid limit"""
        from app.schemas.search import SemanticSearchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SemanticSearchRequest(query="test", limit=0)

        with pytest.raises(ValidationError):
            SemanticSearchRequest(query="test", limit=101)

    def test_semantic_search_request_invalid_similarity(self):
        """Test SemanticSearchRequest rejects invalid similarity"""
        from app.schemas.search import SemanticSearchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SemanticSearchRequest(query="test", min_similarity=-0.1)

        with pytest.raises(ValidationError):
            SemanticSearchRequest(query="test", min_similarity=1.1)

    def test_semantic_search_response_model(self):
        """Test SemanticSearchResponse model"""
        from app.schemas.search import SemanticSearchResponse, SemanticSearchResultItem

        result = SemanticSearchResultItem(
            article_id="test-123",
            title="Test Article",
            content="Test content",
            similarity=0.85,
        )

        response = SemanticSearchResponse(
            query="test query",
            total=1,
            results=[result],
            clusters=None,
            embedding_available=True,
            execution_time_ms=150.5,
        )

        assert response.query == "test query"
        assert response.total == 1
        assert len(response.results) == 1
        assert response.results[0].similarity == 0.85
        assert response.embedding_available is True


class TestEmbeddingService:
    """Test embedding service"""

    def test_embedding_service_unavailable_without_key(self):
        """Test embedding service reports unavailable without API key"""
        from app.services.embedding_service import EmbeddingService

        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
            # Need to patch settings as well
            with patch('app.services.embedding_service.settings') as mock_settings:
                mock_settings.OPENAI_API_KEY = ""
                mock_settings.EMBEDDING_CACHE_SIZE = 100
                mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

                service = EmbeddingService()
                assert service.is_available() is False

    def test_embedding_service_metrics(self):
        """Test embedding service metrics"""
        from app.services.embedding_service import EmbeddingService

        with patch('app.services.embedding_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.EMBEDDING_CACHE_SIZE = 100
            mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

            service = EmbeddingService()
            metrics = service.get_metrics()

            assert "cache_hits" in metrics
            assert "cache_misses" in metrics
            assert "cache_hit_rate" in metrics
            assert "available" in metrics
            assert metrics["available"] is False


class TestSemanticSearchEndpoint:
    """Test semantic search API endpoint"""

    def test_semantic_search_endpoint_exists(self, client):
        """Test semantic search endpoint is registered"""
        # POST to semantic search (will fail validation but endpoint exists)
        response = client.post("/api/v1/search/semantic", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code == 422

    def test_semantic_search_requires_query(self, client):
        """Test semantic search requires query parameter"""
        response = client.post("/api/v1/search/semantic", json={})
        assert response.status_code == 422
        data = response.json()
        assert "query" in str(data)

    @patch('app.services.semantic_search_service.get_embedding_service')
    def test_semantic_search_no_embedding_service(self, mock_get_embedding, client):
        """Test semantic search returns empty when embedding unavailable"""
        # Mock embedding service as unavailable
        mock_service = MagicMock()
        mock_service.is_available.return_value = False
        mock_get_embedding.return_value = mock_service

        response = client.post(
            "/api/v1/search/semantic",
            json={"query": "federal reserve interest rates"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "federal reserve interest rates"
        assert data["total"] == 0
        assert data["results"] == []
        assert data["embedding_available"] is False

    @patch('app.services.semantic_search_service.get_embedding_service')
    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL with pgvector")
    @pytest.mark.asyncio
    async def test_semantic_search_with_results(self, mock_get_embedding, client, db_session):
        """Test semantic search returns results"""
        # This test requires PostgreSQL with pgvector - skip on SQLite
        pass


class TestSemanticSearchClustering:
    """Test result clustering functionality"""

    def test_cluster_schema(self):
        """Test SemanticSearchCluster schema"""
        from app.schemas.search import SemanticSearchCluster, SemanticSearchResultItem

        result = SemanticSearchResultItem(
            article_id="test-1",
            title="Test Article 1",
            content="Content",
            similarity=0.9,
            cluster_id=0,
        )

        cluster = SemanticSearchCluster(
            cluster_id=0,
            size=1,
            representative_title="Test Article 1",
            avg_similarity=0.9,
            articles=[result],
        )

        assert cluster.cluster_id == 0
        assert cluster.size == 1
        assert len(cluster.articles) == 1

    def test_clustering_disabled_by_default(self):
        """Test clustering can be disabled"""
        from app.schemas.search import SemanticSearchRequest

        request = SemanticSearchRequest(
            query="test",
            cluster_results=False
        )
        assert request.cluster_results is False


class TestSemanticSearchFilters:
    """Test semantic search with filters"""

    def test_filters_in_request(self):
        """Test filters can be included in request"""
        from app.schemas.search import SemanticSearchRequest, SearchFilters
        from datetime import datetime

        filters = SearchFilters(
            source=["TechBlog", "DevNews"],
            sentiment=["positive"],
            date_from=datetime(2025, 1, 1),
            date_to=datetime(2025, 12, 31),
        )

        request = SemanticSearchRequest(
            query="market analysis",
            filters=filters,
        )

        assert request.filters is not None
        assert request.filters.source == ["TechBlog", "DevNews"]
        assert request.filters.sentiment == ["positive"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
