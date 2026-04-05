"""
Integration tests for Phase 1 scraping enhancements.
"""
import pytest
from app.services.scraper import ContentScraper, ScrapeStatus
from app.core.user_agents import get_user_agent_pool
from app.core.retry import calculate_backoff_with_jitter, RetryConfig


class TestPhase1Integration:
    @pytest.fixture
    def scraper(self):
        """Create scraper instance (not started - for unit testing)"""
        return ContentScraper()

    def test_ua_pool_initialization(self):
        """Verify User-Agent pool initializes correctly"""
        pool = get_user_agent_pool()
        assert pool is not None

        ua = pool.get_random()
        assert isinstance(ua, str)
        assert len(ua) > 20

    def test_ua_rotation_consistency(self):
        """Verify same domain gets consistent UA"""
        pool = get_user_agent_pool()

        ua1 = pool.get_for_domain("site-a.com")
        ua2 = pool.get_for_domain("site-a.com")
        ua3 = pool.get_for_domain("site-b.com")

        # Same domain = same UA
        assert ua1 == ua2
        # Different domain = potentially different UA (but valid)
        assert isinstance(ua3, str)

    def test_jittered_backoff_produces_variety(self):
        """Verify jittered backoff produces varied delays"""
        config = RetryConfig(base_delay=1.0, max_delay=10.0)

        delays = [calculate_backoff_with_jitter(2, config) for _ in range(20)]

        # Should have variety
        unique_delays = set(delays)
        assert len(unique_delays) > 1

    def test_jittered_backoff_respects_bounds(self):
        """Verify jittered backoff stays within bounds"""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=2.0)

        for attempt in range(10):
            delay = calculate_backoff_with_jitter(attempt, config)
            # Should never exceed max_delay (with small buffer for float precision)
            assert delay <= config.max_delay + 0.01

    def test_trafilatura_extractor_available(self, scraper):
        """Verify trafilatura extractor can be imported"""
        from app.services.extraction.trafilatura_extractor import TrafilaturaExtractor

        extractor = TrafilaturaExtractor()
        # Should initialize without error
        assert extractor is not None
        # is_available may be True or False depending on installation
        assert isinstance(extractor.is_available, bool)

    def test_scraper_has_phase1_attributes(self, scraper):
        """Verify scraper has Phase 1 attributes"""
        assert hasattr(scraper, '_ua_pool')
        assert hasattr(scraper, '_trafilatura')
        assert hasattr(scraper, '_get_ua_for_url')

    def test_feature_flags_configurable(self):
        """Verify feature flags are configurable"""
        from app.core.config import settings

        assert hasattr(settings, 'ENABLE_UA_ROTATION')
        assert hasattr(settings, 'ENABLE_JITTERED_BACKOFF')
        assert hasattr(settings, 'ENABLE_TRAFILATURA_FALLBACK')

        # All should be enabled by default
        assert settings.ENABLE_UA_ROTATION is True
        assert settings.ENABLE_JITTERED_BACKOFF is True
        assert settings.ENABLE_TRAFILATURA_FALLBACK is True
