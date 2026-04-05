"""Tests for HTTP Cache API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.services.http_cache import CacheEntry, CacheStats


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_cache():
    with patch('app.api.cache.get_http_cache') as mock:
        cache = MagicMock()
        mock.return_value = cache
        yield cache


class TestCacheAPI:
    def test_get_stats(self, client, mock_cache):
        mock_cache.get_stats.return_value = CacheStats(
            total_entries=100,
            total_size_bytes=1024 * 1024,  # 1 MB
            total_hits=500,
            total_misses=100,
            hit_rate=0.833,
            oldest_entry_age_seconds=3600,
            avg_entry_age_seconds=1800
        )

        response = client.get("/api/v1/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_entries"] == 100
        assert data["total_hits"] == 500
        assert data["hit_rate"] == 0.833
        assert data["total_size_mb"] == 1.0

    def test_invalidate_url(self, client, mock_cache):
        mock_cache.invalidate.return_value = True

        response = client.post(
            "/api/v1/cache/invalidate",
            json={"url": "https://example.com/article"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["entries_removed"] == 1
        mock_cache.invalidate.assert_called_once_with("https://example.com/article")

    def test_invalidate_url_not_found(self, client, mock_cache):
        mock_cache.invalidate.return_value = False

        response = client.post(
            "/api/v1/cache/invalidate",
            json={"url": "https://example.com/nonexistent"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["entries_removed"] == 0

    def test_invalidate_domain(self, client, mock_cache):
        mock_cache.invalidate_domain.return_value = 5

        response = client.post(
            "/api/v1/cache/invalidate",
            json={"domain": "example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["entries_removed"] == 5
        mock_cache.invalidate_domain.assert_called_once_with("example.com")

    def test_invalidate_no_params(self, client, mock_cache):
        response = client.post(
            "/api/v1/cache/invalidate",
            json={}
        )

        assert response.status_code == 400

    def test_cleanup_expired(self, client, mock_cache):
        mock_cache.cleanup_expired.return_value = 10

        response = client.post("/api/v1/cache/cleanup")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["entries_removed"] == 10

    def test_clear_cache(self, client, mock_cache):
        mock_cache.clear.return_value = 50

        response = client.post("/api/v1/cache/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["entries_cleared"] == 50

    def test_set_domain_ttl(self, client, mock_cache):
        response = client.post(
            "/api/v1/cache/domain-ttl",
            json={"domain": "news.com", "ttl_seconds": 1800}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["domain"] == "news.com"
        assert data["ttl_seconds"] == 1800
        mock_cache.set_domain_ttl.assert_called_once_with("news.com", 1800)

    def test_set_domain_ttl_negative(self, client, mock_cache):
        response = client.post(
            "/api/v1/cache/domain-ttl",
            json={"domain": "news.com", "ttl_seconds": -1}
        )

        assert response.status_code == 400

    def test_get_cache_entry(self, client, mock_cache):
        mock_cache.get.return_value = CacheEntry(
            url="https://example.com/article",
            content="Article content here",
            word_count=100,
            method="newspaper4k",
            status="success",
            metadata={"title": "Test Article"},
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            expires_at=datetime(2024, 1, 1, 13, 0, 0),
            hit_count=5
        )

        response = client.get("/api/v1/cache/entry/https://example.com/article")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/article"
        assert data["word_count"] == 100
        assert data["method"] == "newspaper4k"
        assert data["hit_count"] == 5

    def test_get_cache_entry_not_found(self, client, mock_cache):
        mock_cache.get.return_value = None

        response = client.get("/api/v1/cache/entry/https://example.com/nonexistent")

        assert response.status_code == 404
