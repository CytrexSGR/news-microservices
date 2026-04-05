"""
Strategy Selector

Selects optimal scraping strategy based on source profile.
"""
import logging
from typing import List, Dict, Any

from app.models.source_profile import ScrapeMethodEnum, PaywallTypeEnum

logger = logging.getLogger(__name__)


class StrategySelector:
    """
    Selects scraping strategy based on source intelligence.

    Decision factors:
    - Historical success rate
    - Paywall type
    - JS requirements
    - Stealth requirements
    """

    # Method capabilities
    METHOD_CAPABILITIES = {
        ScrapeMethodEnum.NEWSPAPER4K: {
            "js_support": False,
            "stealth": False,
            "speed": "fast",
            "quality": "high"
        },
        ScrapeMethodEnum.TRAFILATURA: {
            "js_support": False,
            "stealth": False,
            "speed": "fast",
            "quality": "high"
        },
        ScrapeMethodEnum.HTTPX_BASIC: {
            "js_support": False,
            "stealth": False,
            "speed": "very_fast",
            "quality": "low"
        },
        ScrapeMethodEnum.PLAYWRIGHT: {
            "js_support": True,
            "stealth": False,
            "speed": "slow",
            "quality": "high"
        },
        ScrapeMethodEnum.PLAYWRIGHT_STEALTH: {
            "js_support": True,
            "stealth": True,
            "speed": "slow",
            "quality": "high"
        },
        ScrapeMethodEnum.JSONLD: {
            "js_support": False,
            "stealth": False,
            "speed": "very_fast",
            "quality": "structured"
        }
    }

    def select(self, config: Dict[str, Any]) -> ScrapeMethodEnum:
        """
        Select best scraping method based on config.

        Args:
            config: Source config from registry

        Returns:
            Selected scraping method
        """
        base_method = config.get("method", ScrapeMethodEnum.NEWSPAPER4K)
        requires_stealth = config.get("requires_stealth", False)
        paywall_type = config.get("paywall_type", PaywallTypeEnum.UNKNOWN)

        # Upgrade to stealth if required
        if requires_stealth:
            if base_method == ScrapeMethodEnum.PLAYWRIGHT:
                return ScrapeMethodEnum.PLAYWRIGHT_STEALTH
            elif base_method in [ScrapeMethodEnum.NEWSPAPER4K, ScrapeMethodEnum.TRAFILATURA]:
                # These don't have stealth variants, upgrade to playwright_stealth
                logger.info(f"Upgrading {base_method} to playwright_stealth due to stealth requirement")
                return ScrapeMethodEnum.PLAYWRIGHT_STEALTH

        # Hard paywall - try anyway but log warning
        if paywall_type == PaywallTypeEnum.HARD:
            logger.warning(f"Attempting scrape on hard paywall site with {base_method}")

        return base_method

    def get_fallback_chain(self, config: Dict[str, Any]) -> List[ScrapeMethodEnum]:
        """
        Get ordered list of methods to try.

        Returns primary method followed by fallbacks.
        """
        primary = config.get("method", ScrapeMethodEnum.NEWSPAPER4K)
        fallbacks = config.get("fallback_methods", [])

        chain = [primary]
        chain.extend(fallbacks)

        # Deduplicate while preserving order
        seen = set()
        return [m for m in chain if not (m in seen or seen.add(m))]

    def should_use_proxy(self, config: Dict[str, Any]) -> bool:
        """Determine if proxy should be used"""
        return config.get("requires_proxy", False)

    def get_rate_limit(self, config: Dict[str, Any]) -> int:
        """Get rate limit for this source"""
        return config.get("rate_limit", 10)

    def get_method_capabilities(self, method: ScrapeMethodEnum) -> Dict[str, Any]:
        """Get capabilities of a scraping method"""
        return self.METHOD_CAPABILITIES.get(method, {
            "js_support": False,
            "stealth": False,
            "speed": "unknown",
            "quality": "unknown"
        })

    def recommend_method_for_site(
        self,
        is_js_heavy: bool = False,
        has_paywall: bool = False,
        is_bot_protected: bool = False,
        has_structured_data: bool = False
    ) -> ScrapeMethodEnum:
        """
        Recommend best method based on site characteristics.

        Args:
            is_js_heavy: Site requires JavaScript rendering
            has_paywall: Site has paywall (any type)
            is_bot_protected: Site actively blocks bots
            has_structured_data: Site has JSON-LD structured data

        Returns:
            Recommended scraping method
        """
        # JSON-LD is fastest if available
        if has_structured_data and not has_paywall:
            return ScrapeMethodEnum.JSONLD

        # Bot protected sites need stealth
        if is_bot_protected:
            return ScrapeMethodEnum.PLAYWRIGHT_STEALTH

        # JS-heavy sites need Playwright
        if is_js_heavy:
            return ScrapeMethodEnum.PLAYWRIGHT

        # Default: newspaper4k is fast and high quality
        return ScrapeMethodEnum.NEWSPAPER4K


# Singleton instance
_selector_instance = None


def get_strategy_selector() -> StrategySelector:
    """Get singleton Strategy Selector instance"""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = StrategySelector()
    return _selector_instance
