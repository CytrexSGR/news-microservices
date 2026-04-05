"""
Tests for feed API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Feed, FeedItem, FeedHealth


class TestFeedEndpoints:
    """Test feed CRUD operations."""

    def test_create_feed(self, client: TestClient, sample_feed_data):
        """Test creating a new feed."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_feed_data["name"]
        assert data["url"] == sample_feed_data["url"]
        assert data["description"] == sample_feed_data["description"]
        assert data["fetch_interval"] == sample_feed_data["fetch_interval"]
        assert data["is_active"] is True
        assert data["status"] == "ACTIVE"
        assert data["categories"] == sample_feed_data["categories"]
        assert "id" in data
        assert "created_at" in data

    def test_create_duplicate_feed(self, client: TestClient, sample_feed_data):
        """Test that duplicate feed URLs are rejected."""
        # Create first feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201

        # Try to create duplicate
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_list_feeds(self, client: TestClient, sample_feed_data):
        """Test listing feeds with pagination."""
        # Create multiple feeds
        for i in range(5):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            data["name"] = f"Test Feed {i}"
            response = client.post("/api/v1/feeds", json=data)
            assert response.status_code == 201

        # Test listing all feeds
        response = client.get("/api/v1/feeds")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test pagination
        response = client.get("/api/v1/feeds?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_feeds_with_filters(self, client: TestClient, sample_feed_data):
        """Test listing feeds with various filters."""
        # Create feeds with different statuses
        active_feed = sample_feed_data.copy()
        active_feed["url"] = "https://example.com/active.xml"
        response = client.post("/api/v1/feeds", json=active_feed)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Update feed to inactive
        client.put(f"/api/v1/feeds/{feed_id}", json={"is_active": False})

        # Test filtering by active status
        response = client.get("/api/v1/feeds?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is False

        # Test filtering by category
        response = client.get("/api/v1/feeds?category=technology")
        assert response.status_code == 200
        data = response.json()
        assert all("technology" in feed["categories"] for feed in data)

    def test_get_single_feed(self, client: TestClient, sample_feed_data):
        """Test getting a single feed by ID."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Get feed by ID
        response = client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feed_id
        assert data["name"] == sample_feed_data["name"]

    def test_get_nonexistent_feed(self, client: TestClient):
        """Test getting a feed that doesn't exist."""
        response = client.get("/api/v1/feeds/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_feed(self, client: TestClient, sample_feed_data, sample_feed_update):
        """Test updating a feed."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Update feed
        response = client.put(f"/api/v1/feeds/{feed_id}", json=sample_feed_update)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_feed_update["name"]
        assert data["description"] == sample_feed_update["description"]
        assert data["fetch_interval"] == sample_feed_update["fetch_interval"]
        assert data["is_active"] == sample_feed_update["is_active"]
        # URL should not change
        assert data["url"] == sample_feed_data["url"]

    def test_delete_feed(self, client: TestClient, sample_feed_data):
        """Test deleting a feed."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Delete feed
        response = client.delete(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 204

        # Verify feed is deleted
        response = client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 404

    def test_trigger_feed_fetch(self, client: TestClient, sample_feed_data):
        """Test manually triggering a feed fetch."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Trigger fetch
        response = client.post(f"/api/v1/feeds/{feed_id}/fetch")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["feed_id"] == feed_id

    def test_get_feed_items(self, client: TestClient, sample_feed_data):
        """Test getting feed items."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Get items (should be empty initially)
        response = client.get(f"/api/v1/feeds/{feed_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

        # TODO: Add items and test retrieval with pagination

    def test_get_feed_health(self, client: TestClient, sample_feed_data):
        """Test getting feed health metrics."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Get health metrics
        response = client.get(f"/api/v1/feeds/{feed_id}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["feed_id"] == feed_id
        assert data["health_score"] == 100  # Initial score
        assert data["is_healthy"] is True
        assert data["consecutive_failures"] == 0

    def test_get_feed_quality(self, client: TestClient, sample_feed_data):
        """Test getting feed quality score."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Get quality score
        response = client.get(f"/api/v1/feeds/{feed_id}/quality")
        assert response.status_code == 200
        data = response.json()
        assert data["feed_id"] == feed_id
        assert "quality_score" in data
        assert "freshness_score" in data
        assert "consistency_score" in data
        assert "content_score" in data
        assert "reliability_score" in data
        assert "recommendations" in data

    def test_bulk_fetch_feeds(self, client: TestClient, sample_feed_data):
        """Test bulk fetch endpoint."""
        # Create multiple feeds
        feed_ids = []
        for i in range(3):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            data["name"] = f"Test Feed {i}"
            response = client.post("/api/v1/feeds", json=data)
            assert response.status_code == 201
            feed_ids.append(response.json()["id"])

        # Test bulk fetch specific feeds
        response = client.post(
            "/api/v1/feeds/bulk-fetch",
            json={"feed_ids": feed_ids[:2], "force": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_feeds"] == 2
        assert len(data["details"]) == 2

        # Test bulk fetch all feeds
        response = client.post(
            "/api/v1/feeds/bulk-fetch",
            json={"feed_ids": None, "force": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_feeds"] == 3


class TestScrapingEndpoints:
    """Test scraping-related endpoints."""

    def test_get_scraping_threshold(self, client: TestClient, sample_feed_data):
        """Test getting feed-specific scraping failure threshold."""
        # Create feed with custom threshold
        feed_data = sample_feed_data.copy()
        feed_data["scrape_failure_threshold"] = 7
        response = client.post("/api/v1/feeds", json=feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Get threshold
        response = client.get(f"/api/v1/feeds/{feed_id}/threshold")
        assert response.status_code == 200
        data = response.json()
        assert data["scrape_failure_threshold"] == 7
        assert data["feed_id"] == feed_id

    def test_get_threshold_nonexistent_feed(self, client: TestClient):
        """Test getting threshold for non-existent feed."""
        response = client.get("/api/v1/feeds/00000000-0000-0000-0000-000000000000/threshold")
        assert response.status_code == 404

    def test_reset_scraping_failures(self, client: TestClient, sample_feed_data):
        """Test resetting scraping failures and re-enabling scraping."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Simulate failures
        update_data = {
            "scrape_failure_count": 5,
            "scrape_last_failure_at": "2024-01-15T12:00:00Z",
            "scrape_disabled_reason": "auto_threshold",
            "scrape_full_content": False,
        }
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update_data)
        assert response.status_code == 200

        # Verify feed is disabled
        response = client.get(f"/api/v1/feeds/{feed_id}")
        data = response.json()
        assert data["scrape_failure_count"] == 5
        assert data["scrape_full_content"] is False
        assert data["scrape_disabled_reason"] == "auto_threshold"

        # Reset failures
        response = client.post(f"/api/v1/feeds/{feed_id}/scraping/reset")
        assert response.status_code == 200
        reset_data = response.json()
        assert "successfully" in reset_data["message"].lower()

        # Verify reset
        response = client.get(f"/api/v1/feeds/{feed_id}")
        data = response.json()
        assert data["scrape_failure_count"] == 0
        assert data["scrape_last_failure_at"] is None
        assert data["scrape_disabled_reason"] is None
        assert data["scrape_full_content"] is True  # Re-enabled

    def test_reset_nonexistent_feed(self, client: TestClient):
        """Test resetting scraping for non-existent feed."""
        response = client.post("/api/v1/feeds/00000000-0000-0000-0000-000000000000/scraping/reset")
        assert response.status_code == 404

    def test_scrape_method_validation(self, client: TestClient, sample_feed_data):
        """Test that only newspaper4k and playwright are accepted."""
        # Valid methods
        for method in ["newspaper4k", "playwright"]:
            feed_data = sample_feed_data.copy()
            feed_data["url"] = f"https://example.com/{method}.xml"
            feed_data["scrape_method"] = method
            response = client.post("/api/v1/feeds", json=feed_data)
            assert response.status_code == 201
            assert response.json()["scrape_method"] == method

        # Invalid method (old value)
        feed_data = sample_feed_data.copy()
        feed_data["url"] = "https://example.com/invalid.xml"
        feed_data["scrape_method"] = "auto"
        response = client.post("/api/v1/feeds", json=feed_data)
        assert response.status_code == 422  # Validation error

    def test_scrape_failure_threshold_validation(self, client: TestClient, sample_feed_data):
        """Test threshold validation (1-20 range)."""
        # Valid thresholds
        for threshold in [1, 5, 10, 20]:
            feed_data = sample_feed_data.copy()
            feed_data["url"] = f"https://example.com/threshold{threshold}.xml"
            feed_data["scrape_failure_threshold"] = threshold
            response = client.post("/api/v1/feeds", json=feed_data)
            assert response.status_code == 201
            assert response.json()["scrape_failure_threshold"] == threshold

        # Invalid thresholds
        for threshold in [0, -1, 21, 100]:
            feed_data = sample_feed_data.copy()
            feed_data["url"] = f"https://example.com/invalid{threshold}.xml"
            feed_data["scrape_failure_threshold"] = threshold
            response = client.post("/api/v1/feeds", json=feed_data)
            assert response.status_code == 422  # Validation error

    def test_update_scraping_configuration(self, client: TestClient, sample_feed_data):
        """Test updating scraping configuration (method + threshold)."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Update to playwright with higher threshold
        update_data = {
            "scrape_method": "playwright",
            "scrape_failure_threshold": 15,
        }
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update_data)
        assert response.status_code == 200

        # Verify update
        response = client.get(f"/api/v1/feeds/{feed_id}")
        data = response.json()
        assert data["scrape_method"] == "playwright"
        assert data["scrape_failure_threshold"] == 15