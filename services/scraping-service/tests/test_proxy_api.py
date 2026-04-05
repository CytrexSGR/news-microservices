"""Tests for Proxy Manager API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.models.proxy import ProxyConfig, ProxyHealth, ProxyPoolStats, ProxyStatusEnum


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_proxy_manager():
    with patch('app.api.proxy.get_proxy_manager') as mock:
        manager = MagicMock()
        manager._proxies = {}
        mock.return_value = manager
        yield manager


class TestProxyAPI:
    def test_get_stats(self, client, mock_proxy_manager):
        mock_proxy_manager.get_stats.return_value = ProxyPoolStats(
            total_proxies=5,
            healthy_proxies=3,
            unhealthy_proxies=1,
            unknown_proxies=1,
            avg_response_time_ms=150.5,
            total_requests=1000,
            total_failures=50,
            success_rate=0.95
        )

        response = client.get("/api/v1/proxy/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_proxies"] == 5
        assert data["healthy_proxies"] == 3
        assert data["success_rate"] == 0.95

    def test_list_proxies_empty(self, client, mock_proxy_manager):
        response = client.get("/api/v1/proxy/list")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["proxies"] == []

    def test_add_proxy(self, client, mock_proxy_manager):
        response = client.post(
            "/api/v1/proxy/add",
            json={
                "id": "proxy1",
                "host": "proxy.example.com",
                "port": 8080,
                "username": "user",
                "password": "pass"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_proxy_manager.add_proxy.assert_called_once()

    def test_add_proxies_batch(self, client, mock_proxy_manager):
        mock_proxy_manager.add_proxies_from_list.return_value = 3

        response = client.post(
            "/api/v1/proxy/add-batch",
            json={
                "proxies": [
                    {"id": "p1", "host": "proxy1.com", "port": 8080},
                    {"id": "p2", "host": "proxy2.com", "port": 8080},
                    {"id": "p3", "host": "proxy3.com", "port": 8080}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxies_added"] == 3

    def test_remove_proxy(self, client, mock_proxy_manager):
        mock_proxy_manager.remove_proxy.return_value = True

        response = client.delete("/api/v1/proxy/proxy1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_proxy_manager.remove_proxy.assert_called_once_with("proxy1")

    def test_remove_proxy_not_found(self, client, mock_proxy_manager):
        mock_proxy_manager.remove_proxy.return_value = False

        response = client.delete("/api/v1/proxy/nonexistent")

        assert response.status_code == 404

    def test_get_proxy_health(self, client, mock_proxy_manager):
        mock_proxy_manager.get_health.return_value = ProxyHealth(
            proxy_id="proxy1",
            status=ProxyStatusEnum.HEALTHY,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            consecutive_failures=0,
            avg_response_time_ms=150.0,
            last_success_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        response = client.get("/api/v1/proxy/health/proxy1")

        assert response.status_code == 200
        data = response.json()
        assert data["proxy_id"] == "proxy1"
        assert data["status"] == "healthy"
        assert data["total_requests"] == 100

    def test_get_proxy_health_not_found(self, client, mock_proxy_manager):
        mock_proxy_manager.get_health.return_value = None

        response = client.get("/api/v1/proxy/health/nonexistent")

        assert response.status_code == 404

    def test_reset_unhealthy_proxies(self, client, mock_proxy_manager):
        mock_proxy_manager.reset_unhealthy_proxies.return_value = 2

        response = client.post("/api/v1/proxy/reset-unhealthy")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxies_reset"] == 2

    def test_clear_domain_affinity(self, client, mock_proxy_manager):
        mock_proxy_manager.clear_domain_affinity.return_value = 5

        response = client.post("/api/v1/proxy/clear-affinity?domain=example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affinities_cleared"] == 5

    def test_clear_all_domain_affinity(self, client, mock_proxy_manager):
        mock_proxy_manager.clear_domain_affinity.return_value = 10

        response = client.post("/api/v1/proxy/clear-affinity")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affinities_cleared"] == 10

    def test_get_proxy_for_domain(self, client, mock_proxy_manager):
        mock_proxy = MagicMock()
        mock_proxy.id = "proxy1"
        mock_proxy.host = "proxy.example.com"
        mock_proxy.port = 8080
        mock_proxy.url_masked = "http://user:***@proxy.example.com:8080"
        mock_proxy_manager.get_proxy_for_domain.return_value = mock_proxy

        response = client.get("/api/v1/proxy/for-domain/example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "example.com"
        assert data["proxy"]["id"] == "proxy1"

    def test_get_proxy_for_domain_none(self, client, mock_proxy_manager):
        mock_proxy_manager.get_proxy_for_domain.return_value = None

        response = client.get("/api/v1/proxy/for-domain/example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["proxy"] is None
