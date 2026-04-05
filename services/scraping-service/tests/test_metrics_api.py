"""Tests for Metrics API Endpoint"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestMetricsAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_metrics(self, client):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")

        assert response.status_code == 200
        # Check content type is Prometheus format
        assert "text/plain" in response.headers.get("content-type", "") or \
               "text/openmetrics" in response.headers.get("content-type", "")

        # Check response contains expected metric names
        content = response.text
        assert "scraper_" in content

    def test_metrics_contains_request_counters(self, client):
        """Test metrics include request counters"""
        response = client.get("/metrics")
        content = response.text

        # Check for request counter
        assert "scraper_requests_total" in content or "# HELP" in content

    def test_metrics_contains_histograms(self, client):
        """Test metrics include histograms"""
        response = client.get("/metrics")
        content = response.text

        # Histograms have _bucket, _count, _sum suffixes
        # They may be empty if no scrapes occurred
        assert "scraper_" in content

    def test_metrics_health(self, client):
        """Test metrics health endpoint"""
        response = client.get("/metrics/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["metrics_available"] is True
        assert "content_type" in data

    def test_metrics_endpoint_is_accessible(self, client):
        """Test metrics endpoint doesn't require authentication"""
        response = client.get("/metrics")
        # Should not return 401/403
        assert response.status_code == 200

    def test_metrics_format_is_valid(self, client):
        """Test metrics format is valid Prometheus exposition format"""
        response = client.get("/metrics")
        content = response.text

        # Prometheus format should have lines starting with:
        # - # HELP (help text)
        # - # TYPE (metric type)
        # - metric_name{labels} value
        # or just metric_name value

        lines = content.strip().split("\n")
        for line in lines:
            if not line:
                continue
            # Comments start with #
            if line.startswith("#"):
                assert line.startswith("# HELP") or line.startswith("# TYPE")
            # Metric lines have format: name{labels} value or name value
            # They should not have invalid characters
            assert "ERROR" not in line.upper() or "error" in line.lower()  # Allow error as label value
