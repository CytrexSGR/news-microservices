"""
User-Agent Pool for Scraping Service

Provides rotating User-Agent strings to reduce detection.
Uses fake-useragent library with fallback to static list.
"""
import logging
import hashlib
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Fallback User-Agents if fake-useragent fails
FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class UserAgentPool:
    """
    Manages User-Agent rotation for scraping requests.

    Features:
    - Random UA selection for general requests
    - Domain-consistent UA for session continuity
    - Fallback to static list if fake-useragent unavailable
    """

    def __init__(self):
        self._fake_ua = None
        self._domain_cache: Dict[str, str] = {}
        self._init_fake_useragent()

    def _init_fake_useragent(self):
        """Initialize fake-useragent with fallback"""
        try:
            from fake_useragent import UserAgent
            self._fake_ua = UserAgent(browsers=['chrome', 'firefox', 'safari', 'edge'])
            logger.info("fake-useragent initialized successfully")
        except Exception as e:
            logger.warning(f"fake-useragent unavailable, using fallback list: {e}")
            self._fake_ua = None

    def get_random(self) -> str:
        """Get a random User-Agent string"""
        if self._fake_ua:
            try:
                return self._fake_ua.random
            except Exception:
                pass

        # Fallback to static list
        import random
        return random.choice(FALLBACK_USER_AGENTS)

    def get_for_domain(self, domain: str) -> str:
        """
        Get consistent User-Agent for a domain.

        Same domain always gets same UA within session to appear
        as single user browsing the site.
        """
        if domain not in self._domain_cache:
            # Use domain hash to select UA deterministically
            hash_val = int(hashlib.md5(domain.encode()).hexdigest(), 16)
            if self._fake_ua:
                try:
                    # Seed selection based on domain
                    ua_list = [self._fake_ua.chrome, self._fake_ua.firefox, self._fake_ua.safari]
                    self._domain_cache[domain] = ua_list[hash_val % len(ua_list)]
                except Exception:
                    self._domain_cache[domain] = FALLBACK_USER_AGENTS[hash_val % len(FALLBACK_USER_AGENTS)]
            else:
                self._domain_cache[domain] = FALLBACK_USER_AGENTS[hash_val % len(FALLBACK_USER_AGENTS)]

        return self._domain_cache[domain]

    def clear_cache(self):
        """Clear domain-UA cache (for testing or session reset)"""
        self._domain_cache.clear()


# Singleton instance
_pool: Optional[UserAgentPool] = None


def get_user_agent_pool() -> UserAgentPool:
    """Get or create singleton UserAgentPool"""
    global _pool
    if _pool is None:
        _pool = UserAgentPool()
    return _pool
