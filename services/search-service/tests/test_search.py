"""
Tests for search functionality.

Uses SQLite for testing (via conftest.py) to avoid PostgreSQL dependency.
Note: Tests requiring PostgreSQL full-text search are skipped on SQLite.
"""
import pytest
from tests.conftest import IS_SQLITE


class TestSearch:
    """Test search endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "search-service"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "documentation" in data

    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL full-text search (ts_rank, to_tsquery)")
    def test_basic_search(self, client, sample_articles):
        """Test basic search"""
        response = client.get("/api/v1/search?query=python&page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert data["query"] == "python"
        assert "total" in data
        assert "results" in data
        assert isinstance(data["results"], list)

        # Should find the Python article
        if data["total"] > 0:
            assert any("python" in r["title"].lower() for r in data["results"])

    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL full-text search (ts_rank, to_tsquery)")
    def test_search_with_filters(self, client, sample_articles):
        """Test search with filters"""
        response = client.get(
            "/api/v1/search?query=programming&source=TechBlog&sentiment=positive"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "programming"
        if data["total"] > 0:
            for result in data["results"]:
                assert result["source"] == "TechBlog"
                assert result["sentiment"] == "positive"

    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL full-text search (ts_rank, to_tsquery)")
    def test_search_pagination(self, client, sample_articles):
        """Test search pagination"""
        # Page 1
        response = client.get("/api/v1/search?query=programming&page=1&page_size=1")
        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 1
        assert len(data["results"]) <= 1

    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL similarity() function from pg_trgm extension")
    @pytest.mark.asyncio
    async def test_suggestions(self, client, db_session, sample_articles):
        """Test autocomplete suggestions"""
        from app.models.search import SearchAnalytics

        # First, create some search analytics
        analytics = SearchAnalytics(query="python tutorial", hits=10)
        db_session.add(analytics)
        await db_session.commit()

        response = client.get("/api/v1/search/suggest?query=pyth&limit=5")
        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    @pytest.mark.asyncio
    async def test_popular_queries(self, client, db_session):
        """Test popular queries endpoint"""
        from app.models.search import SearchAnalytics

        # Create some analytics data
        queries = [
            SearchAnalytics(query="python", hits=100),
            SearchAnalytics(query="javascript", hits=80),
            SearchAnalytics(query="database", hits=60),
        ]
        for q in queries:
            db_session.add(q)
        await db_session.commit()

        response = client.get("/api/v1/search/popular?limit=10")
        assert response.status_code == 200
        data = response.json()

        assert "popular_queries" in data
        assert isinstance(data["popular_queries"], list)

    def test_search_validation(self, client):
        """Test search validation"""
        # Empty query
        response = client.get("/api/v1/search?query=")
        assert response.status_code == 422  # Validation error

        # Invalid page
        response = client.get("/api/v1/search?query=test&page=0")
        assert response.status_code == 422

    @pytest.mark.skipif(IS_SQLITE, reason="Requires PostgreSQL full-text search (ts_rank, to_tsquery, similarity)")
    def test_advanced_search(self, client, sample_articles):
        """Test advanced search endpoint"""
        request_data = {
            "query": "programming",
            "page": 1,
            "page_size": 10,
            "use_fuzzy": True,
            "highlight": True,
            "facets": ["source", "sentiment"]
        }

        response = client.post("/api/v1/search/advanced", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert "results" in data
        assert "facets" in data


class TestSavedSearches:
    """Test saved searches endpoints"""

    def test_create_saved_search_unauthorized(self, client):
        """Test creating saved search without auth"""
        data = {
            "name": "My Search",
            "query": "python tutorial",
            "notifications_enabled": False
        }

        response = client.post("/api/v1/search/saved", json=data)
        assert response.status_code == 403  # Requires authentication


class TestSearchHistory:
    """Test search history endpoints"""

    def test_get_search_history_unauthorized(self, client):
        """Test getting search history without auth"""
        response = client.get("/api/v1/search/history")
        assert response.status_code == 403  # Requires authentication


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
