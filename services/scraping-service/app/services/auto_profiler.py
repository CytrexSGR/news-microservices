"""
Auto-Profiler Service

Automatically determines the best scraping method for new domains.

When a new domain is encountered:
1. Quick-test with newspaper4k (fastest)
2. If fails: test trafilatura
3. If fails: test playwright (JS support)
4. If fails: test stealth (anti-detection)
5. Save best method to profile

Features:
- Parallel testing for speed
- Quality scoring to pick best result
- Paywall detection
- Automatic profile persistence
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from app.models.source_profile import (
    ScrapeMethodEnum,
    PaywallTypeEnum,
    SourceProfile,
    SourceProfileCreate,
)

logger = logging.getLogger(__name__)


@dataclass
class ProfileTestResult:
    """Result of testing a scraping method"""
    method: ScrapeMethodEnum
    success: bool
    word_count: int
    quality_score: float
    response_time_ms: int
    error: Optional[str] = None
    is_paywall: bool = False
    content_preview: Optional[str] = None


class AutoProfiler:
    """
    Automatically profiles new domains to find optimal scraping method.

    Tests methods in order of speed/resource usage:
    1. newspaper4k - Fast, no browser needed
    2. trafilatura - Alternative extractor
    3. playwright - Full browser for JS
    4. stealth - Anti-detection measures
    """

    # Minimum word count to consider a scrape successful
    MIN_WORD_COUNT = 50

    # Quality threshold to accept a method
    MIN_QUALITY_SCORE = 0.3

    # Paywall indicators
    PAYWALL_INDICATORS = [
        "subscribe to read",
        "subscription required",
        "premium content",
        "sign in to continue",
        "create an account",
        "become a member",
        "unlock this article",
        "already a subscriber",
        "paywall",
        "limited articles",
        "free articles remaining",
    ]

    def __init__(self):
        self._profiling_in_progress: Dict[str, asyncio.Event] = {}
        self._profiling_results: Dict[str, SourceProfile] = {}

    async def profile_domain(
        self,
        url: str,
        scraper: Any,  # ContentScraper instance
    ) -> SourceProfile:
        """
        Profile a domain to find the best scraping method.

        Args:
            url: URL to test (used to extract domain)
            scraper: ContentScraper instance for testing

        Returns:
            SourceProfile with optimal settings
        """
        domain = self._extract_domain(url)

        # Check if profiling already in progress for this domain
        if domain in self._profiling_in_progress:
            logger.info(f"Waiting for existing profiling of {domain}")
            await self._profiling_in_progress[domain].wait()
            return self._profiling_results.get(domain)

        # Start profiling
        event = asyncio.Event()
        self._profiling_in_progress[domain] = event

        try:
            logger.info(f"Starting auto-profiling for domain: {domain}")

            # Test each method
            results = await self._test_all_methods(url, scraper)

            # Analyze results and create profile
            profile = self._create_profile_from_results(domain, results)

            self._profiling_results[domain] = profile
            logger.info(
                f"Auto-profiling complete for {domain}: "
                f"method={profile.scrape_method.value}, "
                f"paywall={profile.paywall_type.value}"
            )

            return profile

        finally:
            event.set()
            del self._profiling_in_progress[domain]

    async def _test_all_methods(
        self,
        url: str,
        scraper: Any,
    ) -> List[ProfileTestResult]:
        """Test all scraping methods and return results."""
        results = []

        # Test methods in order (fastest first)
        methods_to_test = [
            (ScrapeMethodEnum.NEWSPAPER4K, self._test_newspaper4k),
            (ScrapeMethodEnum.TRAFILATURA, self._test_trafilatura),
            (ScrapeMethodEnum.PLAYWRIGHT, self._test_playwright),
            (ScrapeMethodEnum.PLAYWRIGHT_STEALTH, self._test_stealth),
        ]

        for method, test_func in methods_to_test:
            try:
                result = await test_func(url, scraper)
                results.append(result)

                # If we got a good result, we can skip heavier methods
                if result.success and result.word_count >= self.MIN_WORD_COUNT * 2:
                    if result.quality_score >= 0.7 and not result.is_paywall:
                        logger.info(
                            f"Method {method.value} works well, skipping remaining tests"
                        )
                        break

            except Exception as e:
                logger.warning(f"Error testing {method.value}: {e}")
                results.append(ProfileTestResult(
                    method=method,
                    success=False,
                    word_count=0,
                    quality_score=0.0,
                    response_time_ms=0,
                    error=str(e)
                ))

        return results

    async def _test_newspaper4k(
        self,
        url: str,
        scraper: Any,
    ) -> ProfileTestResult:
        """Test newspaper4k extraction."""
        import time
        start = time.perf_counter()

        try:
            result = await scraper._scrape_with_newspaper4k(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            is_paywall = self._detect_paywall(result.content or "")
            quality = self._calculate_quality(result.content, result.word_count)

            return ProfileTestResult(
                method=ScrapeMethodEnum.NEWSPAPER4K,
                success=result.content is not None and result.word_count >= self.MIN_WORD_COUNT,
                word_count=result.word_count,
                quality_score=quality,
                response_time_ms=elapsed_ms,
                is_paywall=is_paywall,
                content_preview=result.content[:200] if result.content else None,
            )
        except Exception as e:
            return ProfileTestResult(
                method=ScrapeMethodEnum.NEWSPAPER4K,
                success=False,
                word_count=0,
                quality_score=0.0,
                response_time_ms=int((time.perf_counter() - start) * 1000),
                error=str(e)
            )

    async def _test_trafilatura(
        self,
        url: str,
        scraper: Any,
    ) -> ProfileTestResult:
        """Test trafilatura extraction."""
        import time
        start = time.perf_counter()

        try:
            # Use the scraper's trafilatura method directly
            result = await scraper._scrape_with_trafilatura(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            is_paywall = self._detect_paywall(result.content or "")
            quality = self._calculate_quality(result.content, result.word_count)

            return ProfileTestResult(
                method=ScrapeMethodEnum.TRAFILATURA,
                success=result.content is not None and result.word_count >= self.MIN_WORD_COUNT,
                word_count=result.word_count,
                quality_score=quality,
                response_time_ms=elapsed_ms,
                is_paywall=is_paywall,
                content_preview=result.content[:200] if result.content else None,
            )
        except Exception as e:
            return ProfileTestResult(
                method=ScrapeMethodEnum.TRAFILATURA,
                success=False,
                word_count=0,
                quality_score=0.0,
                response_time_ms=int((time.perf_counter() - start) * 1000),
                error=str(e)
            )

    async def _test_playwright(
        self,
        url: str,
        scraper: Any,
    ) -> ProfileTestResult:
        """Test playwright extraction."""
        import time
        start = time.perf_counter()

        try:
            result = await scraper._scrape_with_playwright(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            is_paywall = self._detect_paywall(result.content or "")
            quality = self._calculate_quality(result.content, result.word_count)

            return ProfileTestResult(
                method=ScrapeMethodEnum.PLAYWRIGHT,
                success=result.content is not None and result.word_count >= self.MIN_WORD_COUNT,
                word_count=result.word_count,
                quality_score=quality,
                response_time_ms=elapsed_ms,
                is_paywall=is_paywall,
                content_preview=result.content[:200] if result.content else None,
            )
        except Exception as e:
            return ProfileTestResult(
                method=ScrapeMethodEnum.PLAYWRIGHT,
                success=False,
                word_count=0,
                quality_score=0.0,
                response_time_ms=int((time.perf_counter() - start) * 1000),
                error=str(e)
            )

    async def _test_stealth(
        self,
        url: str,
        scraper: Any,
    ) -> ProfileTestResult:
        """Test stealth extraction using playwright_stealth."""
        import time
        start = time.perf_counter()

        try:
            result = await scraper._scrape_with_playwright_stealth(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            is_paywall = self._detect_paywall(result.content or "")
            quality = self._calculate_quality(result.content, result.word_count)

            return ProfileTestResult(
                method=ScrapeMethodEnum.PLAYWRIGHT_STEALTH,
                success=result.content is not None and result.word_count >= self.MIN_WORD_COUNT,
                word_count=result.word_count,
                quality_score=quality,
                response_time_ms=elapsed_ms,
                is_paywall=is_paywall,
                content_preview=result.content[:200] if result.content else None,
            )
        except Exception as e:
            return ProfileTestResult(
                method=ScrapeMethodEnum.PLAYWRIGHT_STEALTH,
                success=False,
                word_count=0,
                quality_score=0.0,
                response_time_ms=int((time.perf_counter() - start) * 1000),
                error=str(e)
            )

    def _detect_paywall(self, content: str) -> bool:
        """Detect if content indicates a paywall."""
        if not content:
            return False

        content_lower = content.lower()

        # Check for paywall indicators
        for indicator in self.PAYWALL_INDICATORS:
            if indicator in content_lower:
                return True

        # Very short content might indicate paywall
        word_count = len(content.split())
        if word_count < 100 and word_count > 0:
            # Check ratio of paywall words
            paywall_word_count = sum(
                1 for indicator in self.PAYWALL_INDICATORS
                if indicator in content_lower
            )
            if paywall_word_count >= 2:
                return True

        return False

    def _calculate_quality(self, content: Optional[str], word_count: int) -> float:
        """Calculate content quality score (0-1)."""
        if not content or word_count == 0:
            return 0.0

        score = 0.0

        # Word count factor (more is better, up to a point)
        if word_count >= 500:
            score += 0.4
        elif word_count >= 200:
            score += 0.3
        elif word_count >= 100:
            score += 0.2
        elif word_count >= 50:
            score += 0.1

        # Paragraph structure (indicates proper extraction)
        paragraphs = content.count('\n\n')
        if paragraphs >= 5:
            score += 0.2
        elif paragraphs >= 2:
            score += 0.1

        # Sentence structure (periods followed by space and capital)
        import re
        sentences = len(re.findall(r'\. [A-Z]', content))
        if sentences >= 10:
            score += 0.2
        elif sentences >= 5:
            score += 0.1

        # No paywall indicators
        if not self._detect_paywall(content):
            score += 0.2

        return min(1.0, score)

    def _create_profile_from_results(
        self,
        domain: str,
        results: List[ProfileTestResult],
    ) -> SourceProfile:
        """Create a SourceProfile from test results."""

        # Filter successful results
        successful = [r for r in results if r.success and not r.is_paywall]

        if not successful:
            # Check if it's a paywall
            paywall_results = [r for r in results if r.is_paywall]
            if paywall_results:
                paywall_type = PaywallTypeEnum.HARD
            else:
                paywall_type = PaywallTypeEnum.UNKNOWN

            # No method works - use stealth as last resort
            return SourceProfile(
                id=0,
                domain=domain,
                scrape_method=ScrapeMethodEnum.PLAYWRIGHT_STEALTH,
                fallback_methods=[ScrapeMethodEnum.PLAYWRIGHT],
                paywall_type=paywall_type,
                requires_stealth=True,
                requires_ua_rotation=True,
                notes="Auto-profiled: no method succeeded",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Sort by quality and pick best
        successful.sort(key=lambda r: (r.quality_score, r.word_count), reverse=True)
        best = successful[0]

        # Build fallback chain (exclude best method)
        all_methods = [
            ScrapeMethodEnum.NEWSPAPER4K,
            ScrapeMethodEnum.TRAFILATURA,
            ScrapeMethodEnum.PLAYWRIGHT,
            ScrapeMethodEnum.PLAYWRIGHT_STEALTH,
        ]
        fallbacks = [m for m in all_methods if m != best.method]

        # Determine if stealth/JS is required
        requires_stealth = best.method == ScrapeMethodEnum.PLAYWRIGHT_STEALTH
        requires_js = best.method in [ScrapeMethodEnum.PLAYWRIGHT, ScrapeMethodEnum.PLAYWRIGHT_STEALTH]

        return SourceProfile(
            id=0,
            domain=domain,
            scrape_method=best.method,
            fallback_methods=fallbacks,
            paywall_type=PaywallTypeEnum.NONE,
            requires_stealth=requires_stealth,
            requires_ua_rotation=True,
            avg_word_count=best.word_count,
            avg_response_time_ms=best.response_time_ms,
            notes=f"Auto-profiled: best method={best.method.value}, quality={best.quality_score:.2f}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain


# Singleton instance
_auto_profiler: Optional[AutoProfiler] = None


def get_auto_profiler() -> AutoProfiler:
    """Get singleton AutoProfiler instance."""
    global _auto_profiler
    if _auto_profiler is None:
        _auto_profiler = AutoProfiler()
    return _auto_profiler
