"""Tests for User-Agent Rotation in Scraper"""
import pytest
from app.services.scraper import ContentScraper
from app.core.user_agents import get_user_agent_pool


class TestScraperUARotation:
    def test_scraper_uses_dynamic_user_agent(self):
        """Verify scraper gets UA from pool, not static config"""
        pool = get_user_agent_pool()
        ua = pool.get_for_domain("test.com")

        # UA should be a real browser string, not our bot identifier
        assert "Mozilla" in ua
        assert len(ua) > 50

    def test_same_domain_gets_consistent_ua(self):
        """Same domain should get same UA for session consistency"""
        pool = get_user_agent_pool()
        ua1 = pool.get_for_domain("news-site.com")
        ua2 = pool.get_for_domain("news-site.com")

        assert ua1 == ua2

    def test_get_ua_for_url_extracts_domain(self):
        """Test _get_ua_for_url method extracts domain correctly"""
        scraper = ContentScraper()
        # Mock UA pool
        scraper._ua_pool = get_user_agent_pool()

        from app.core.config import settings
        original_setting = settings.ENABLE_UA_ROTATION
        settings.ENABLE_UA_ROTATION = True

        try:
            ua1 = scraper._get_ua_for_url("https://example.com/article/123")
            ua2 = scraper._get_ua_for_url("https://example.com/different/path")

            # Same domain should get same UA
            assert ua1 == ua2
            assert "Mozilla" in ua1
        finally:
            settings.ENABLE_UA_ROTATION = original_setting

    def test_ua_rotation_disabled_uses_static(self):
        """When UA rotation disabled, should use static config"""
        scraper = ContentScraper()
        scraper._ua_pool = None

        from app.core.config import settings
        original_setting = settings.ENABLE_UA_ROTATION
        settings.ENABLE_UA_ROTATION = False

        try:
            ua = scraper._get_ua_for_url("https://test.com/page")
            assert ua == settings.SCRAPING_USER_AGENT
        finally:
            settings.ENABLE_UA_ROTATION = original_setting
