"""Tests for Source Registry Service"""
import pytest
from unittest.mock import MagicMock
from app.services.source_registry import SourceRegistry, get_source_registry
from app.models.source_profile import (
    ScrapeMethodEnum,
    PaywallTypeEnum,
    ScrapeStatusEnum,
    SourceProfileCreate,
    SourceProfileUpdate,
    SourceProfileMetricsUpdate
)


class TestSourceRegistry:
    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test"""
        reg = SourceRegistry()
        reg.clear_cache()
        return reg

    def test_extract_domain_from_url(self, registry):
        """Test domain extraction from URLs"""
        assert registry._extract_domain("https://www.example.com/article") == "example.com"
        assert registry._extract_domain("https://news.bbc.co.uk/story") == "news.bbc.co.uk"
        assert registry._extract_domain("http://test.de") == "test.de"
        assert registry._extract_domain("https://www.spiegel.de/politik/article-123") == "spiegel.de"

    def test_get_profile_returns_none_for_unknown(self, registry):
        """Test get_profile returns None for unknown domains"""
        profile = registry.get_profile("https://unknown-site.com/page")
        assert profile is None

    def test_get_or_create_profile_creates_new(self, registry):
        """Test get_or_create_profile creates new profile"""
        profile = registry.get_or_create_profile("https://new-site.com/article")

        assert profile is not None
        assert profile.domain == "new-site.com"
        assert profile.scrape_method == ScrapeMethodEnum.NEWSPAPER4K
        assert profile.scrape_status == ScrapeStatusEnum.UNKNOWN

    def test_get_or_create_profile_returns_existing(self, registry):
        """Test get_or_create_profile returns existing profile"""
        # Create first
        profile1 = registry.get_or_create_profile("https://existing.com/page1")

        # Get again
        profile2 = registry.get_or_create_profile("https://existing.com/page2")

        assert profile1.id == profile2.id
        assert profile1.domain == profile2.domain

    def test_select_best_method_default(self, registry):
        """Test default method selection"""
        method = registry._select_best_method(None)
        assert method == ScrapeMethodEnum.NEWSPAPER4K

    def test_select_best_method_keeps_working(self, registry):
        """Test method selection keeps working method"""
        from app.models.source_profile import SourceProfile

        profile = SourceProfile(
            id=1,
            domain="test.com",
            scrape_method=ScrapeMethodEnum.TRAFILATURA,
            scrape_status=ScrapeStatusEnum.WORKING
        )

        method = registry._select_best_method(profile)
        assert method == ScrapeMethodEnum.TRAFILATURA

    def test_select_best_method_uses_fallback_for_degraded(self, registry):
        """Test method selection uses fallback for degraded status"""
        from app.models.source_profile import SourceProfile

        profile = SourceProfile(
            id=1,
            domain="test.com",
            scrape_method=ScrapeMethodEnum.NEWSPAPER4K,
            scrape_status=ScrapeStatusEnum.DEGRADED,
            fallback_methods=[ScrapeMethodEnum.TRAFILATURA, ScrapeMethodEnum.PLAYWRIGHT]
        )

        method = registry._select_best_method(profile)
        assert method == ScrapeMethodEnum.TRAFILATURA

    def test_calculate_success_rate(self, registry):
        """Test success rate calculation"""
        # 90 successes out of 100 total
        rate = registry._calculate_success_rate(90, 100, True)
        assert rate == pytest.approx(0.9, rel=0.01)

        # 50 out of 100
        rate = registry._calculate_success_rate(50, 100, False)
        assert rate == pytest.approx(0.5, rel=0.01)

    def test_determine_status_unknown_for_few_attempts(self, registry):
        """Test status is unknown with few attempts"""
        status = registry._determine_status(3, 3)
        assert status == ScrapeStatusEnum.UNKNOWN

    def test_determine_status_working(self, registry):
        """Test working status for high success rate"""
        status = registry._determine_status(100, 90)
        assert status == ScrapeStatusEnum.WORKING

    def test_determine_status_degraded(self, registry):
        """Test degraded status for medium success rate"""
        status = registry._determine_status(100, 60)
        assert status == ScrapeStatusEnum.DEGRADED

    def test_determine_status_blocked(self, registry):
        """Test blocked status for low success rate"""
        status = registry._determine_status(100, 30)
        assert status == ScrapeStatusEnum.BLOCKED

    def test_update_metrics_success(self, registry):
        """Test metrics update after successful scrape"""
        url = "https://test-site.com/article"

        # First create profile
        registry.get_or_create_profile(url)

        # Update with success
        metrics = SourceProfileMetricsUpdate(
            success=True,
            response_time_ms=150,
            word_count=500,
            extraction_quality=0.9,
            method_used=ScrapeMethodEnum.NEWSPAPER4K
        )

        updated = registry.update_metrics(url, metrics)

        assert updated.total_attempts == 1
        assert updated.total_successes == 1
        assert updated.total_failures == 0
        assert updated.success_rate == 1.0
        assert updated.avg_word_count == 500
        assert updated.last_successful_scrape is not None

    def test_update_metrics_failure(self, registry):
        """Test metrics update after failed scrape"""
        url = "https://fail-site.com/article"

        # First create profile
        registry.get_or_create_profile(url)

        # Update with failure
        metrics = SourceProfileMetricsUpdate(
            success=False,
            response_time_ms=5000,
            word_count=0,
            extraction_quality=0.0,
            method_used=ScrapeMethodEnum.NEWSPAPER4K,
            error_message="Timeout"
        )

        updated = registry.update_metrics(url, metrics)

        assert updated.total_attempts == 1
        assert updated.total_successes == 0
        assert updated.total_failures == 1
        assert updated.success_rate == 0.0
        assert updated.last_failed_scrape is not None

    def test_get_scrape_config(self, registry):
        """Test getting scrape config"""
        config = registry.get_scrape_config("https://new-domain.com/page")

        assert "method" in config
        assert "fallback_methods" in config
        assert "requires_ua_rotation" in config
        assert "rate_limit" in config
        assert "paywall_type" in config

    def test_list_profiles(self, registry):
        """Test listing profiles"""
        # Create some profiles
        registry.get_or_create_profile("https://site1.com/a")
        registry.get_or_create_profile("https://site2.com/b")
        registry.get_or_create_profile("https://site3.com/c")

        profiles = registry.list_profiles()
        assert len(profiles) == 3

    def test_list_profiles_with_filter(self, registry):
        """Test listing profiles with status filter"""
        # Create profiles
        registry.get_or_create_profile("https://site1.com/a")
        registry.get_or_create_profile("https://site2.com/b")

        # All should be UNKNOWN initially
        profiles = registry.list_profiles(status=ScrapeStatusEnum.UNKNOWN)
        assert len(profiles) == 2

        profiles = registry.list_profiles(status=ScrapeStatusEnum.WORKING)
        assert len(profiles) == 0

    def test_update_profile(self, registry):
        """Test manual profile update"""
        # Create profile
        registry.get_or_create_profile("https://update-test.com/page")

        # Update it
        update = SourceProfileUpdate(
            scrape_method=ScrapeMethodEnum.PLAYWRIGHT,
            requires_stealth=True,
            notes="Needs JS rendering"
        )

        updated = registry.update_profile("update-test.com", update)

        assert updated.scrape_method == ScrapeMethodEnum.PLAYWRIGHT
        assert updated.requires_stealth is True
        assert updated.notes == "Needs JS rendering"

    def test_update_profile_unknown_domain(self, registry):
        """Test update returns None for unknown domain"""
        update = SourceProfileUpdate(requires_stealth=True)
        result = registry.update_profile("unknown.com", update)
        assert result is None

    def test_clear_cache(self, registry):
        """Test cache clearing"""
        registry.get_or_create_profile("https://site.com/a")
        assert len(registry._cache) == 1

        registry.clear_cache()
        assert len(registry._cache) == 0

    def test_get_statistics(self, registry):
        """Test registry statistics"""
        # Empty stats
        stats = registry.get_statistics()
        assert stats["total_sources"] == 0

        # Add some profiles
        registry.get_or_create_profile("https://site1.com/a")
        registry.get_or_create_profile("https://site2.com/b")

        stats = registry.get_statistics()
        assert stats["total_sources"] == 2
        assert stats["unknown"] == 2  # All new profiles are unknown

    def test_singleton_instance(self):
        """Test singleton pattern"""
        reg1 = get_source_registry()
        reg2 = get_source_registry()
        assert reg1 is reg2
