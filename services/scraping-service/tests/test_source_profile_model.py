"""Tests for Source Profile Model"""
import pytest
from datetime import datetime
from app.models.source_profile import (
    SourceProfile,
    SourceProfileCreate,
    SourceProfileUpdate,
    ScrapeMethodEnum,
    PaywallTypeEnum,
    ScrapeStatusEnum,
    SourceProfileMetricsUpdate
)


class TestSourceProfileModel:
    def test_create_source_profile(self):
        """Test creating a source profile with all fields"""
        profile = SourceProfile(
            id=1,
            domain="example.com",
            scrape_method=ScrapeMethodEnum.NEWSPAPER4K,
            paywall_type=PaywallTypeEnum.NONE,
            success_rate=0.95,
            avg_response_time_ms=250,
            total_attempts=100,
            total_successes=95
        )

        assert profile.domain == "example.com"
        assert profile.scrape_method == ScrapeMethodEnum.NEWSPAPER4K
        assert profile.success_rate == 0.95
        assert profile.total_attempts == 100
        assert profile.total_successes == 95

    def test_source_profile_defaults(self):
        """Test source profile has sensible defaults"""
        profile = SourceProfile(
            id=1,
            domain="test.com"
        )

        assert profile.scrape_method == ScrapeMethodEnum.NEWSPAPER4K
        assert profile.paywall_type == PaywallTypeEnum.UNKNOWN
        assert profile.scrape_status == ScrapeStatusEnum.UNKNOWN
        assert profile.success_rate == 0.0
        assert profile.requires_ua_rotation is True
        assert profile.requires_stealth is False
        assert profile.requires_proxy is False

    def test_scrape_method_enum_values(self):
        """Verify all scrape method enum values"""
        assert ScrapeMethodEnum.NEWSPAPER4K.value == "newspaper4k"
        assert ScrapeMethodEnum.TRAFILATURA.value == "trafilatura"
        assert ScrapeMethodEnum.PLAYWRIGHT.value == "playwright"
        assert ScrapeMethodEnum.PLAYWRIGHT_STEALTH.value == "playwright_stealth"
        assert ScrapeMethodEnum.HTTPX_BASIC.value == "httpx_basic"
        assert ScrapeMethodEnum.JSONLD.value == "jsonld"

    def test_paywall_type_enum_values(self):
        """Verify all paywall type enum values"""
        assert PaywallTypeEnum.NONE.value == "none"
        assert PaywallTypeEnum.SOFT.value == "soft"
        assert PaywallTypeEnum.HARD.value == "hard"
        assert PaywallTypeEnum.METERED.value == "metered"
        assert PaywallTypeEnum.REGISTRATION.value == "registration"
        assert PaywallTypeEnum.UNKNOWN.value == "unknown"

    def test_scrape_status_enum_values(self):
        """Verify all scrape status enum values"""
        assert ScrapeStatusEnum.WORKING.value == "working"
        assert ScrapeStatusEnum.DEGRADED.value == "degraded"
        assert ScrapeStatusEnum.BLOCKED.value == "blocked"
        assert ScrapeStatusEnum.UNSUPPORTED.value == "unsupported"
        assert ScrapeStatusEnum.UNKNOWN.value == "unknown"

    def test_source_profile_create_schema(self):
        """Test creating profile via create schema"""
        create_data = SourceProfileCreate(
            domain="news-site.com",
            scrape_method=ScrapeMethodEnum.PLAYWRIGHT
        )
        assert create_data.domain == "news-site.com"
        assert create_data.scrape_method == ScrapeMethodEnum.PLAYWRIGHT
        assert create_data.paywall_type == PaywallTypeEnum.UNKNOWN  # default

    def test_source_profile_update_schema(self):
        """Test update schema with partial fields"""
        update_data = SourceProfileUpdate(
            scrape_method=ScrapeMethodEnum.TRAFILATURA,
            requires_stealth=True
        )
        assert update_data.scrape_method == ScrapeMethodEnum.TRAFILATURA
        assert update_data.requires_stealth is True
        assert update_data.paywall_type is None  # not set

    def test_source_profile_metrics_update(self):
        """Test metrics update schema"""
        metrics = SourceProfileMetricsUpdate(
            success=True,
            response_time_ms=150,
            word_count=500,
            extraction_quality=0.85,
            method_used=ScrapeMethodEnum.NEWSPAPER4K
        )

        assert metrics.success is True
        assert metrics.response_time_ms == 150
        assert metrics.word_count == 500
        assert metrics.extraction_quality == 0.85
        assert metrics.method_used == ScrapeMethodEnum.NEWSPAPER4K

    def test_source_profile_with_fallback_methods(self):
        """Test profile with fallback methods list"""
        profile = SourceProfile(
            id=1,
            domain="complex-site.com",
            scrape_method=ScrapeMethodEnum.NEWSPAPER4K,
            fallback_methods=[
                ScrapeMethodEnum.TRAFILATURA,
                ScrapeMethodEnum.PLAYWRIGHT
            ]
        )

        assert len(profile.fallback_methods) == 2
        assert profile.fallback_methods[0] == ScrapeMethodEnum.TRAFILATURA
        assert profile.fallback_methods[1] == ScrapeMethodEnum.PLAYWRIGHT

    def test_source_profile_with_custom_headers(self):
        """Test profile with custom headers"""
        profile = SourceProfile(
            id=1,
            domain="api-site.com",
            custom_headers={
                "X-Custom-Header": "value",
                "Authorization": "Bearer token123"
            }
        )

        assert "X-Custom-Header" in profile.custom_headers
        assert profile.custom_headers["X-Custom-Header"] == "value"
