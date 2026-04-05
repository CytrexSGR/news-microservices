"""Tests for news API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.news import router, get_client, get_tracker


def create_test_app():
    """Create a test app without lifespan."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    return test_app


def create_mock_client(mock_response=None):
    """Create a mock MediaStack client."""
    mock = MagicMock()
    mock.fetch_live_news = AsyncMock(return_value=mock_response or {})
    mock.fetch_historical_news = AsyncMock(return_value=mock_response or {})
    mock.get_sources = AsyncMock(return_value=mock_response or {})
    return mock


def create_mock_tracker(
    can_request=True,
    current_calls=1,
    remaining=9999,
    status="ok"
):
    """Create a mock usage tracker."""
    mock = MagicMock()
    mock.can_make_request = AsyncMock(return_value=can_request)
    mock.record_request = AsyncMock(return_value=current_calls)
    mock.get_usage_stats = AsyncMock(return_value={
        "current_calls": current_calls,
        "monthly_limit": 10000,
        "remaining": remaining,
        "percentage": (current_calls / 10000) * 100,
        "month": "2025-12",
        "days_remaining": 5,
        "calls_per_day_remaining": remaining // 5 if remaining > 0 else 0,
        "status": status
    })
    return mock


class TestLiveNewsEndpoint:
    """Tests for GET /api/v1/news/live endpoint."""

    def test_get_live_news_success(self):
        """Test successful live news fetch."""
        test_app = create_test_app()

        mock_response = {
            "pagination": {"limit": 25, "offset": 0, "count": 1, "total": 100},
            "data": [{
                "author": "Test Author",
                "title": "Test Article",
                "description": "Test description",
                "url": "https://example.com/article",
                "source": "cnn",
                "image": None,
                "category": "general",
                "language": "en",
                "country": "us",
                "published_at": "2025-12-26T12:00:00+00:00"
            }]
        }

        mock_client = create_mock_client(mock_response)
        mock_tracker = create_mock_tracker()

        test_app.dependency_overrides[get_client] = lambda: mock_client
        test_app.dependency_overrides[get_tracker] = lambda: mock_tracker

        client = TestClient(test_app)
        response = client.get("/api/v1/news/live?keywords=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Test Article"
        assert data["usage"]["remaining"] == 9999

        # Cleanup
        test_app.dependency_overrides.clear()

    def test_get_live_news_rate_limited(self):
        """Test rate limit exceeded response."""
        test_app = create_test_app()

        mock_client = create_mock_client()
        mock_tracker = create_mock_tracker(
            can_request=False,
            current_calls=10000,
            remaining=0,
            status="critical"
        )

        test_app.dependency_overrides[get_client] = lambda: mock_client
        test_app.dependency_overrides[get_tracker] = lambda: mock_tracker

        client = TestClient(test_app)
        response = client.get("/api/v1/news/live")

        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"]["error"].lower()

        test_app.dependency_overrides.clear()


class TestUsageEndpoint:
    """Tests for GET /api/v1/news/usage endpoint."""

    def test_get_usage_stats(self):
        """Test usage stats endpoint."""
        test_app = create_test_app()

        mock_tracker = create_mock_tracker(
            current_calls=500,
            remaining=9500,
            status="ok"
        )

        test_app.dependency_overrides[get_tracker] = lambda: mock_tracker

        client = TestClient(test_app)
        response = client.get("/api/v1/news/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["current_calls"] == 500
        assert data["status"] == "ok"

        test_app.dependency_overrides.clear()


class TestSourcesEndpoint:
    """Tests for GET /api/v1/news/sources endpoint."""

    def test_get_sources_success(self):
        """Test successful sources fetch."""
        test_app = create_test_app()

        mock_response = {
            "data": [
                {"id": "cnn", "name": "CNN", "category": "general", "country": "us", "language": "en"},
                {"id": "bbc", "name": "BBC", "category": "general", "country": "gb", "language": "en"}
            ]
        }

        mock_client = create_mock_client()
        mock_client.get_sources = AsyncMock(return_value=mock_response)
        mock_tracker = create_mock_tracker()

        test_app.dependency_overrides[get_client] = lambda: mock_client
        test_app.dependency_overrides[get_tracker] = lambda: mock_tracker

        client = TestClient(test_app)
        response = client.get("/api/v1/news/sources")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "cnn"

        test_app.dependency_overrides.clear()
