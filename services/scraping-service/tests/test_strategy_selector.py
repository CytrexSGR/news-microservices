"""Tests for Strategy Selector"""
import pytest
from app.services.extraction.strategy_selector import StrategySelector, get_strategy_selector
from app.models.source_profile import ScrapeMethodEnum, PaywallTypeEnum, ScrapeStatusEnum


class TestStrategySelector:
    @pytest.fixture
    def selector(self):
        return StrategySelector()

    def test_select_for_unknown_source(self, selector):
        """Test selection for unknown source returns default"""
        config = {
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallback_methods": [ScrapeMethodEnum.TRAFILATURA],
            "requires_stealth": False,
            "paywall_type": PaywallTypeEnum.UNKNOWN
        }

        method = selector.select(config)
        assert method == ScrapeMethodEnum.NEWSPAPER4K

    def test_select_upgrades_to_stealth(self, selector):
        """Test stealth requirement upgrades to stealth variant"""
        config = {
            "method": ScrapeMethodEnum.PLAYWRIGHT,
            "fallback_methods": [],
            "requires_stealth": True,
            "paywall_type": PaywallTypeEnum.NONE
        }

        method = selector.select(config)
        assert method == ScrapeMethodEnum.PLAYWRIGHT_STEALTH

    def test_select_upgrades_newspaper_to_stealth(self, selector):
        """Test newspaper4k with stealth requirement upgrades to playwright_stealth"""
        config = {
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallback_methods": [],
            "requires_stealth": True,
            "paywall_type": PaywallTypeEnum.NONE
        }

        method = selector.select(config)
        assert method == ScrapeMethodEnum.PLAYWRIGHT_STEALTH

    def test_select_respects_hard_paywall(self, selector):
        """Test method is returned even with hard paywall (logging warning)"""
        config = {
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallback_methods": [],
            "requires_stealth": False,
            "paywall_type": PaywallTypeEnum.HARD
        }

        method = selector.select(config)
        assert method == ScrapeMethodEnum.NEWSPAPER4K  # Still returns method

    def test_get_fallback_chain(self, selector):
        """Test fallback chain generation"""
        config = {
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallback_methods": [ScrapeMethodEnum.TRAFILATURA, ScrapeMethodEnum.PLAYWRIGHT],
            "requires_stealth": False,
            "paywall_type": PaywallTypeEnum.NONE
        }

        chain = selector.get_fallback_chain(config)
        assert chain == [
            ScrapeMethodEnum.NEWSPAPER4K,
            ScrapeMethodEnum.TRAFILATURA,
            ScrapeMethodEnum.PLAYWRIGHT
        ]

    def test_get_fallback_chain_deduplicates(self, selector):
        """Test fallback chain removes duplicates"""
        config = {
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallback_methods": [
                ScrapeMethodEnum.NEWSPAPER4K,  # Duplicate
                ScrapeMethodEnum.TRAFILATURA
            ],
        }

        chain = selector.get_fallback_chain(config)
        assert chain == [
            ScrapeMethodEnum.NEWSPAPER4K,
            ScrapeMethodEnum.TRAFILATURA
        ]

    def test_get_fallback_chain_empty_fallbacks(self, selector):
        """Test fallback chain with no fallbacks"""
        config = {
            "method": ScrapeMethodEnum.PLAYWRIGHT,
            "fallback_methods": [],
        }

        chain = selector.get_fallback_chain(config)
        assert chain == [ScrapeMethodEnum.PLAYWRIGHT]

    def test_should_use_proxy(self, selector):
        """Test proxy requirement detection"""
        config_no_proxy = {"requires_proxy": False}
        config_proxy = {"requires_proxy": True}

        assert selector.should_use_proxy(config_no_proxy) is False
        assert selector.should_use_proxy(config_proxy) is True

    def test_get_rate_limit(self, selector):
        """Test rate limit retrieval"""
        config = {"rate_limit": 5}
        assert selector.get_rate_limit(config) == 5

        config_default = {}
        assert selector.get_rate_limit(config_default) == 10  # Default

    def test_get_method_capabilities(self, selector):
        """Test method capabilities retrieval"""
        caps = selector.get_method_capabilities(ScrapeMethodEnum.PLAYWRIGHT)

        assert caps["js_support"] is True
        assert caps["stealth"] is False
        assert caps["speed"] == "slow"

    def test_get_method_capabilities_stealth(self, selector):
        """Test stealth method capabilities"""
        caps = selector.get_method_capabilities(ScrapeMethodEnum.PLAYWRIGHT_STEALTH)

        assert caps["js_support"] is True
        assert caps["stealth"] is True

    def test_recommend_method_for_js_heavy(self, selector):
        """Test recommendation for JS-heavy site"""
        method = selector.recommend_method_for_site(is_js_heavy=True)
        assert method == ScrapeMethodEnum.PLAYWRIGHT

    def test_recommend_method_for_bot_protected(self, selector):
        """Test recommendation for bot-protected site"""
        method = selector.recommend_method_for_site(is_bot_protected=True)
        assert method == ScrapeMethodEnum.PLAYWRIGHT_STEALTH

    def test_recommend_method_for_structured_data(self, selector):
        """Test recommendation for site with structured data"""
        method = selector.recommend_method_for_site(has_structured_data=True)
        assert method == ScrapeMethodEnum.JSONLD

    def test_recommend_method_default(self, selector):
        """Test default recommendation"""
        method = selector.recommend_method_for_site()
        assert method == ScrapeMethodEnum.NEWSPAPER4K

    def test_recommend_method_paywall_with_structured(self, selector):
        """Test paywall overrides structured data preference"""
        method = selector.recommend_method_for_site(
            has_structured_data=True,
            has_paywall=True
        )
        # Should NOT use JSONLD because of paywall
        assert method == ScrapeMethodEnum.NEWSPAPER4K

    def test_singleton_instance(self):
        """Test singleton pattern"""
        sel1 = get_strategy_selector()
        sel2 = get_strategy_selector()
        assert sel1 is sel2
