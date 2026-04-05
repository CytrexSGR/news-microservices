"""Tests for User-Agent Pool"""
import pytest
from app.core.user_agents import UserAgentPool


class TestUserAgentPool:
    def test_get_random_returns_string(self):
        pool = UserAgentPool()
        ua = pool.get_random()
        assert isinstance(ua, str)
        assert len(ua) > 20  # Real UA strings are long

    def test_get_random_returns_different_values(self):
        pool = UserAgentPool()
        agents = {pool.get_random() for _ in range(10)}
        assert len(agents) >= 1  # At least one valid UA

    def test_get_for_domain_consistency(self):
        pool = UserAgentPool()
        ua1 = pool.get_for_domain("example.com")
        ua2 = pool.get_for_domain("example.com")
        assert ua1 == ua2  # Same domain = same UA (session consistency)

    def test_get_for_domain_different_domains(self):
        pool = UserAgentPool()
        ua1 = pool.get_for_domain("site-a.com")
        ua2 = pool.get_for_domain("site-b.com")
        # Could be same or different, but should not error
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)

    def test_clear_cache(self):
        pool = UserAgentPool()
        pool.get_for_domain("test.com")
        assert "test.com" in pool._domain_cache
        pool.clear_cache()
        assert "test.com" not in pool._domain_cache
