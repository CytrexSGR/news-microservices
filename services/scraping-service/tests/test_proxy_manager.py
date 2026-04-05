"""Tests for Proxy Manager"""
import pytest
from app.services.proxy_manager import ProxyManager, get_proxy_manager
from app.models.proxy import ProxyConfig, ProxyRotationConfig, ProxyTypeEnum, ProxyStatusEnum


class TestProxyManager:
    @pytest.fixture
    def manager(self):
        config = ProxyRotationConfig(enabled=True)
        return ProxyManager(config)

    @pytest.fixture
    def sample_proxies(self):
        return [
            {"id": "proxy1", "host": "proxy1.example.com", "port": 8080},
            {"id": "proxy2", "host": "proxy2.example.com", "port": 8080},
            {"id": "proxy3", "host": "proxy3.example.com", "port": 8080},
        ]

    def test_add_proxy(self, manager):
        proxy = ProxyConfig(
            id="test1",
            host="proxy.example.com",
            port=8080
        )
        manager.add_proxy(proxy)

        assert "test1" in manager._proxies
        assert "test1" in manager._health

    def test_add_proxies_from_list(self, manager, sample_proxies):
        added = manager.add_proxies_from_list(sample_proxies)

        assert added == 3
        assert len(manager._proxies) == 3

    def test_remove_proxy(self, manager):
        proxy = ProxyConfig(id="test1", host="proxy.example.com", port=8080)
        manager.add_proxy(proxy)

        result = manager.remove_proxy("test1")
        assert result is True
        assert "test1" not in manager._proxies

    def test_remove_nonexistent_proxy(self, manager):
        result = manager.remove_proxy("nonexistent")
        assert result is False

    def test_get_proxy_for_domain_disabled(self, manager):
        manager.config.enabled = False
        result = manager.get_proxy_for_domain("example.com")
        assert result is None

    def test_get_proxy_for_domain_no_proxies(self, manager):
        result = manager.get_proxy_for_domain("example.com")
        assert result is None

    def test_get_proxy_for_domain_round_robin(self, manager, sample_proxies):
        manager.add_proxies_from_list(sample_proxies)

        # Get proxies in round-robin order
        first = manager.get_proxy_for_domain("example1.com")
        second = manager.get_proxy_for_domain("example2.com")
        third = manager.get_proxy_for_domain("example3.com")

        assert first is not None
        assert second is not None
        assert third is not None

    def test_get_proxy_excluded_domain(self, manager, sample_proxies):
        manager.config.excluded_domains = ["excluded.com"]
        manager.add_proxies_from_list(sample_proxies)

        result = manager.get_proxy_for_domain("excluded.com")
        assert result is None

    def test_domain_affinity(self, manager, sample_proxies):
        manager.add_proxies_from_list(sample_proxies)

        # First request establishes affinity
        first = manager.get_proxy_for_domain("example.com")
        # Second request should return same proxy
        second = manager.get_proxy_for_domain("example.com")

        assert first.id == second.id

    def test_record_success(self, manager):
        proxy = ProxyConfig(id="test1", host="proxy.example.com", port=8080)
        manager.add_proxy(proxy)

        manager.record_success("test1", 150.0)

        health = manager.get_health("test1")
        assert health.total_requests == 1
        assert health.successful_requests == 1
        assert health.status == ProxyStatusEnum.HEALTHY

    def test_record_failure(self, manager):
        proxy = ProxyConfig(id="test1", host="proxy.example.com", port=8080)
        manager.add_proxy(proxy)

        manager.record_failure("test1", "Connection timeout")

        health = manager.get_health("test1")
        assert health.total_requests == 1
        assert health.failed_requests == 1
        assert health.consecutive_failures == 1

    def test_circuit_breaking(self, manager):
        proxy = ProxyConfig(id="test1", host="proxy.example.com", port=8080)
        manager.add_proxy(proxy)
        manager.config.max_consecutive_failures = 3

        # Record multiple failures
        for _ in range(3):
            manager.record_failure("test1", "Error")

        health = manager.get_health("test1")
        assert health.status == ProxyStatusEnum.UNHEALTHY

    def test_get_stats(self, manager, sample_proxies):
        manager.add_proxies_from_list(sample_proxies)

        stats = manager.get_stats()
        assert stats.total_proxies == 3
        assert stats.unknown_proxies == 3

    def test_reset_unhealthy_proxies(self, manager):
        proxy = ProxyConfig(id="test1", host="proxy.example.com", port=8080)
        manager.add_proxy(proxy)
        manager.config.recovery_timeout_seconds = 0  # Immediate recovery

        # Mark as unhealthy
        for _ in range(3):
            manager.record_failure("test1")

        # Reset
        count = manager.reset_unhealthy_proxies()
        assert count == 1

        health = manager.get_health("test1")
        assert health.status == ProxyStatusEnum.UNKNOWN

    def test_clear_domain_affinity(self, manager, sample_proxies):
        manager.add_proxies_from_list(sample_proxies)
        manager.get_proxy_for_domain("example.com")

        count = manager.clear_domain_affinity("example.com")
        assert count == 1

    def test_clear_all_domain_affinity(self, manager, sample_proxies):
        manager.add_proxies_from_list(sample_proxies)
        manager.get_proxy_for_domain("example1.com")
        manager.get_proxy_for_domain("example2.com")

        count = manager.clear_domain_affinity()
        assert count == 2

    def test_proxy_url_generation(self):
        proxy = ProxyConfig(
            id="test",
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass"
        )
        assert "user:pass@" in proxy.url
        assert "user:***@" in proxy.url_masked

    def test_singleton_instance(self):
        m1 = get_proxy_manager()
        m2 = get_proxy_manager()
        assert m1 is m2
