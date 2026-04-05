"""
Extended API endpoint tests for feed service

Tests edge cases, error handling, and validation for all endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Feed, FeedItem


class TestFeedCreationEndpoint:
    """Test POST /api/v1/feeds endpoint."""

    def test_create_feed_with_minimal_data(self, client: TestClient):
        """Test creating feed with only required fields."""
        data = {
            "name": "Minimal Feed",
            "url": "https://example.com/minimal.xml",
        }
        response = client.post("/api/v1/feeds", json=data)

        assert response.status_code == 201
        assert response.json()["name"] == "Minimal Feed"
        assert response.json()["is_active"] is True

    def test_create_feed_with_all_optional_fields(self, client: TestClient):
        """Test creating feed with all optional fields."""
        data = {
            "name": "Complete Feed",
            "url": "https://complete.example.com/feed.xml",
            "description": "A complete feed configuration",
            "category": "Technology",
            "fetch_interval": 120,
            "scrape_full_content": True,
            "scrape_method": "playwright",
            "scrape_failure_threshold": 7,
            "enable_categorization": True,
            "enable_finance_sentiment": True,
            "enable_geopolitical_sentiment": True,
            "enable_analysis_v2": True,
        }
        response = client.post("/api/v1/feeds", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["description"] == "A complete feed configuration"
        assert result["fetch_interval"] == 120
        assert result["scrape_full_content"] is True
        assert result["enable_categorization"] is True

    def test_create_feed_missing_required_field(self, client: TestClient):
        """Test validation requires name."""
        data = {
            "url": "https://example.com/feed.xml",
            # Missing name
        }
        response = client.post("/api/v1/feeds", json=data)

        assert response.status_code == 422

    def test_create_feed_invalid_url(self, client: TestClient):
        """Test validation of URL format."""
        data = {
            "name": "Bad URL Feed",
            "url": "not-a-url",
        }
        response = client.post("/api/v1/feeds", json=data)

        # Should reject invalid URL
        assert response.status_code == 422

    def test_create_feed_invalid_scrape_method(self, client: TestClient):
        """Test scrape_method enum validation."""
        data = {
            "name": "Invalid Method Feed",
            "url": "https://example.com/feed.xml",
            "scrape_method": "invalid_method",
        }
        response = client.post("/api/v1/feeds", json=data)

        assert response.status_code == 422

    def test_create_feed_invalid_scrape_threshold(self, client: TestClient):
        """Test scrape_failure_threshold range validation (1-20)."""
        invalid_thresholds = [0, -1, 21, 100]

        for threshold in invalid_thresholds:
            data = {
                "name": "Invalid Threshold Feed",
                "url": f"https://example.com/feed{threshold}.xml",
                "scrape_failure_threshold": threshold,
            }
            response = client.post("/api/v1/feeds", json=data)
            assert response.status_code == 422

    def test_create_feed_invalid_fetch_interval(self, client: TestClient):
        """Test fetch_interval validation."""
        data = {
            "name": "Invalid Interval Feed",
            "url": "https://example.com/feed.xml",
            "fetch_interval": -5,
        }
        response = client.post("/api/v1/feeds", json=data)

        assert response.status_code == 422


class TestFeedUpdateEndpoint:
    """Test PUT/PATCH /api/v1/feeds/{id} endpoint."""

    def test_update_feed_partial(self, client: TestClient, sample_feed_data):
        """Test partial update with PATCH."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        assert response.status_code == 201
        feed_id = response.json()["id"]

        # Update just name
        update = {"name": "Updated Name Only"}
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Name Only"
        assert result["url"] == sample_feed_data["url"]  # Unchanged

    def test_update_feed_url_immutable(self, client: TestClient, sample_feed_data):
        """Test that URL cannot be updated."""
        # Create feed
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        # Try to update URL
        update = {"url": "https://new-url.com/feed.xml"}
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        # Should succeed but URL unchanged
        assert response.status_code == 200
        result = response.json()
        assert result["url"] == sample_feed_data["url"]

    def test_update_feed_nonexistent(self, client: TestClient):
        """Test updating non-existent feed."""
        fake_id = str(uuid4())
        response = client.patch(f"/api/v1/feeds/{fake_id}", json={"name": "New"})

        assert response.status_code == 404

    def test_update_feed_health_fields(self, client: TestClient, sample_feed_data):
        """Test updating health-related fields."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        update = {
            "status": "ERROR",
            "health_score": 50,
            "consecutive_failures": 3,
        }
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        assert response.status_code == 200
        result = response.json()
        assert result["health_score"] == 50

    def test_update_feed_scraping_config(self, client: TestClient, sample_feed_data):
        """Test updating scraping configuration."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        update = {
            "scrape_full_content": True,
            "scrape_method": "playwright",
            "scrape_failure_threshold": 10,
        }
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        assert response.status_code == 200
        result = response.json()
        assert result["scrape_full_content"] is True
        assert result["scrape_method"] == "playwright"

    def test_update_feed_analysis_flags(self, client: TestClient, sample_feed_data):
        """Test updating analysis configuration flags."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        update = {
            "enable_categorization": True,
            "enable_finance_sentiment": True,
            "enable_analysis_v2": True,
        }
        response = client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        assert response.status_code == 200
        result = response.json()
        assert result["enable_categorization"] is True


class TestFeedDeleteEndpoint:
    """Test DELETE /api/v1/feeds/{id} endpoint."""

    def test_delete_feed_success(self, client: TestClient, sample_feed_data):
        """Test successful feed deletion."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        response = client.delete(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 204

        # Verify gone
        response = client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_feed(self, client: TestClient):
        """Test deleting non-existent feed."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/feeds/{fake_id}")

        assert response.status_code == 404

    def test_delete_feed_cascades_items(self, client: TestClient, sample_feed_data, db_session):
        """Test that deleting feed cascades to items."""
        # Create feed via API
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        # Add item directly to database (API doesn't have item creation)
        from uuid import UUID
        feed_uuid = UUID(feed_id)

        item = FeedItem(
            feed_id=feed_uuid,
            title="Item to Delete",
            link="https://example.com/item",
            content_hash="hash123",
        )
        db_session.add(item)
        db_session.commit()

        # Verify item exists
        response = client.get(f"/api/v1/feeds/{feed_id}/items")
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Delete feed
        response = client.delete(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 204

        # Verify item is gone
        response = client.get(f"/api/v1/feeds/{feed_id}/items")
        assert response.status_code == 404


class TestFeedListEndpoint:
    """Test GET /api/v1/feeds endpoint."""

    def test_list_feeds_empty(self, client: TestClient):
        """Test listing feeds when none exist."""
        response = client.get("/api/v1/feeds")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_feeds_pagination(self, client: TestClient, sample_feed_data):
        """Test pagination of feed list."""
        # Create 10 feeds
        for i in range(10):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            data["name"] = f"Feed {i}"
            client.post("/api/v1/feeds", json=data)

        # Test skip/limit
        response = client.get("/api/v1/feeds?skip=0&limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

        response = client.get("/api/v1/feeds?skip=5&limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_list_feeds_filter_by_status(self, client: TestClient, sample_feed_data):
        """Test filtering feeds by status."""
        # Create active feed
        active_data = sample_feed_data.copy()
        active_data["url"] = "https://example.com/active.xml"
        response = client.post("/api/v1/feeds", json=active_data)
        active_id = response.json()["id"]

        # Create inactive feed
        inactive_data = sample_feed_data.copy()
        inactive_data["url"] = "https://example.com/inactive.xml"
        response = client.post("/api/v1/feeds", json=inactive_data)
        inactive_id = response.json()["id"]

        # Deactivate one
        client.patch(f"/api/v1/feeds/{inactive_id}", json={"is_active": False})

        # Filter by active status
        response = client.get("/api/v1/feeds?is_active=true")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == active_id

    def test_list_feeds_filter_by_health_score(self, client: TestClient, sample_feed_data):
        """Test filtering feeds by health score range."""
        # Create multiple feeds
        data1 = sample_feed_data.copy()
        data1["url"] = "https://example.com/healthy.xml"
        response = client.post("/api/v1/feeds", json=data1)
        healthy_id = response.json()["id"]

        data2 = sample_feed_data.copy()
        data2["url"] = "https://example.com/unhealthy.xml"
        response = client.post("/api/v1/feeds", json=data2)
        unhealthy_id = response.json()["id"]

        # Update health scores
        client.patch(f"/api/v1/feeds/{healthy_id}", json={"health_score": 95})
        client.patch(f"/api/v1/feeds/{unhealthy_id}", json={"health_score": 30})

        # Filter by health range
        response = client.get("/api/v1/feeds?health_score_min=80")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == healthy_id

    def test_list_feeds_sort_order(self, client: TestClient, sample_feed_data):
        """Test feeds are returned in consistent order."""
        for i in range(3):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            data["name"] = f"Feed {i}"
            client.post("/api/v1/feeds", json=data)

        response = client.get("/api/v1/feeds")
        names = [feed["name"] for feed in response.json()]

        # Second call should return same order
        response = client.get("/api/v1/feeds")
        names2 = [feed["name"] for feed in response.json()]

        assert names == names2


class TestFeedGetEndpoint:
    """Test GET /api/v1/feeds/{id} endpoint."""

    def test_get_feed_success(self, client: TestClient, sample_feed_data):
        """Test getting a specific feed."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        response = client.get(f"/api/v1/feeds/{feed_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == feed_id
        assert result["name"] == sample_feed_data["name"]

    def test_get_feed_includes_all_fields(self, client: TestClient, sample_feed_data):
        """Test that all fields are included in response."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        response = client.get(f"/api/v1/feeds/{feed_id}")
        result = response.json()

        # Check key fields
        required_fields = [
            "id", "name", "url", "description", "is_active", "status",
            "health_score", "consecutive_failures", "created_at", "updated_at"
        ]

        for field in required_fields:
            assert field in result

    def test_get_nonexistent_feed(self, client: TestClient):
        """Test getting non-existent feed."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/feeds/{fake_id}")

        assert response.status_code == 404

    def test_get_feed_invalid_id_format(self, client: TestClient):
        """Test getting feed with invalid UUID format."""
        response = client.get("/api/v1/feeds/not-a-uuid")

        assert response.status_code == 422 or response.status_code == 404


class TestFeedBulkOperations:
    """Test bulk operation endpoints."""

    def test_bulk_fetch_specific_feeds(self, client: TestClient, sample_feed_data):
        """Test bulk fetch for specific feeds."""
        # Create feeds
        feed_ids = []
        for i in range(3):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            response = client.post("/api/v1/feeds", json=data)
            feed_ids.append(response.json()["id"])

        # Bulk fetch specific ones
        response = client.post(
            "/api/v1/feeds/bulk-fetch",
            json={"feed_ids": feed_ids[:2], "force": False}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["total_feeds"] == 2

    def test_bulk_fetch_all_feeds(self, client: TestClient, sample_feed_data):
        """Test bulk fetch all feeds."""
        # Create feeds
        for i in range(3):
            data = sample_feed_data.copy()
            data["url"] = f"https://example.com/feed{i}.xml"
            client.post("/api/v1/feeds", json=data)

        # Bulk fetch all
        response = client.post(
            "/api/v1/feeds/bulk-fetch",
            json={"feed_ids": None, "force": True}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["total_feeds"] == 3

    def test_bulk_fetch_nonexistent_feed(self, client: TestClient):
        """Test bulk fetch with non-existent feed ID."""
        fake_id = str(uuid4())

        response = client.post(
            "/api/v1/feeds/bulk-fetch",
            json={"feed_ids": [fake_id], "force": False}
        )

        # Should handle gracefully
        assert response.status_code == 200


class TestFeedHealthEndpoint:
    """Test GET /api/v1/feeds/{id}/health endpoint."""

    def test_get_feed_health_initial(self, client: TestClient, sample_feed_data):
        """Test getting health metrics for new feed."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        response = client.get(f"/api/v1/feeds/{feed_id}/health")

        assert response.status_code == 200
        result = response.json()
        assert result["feed_id"] == feed_id
        assert result["health_score"] == 100
        assert result["is_healthy"] is True
        assert result["consecutive_failures"] == 0

    def test_get_feed_health_nonexistent(self, client: TestClient):
        """Test getting health for non-existent feed."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/feeds/{fake_id}/health")

        assert response.status_code == 404


class TestFeedQualityEndpoint:
    """Test GET /api/v1/feeds/{id}/quality endpoint."""

    def test_get_feed_quality_initial(self, client: TestClient, sample_feed_data):
        """Test getting quality metrics for new feed."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        response = client.get(f"/api/v1/feeds/{feed_id}/quality")

        assert response.status_code == 200
        result = response.json()
        assert result["feed_id"] == feed_id
        assert "quality_score" in result
        assert "freshness_score" in result
        assert "consistency_score" in result
        assert "content_score" in result
        assert "reliability_score" in result

    def test_get_feed_quality_nonexistent(self, client: TestClient):
        """Test getting quality for non-existent feed."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/feeds/{fake_id}/quality")

        assert response.status_code == 404


class TestFeedScrappingEndpoints:
    """Test scraping configuration endpoints."""

    def test_reset_scraping_failures(self, client: TestClient, sample_feed_data):
        """Test resetting scraping failures."""
        response = client.post("/api/v1/feeds", json=sample_feed_data)
        feed_id = response.json()["id"]

        # Simulate failures
        update = {
            "scrape_failure_count": 5,
            "scrape_disabled_reason": "auto_threshold",
            "scrape_full_content": False,
        }
        client.patch(f"/api/v1/feeds/{feed_id}", json=update)

        # Reset
        response = client.post(f"/api/v1/feeds/{feed_id}/scraping/reset")

        assert response.status_code == 200
        result = response.json()
        assert "successfully" in result.get("message", "").lower()

    def test_reset_nonexistent_feed_scraping(self, client: TestClient):
        """Test resetting scraping for non-existent feed."""
        fake_id = str(uuid4())
        response = client.post(f"/api/v1/feeds/{fake_id}/scraping/reset")

        assert response.status_code == 404
