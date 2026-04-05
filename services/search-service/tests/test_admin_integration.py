"""
Integration tests for Admin API endpoints.

These tests require PostgreSQL container and should be run with:
    pytest tests/test_admin_integration.py --postgresql
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.search import ArticleIndex, SearchHistory, SearchAnalytics


# Mock dependencies
def mock_get_current_user():
    """Mock authenticated user."""
    return {
        "user_id": "test-admin-123",
        "email": "admin@test.com",
        "role": "admin"
    }


app.dependency_overrides[get_current_user] = mock_get_current_user


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def setup_test_data(postgres_session: AsyncSession, postgres_engine):
    """
    Create test data for admin endpoints.

    Sets up articles, search history, and analytics for testing.
    """
    # Import the session maker from conftest
    from tests.conftest import _PostgresAsyncTestingSessionLocal

    # Verify that the session maker is initialized
    if _PostgresAsyncTestingSessionLocal is None:
        raise RuntimeError(
            "PostgreSQL session maker not initialized. "
            "Make sure postgres_engine fixture runs first."
        )

    # Override get_db to create new sessions from the PostgreSQL engine
    async def override_get_db_postgres():
        async with _PostgresAsyncTestingSessionLocal() as db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db_postgres

    # Create sample articles
    articles = [
        ArticleIndex(
            article_id="art1",
            title="Python Testing Best Practices",
            content="Learn how to write effective tests in Python using pytest and testcontainers.",
            author="Test Author",
            source="TechBlog",
            url="https://example.com/python-testing",
            sentiment="positive",
        ),
        ArticleIndex(
            article_id="art2",
            title="Docker Container Optimization",
            content="Optimize your Docker containers for production deployments.",
            author="DevOps Expert",
            source="DevOps Weekly",
            url="https://example.com/docker-optimization",
            sentiment="neutral",
        ),
        ArticleIndex(
            article_id="art3",
            title="PostgreSQL Performance Tuning",
            content="Advanced PostgreSQL performance optimization techniques and best practices.",
            author="DBA Master",
            source="DataScience",
            url="https://example.com/postgres-tuning",
            sentiment="positive",
        ),
    ]

    for article in articles:
        postgres_session.add(article)
    await postgres_session.commit()

    # Create search history
    search_history = [
        SearchHistory(
            query="python testing",
            results_count=10,
            user_id="user1",
        ),
        SearchHistory(
            query="docker optimization",
            results_count=5,
            user_id="user2",
        ),
        SearchHistory(
            query="postgresql tuning",
            results_count=8,
            user_id="user1",
        ),
    ]

    for history in search_history:
        postgres_session.add(history)
    await postgres_session.commit()

    # Create search analytics
    analytics = [
        SearchAnalytics(query="python testing", hits=100),
        SearchAnalytics(query="docker optimization", hits=80),
        SearchAnalytics(query="postgresql tuning", hits=60),
    ]

    for analytic in analytics:
        postgres_session.add(analytic)
    await postgres_session.commit()

    yield

    # Cleanup is handled by conftest_postgres.py


@pytest.mark.postgresql
class TestAdminIndexStatistics:
    """Test /admin/stats/index endpoint"""

    def test_get_index_statistics(self, client, setup_test_data):
        """Test getting index statistics"""
        response = client.get("/api/v1/admin/stats/index")
        assert response.status_code == 200

        data = response.json()

        # Check structure
        assert "total_indexed" in data
        assert "by_source" in data
        assert "by_sentiment" in data
        assert "recent_24h" in data
        assert "index_size" in data
        assert "last_updated" in data

        # Verify data
        assert data["total_indexed"] == 3
        assert isinstance(data["by_source"], list)
        assert isinstance(data["by_sentiment"], list)

        # Check sources
        sources = [item["source"] for item in data["by_source"]]
        assert "TechBlog" in sources
        assert "DevOps Weekly" in sources
        assert "DataScience" in sources

        # Check sentiments
        sentiments = {item["sentiment"]: item["count"] for item in data["by_sentiment"]}
        assert sentiments["positive"] == 2
        assert sentiments["neutral"] == 1


@pytest.mark.postgresql
class TestAdminQueryStatistics:
    """Test /admin/stats/queries endpoint"""

    def test_get_query_statistics(self, client, setup_test_data):
        """Test getting query statistics"""
        response = client.get("/api/v1/admin/stats/queries")
        assert response.status_code == 200

        data = response.json()

        # Check structure
        assert "top_queries" in data
        assert "total_searches" in data
        assert "recent_24h" in data
        assert "avg_results_per_query" in data
        assert "last_updated" in data

        # Verify data
        assert data["total_searches"] == 3
        assert data["recent_24h"] == 3  # All in last 24h
        assert isinstance(data["avg_results_per_query"], (int, float))

        # Check top queries
        assert isinstance(data["top_queries"], list)
        if len(data["top_queries"]) > 0:
            top_query = data["top_queries"][0]
            assert "query" in top_query
            assert "hits" in top_query
            assert top_query["query"] == "python testing"  # Most hits
            assert top_query["hits"] == 100

    def test_get_query_statistics_with_limit(self, client, setup_test_data):
        """Test query statistics with custom limit"""
        response = client.get("/api/v1/admin/stats/queries?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["top_queries"]) <= 2


@pytest.mark.postgresql
class TestAdminPerformanceStatistics:
    """Test /admin/stats/performance endpoint"""

    def test_get_performance_statistics(self, client, setup_test_data):
        """Test getting performance statistics"""
        response = client.get("/api/v1/admin/stats/performance")
        assert response.status_code == 200

        data = response.json()

        # Check structure
        assert "avg_execution_time_ms" in data
        assert "slowest_queries" in data
        assert "result_distribution" in data
        assert "last_updated" in data

        # Verify data types
        assert isinstance(data["avg_execution_time_ms"], (int, float))
        assert isinstance(data["slowest_queries"], list)
        assert isinstance(data["result_distribution"], list)

        # Check result distribution
        if len(data["result_distribution"]) > 0:
            dist = data["result_distribution"][0]
            assert "range" in dist
            assert "count" in dist


@pytest.mark.postgresql
class TestAdminCacheStatistics:
    """Test /admin/stats/cache endpoint (mocked Redis)"""

    def test_get_cache_statistics(self, client):
        """Test getting cache statistics"""
        # Note: Redis is mocked in conftest.py, so this tests the endpoint structure
        response = client.get("/api/v1/admin/stats/cache")
        assert response.status_code == 200

        data = response.json()

        # Check structure
        assert "total_keys" in data
        assert "memory_used" in data
        assert "hit_rate_percent" in data
        assert "total_hits" in data
        assert "total_misses" in data
        assert "evicted_keys" in data
        assert "expired_keys" in data
        assert "last_updated" in data


@pytest.mark.postgresql
class TestAdminCeleryStatistics:
    """Test /admin/stats/celery endpoint"""

    def test_get_celery_statistics(self, client):
        """Test getting Celery statistics"""
        response = client.get("/api/v1/admin/stats/celery")
        assert response.status_code == 200

        data = response.json()

        # Check structure
        assert "active_workers" in data
        assert "registered_tasks" in data
        assert "reserved_tasks" in data
        assert "worker_stats" in data
        assert "status" in data
        assert "last_updated" in data

        # Verify data types
        assert isinstance(data["active_workers"], int)
        assert isinstance(data["registered_tasks"], int)
        assert isinstance(data["worker_stats"], list)
        assert data["status"] in ["healthy", "no_workers"]


@pytest.mark.postgresql
class TestAdminEndToEnd:
    """End-to-end tests for admin dashboard"""

    def test_admin_dashboard_workflow(self, client, setup_test_data):
        """Test complete admin dashboard workflow"""
        # 1. Check index statistics
        index_resp = client.get("/api/v1/admin/stats/index")
        assert index_resp.status_code == 200
        assert index_resp.json()["total_indexed"] == 3

        # 2. Check query statistics
        query_resp = client.get("/api/v1/admin/stats/queries")
        assert query_resp.status_code == 200
        assert query_resp.json()["total_searches"] == 3

        # 3. Check performance statistics
        perf_resp = client.get("/api/v1/admin/stats/performance")
        assert perf_resp.status_code == 200

        # 4. Check cache statistics
        cache_resp = client.get("/api/v1/admin/stats/cache")
        assert cache_resp.status_code == 200

        # 5. Check Celery statistics
        celery_resp = client.get("/api/v1/admin/stats/celery")
        assert celery_resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--postgresql"])
