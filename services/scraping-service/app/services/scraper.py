"""
Content Scraper Service

Implements multiple scraping strategies:
- newspaper4k: Fast, intelligent article extraction with NLP
- Playwright: Full browser for JavaScript-heavy sites
- Playwright-Stealth: Full browser with anti-detection measures
- trafilatura: Fallback content extractor

Features:
- Exponential backoff retry logic with jitter
- User-Agent rotation for anti-detection
- Proper browser context cleanup (memory leak fix)
- Rate limiting integration
- Fallback extraction chain (newspaper4k -> trafilatura)
- Source Registry integration (Phase 2: Intelligence)
- Intelligent method selection based on source profile
- Playwright-Stealth with fingerprint randomization (Phase 3: Anti-Detection)
- Human-like behavior simulation (mouse movements, scrolling)
"""
import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    Playwright
)
from newspaper import Article, ArticleException

from app.core.config import settings
from app.core.retry import retry_handler, RetryConfig
from app.core.user_agents import get_user_agent_pool
from app.services.extraction.trafilatura_extractor import TrafilaturaExtractor
from app.services.source_registry import get_source_registry, SourceRegistry
from app.services.extraction.strategy_selector import get_strategy_selector, StrategySelector
from app.models.source_profile import ScrapeMethodEnum, SourceProfileMetricsUpdate
from app.services.stealth import StealthBrowser, FingerprintGenerator
from app.services.stealth.playwright_stealth import get_stealth_browser
from app.services.stealth.fingerprint import get_fingerprint_generator
from app.services.dlq_handler import DLQHandler, get_dlq_handler
from app.services.auto_profiler import AutoProfiler, get_auto_profiler
from app.services.extraction.jsonld_extractor import JSONLDExtractor, get_jsonld_extractor
from app.models.dlq import DeadLetterCreate, FailureReasonEnum
from app.core.metrics import MetricsCollector, get_metrics_collector
from app.services.quality_scorer import ContentQualityScorer, get_quality_scorer
from app.services.proxy_manager import ProxyManager, get_proxy_manager
from app.services.http_cache import HTTPCache, get_http_cache, CacheEntry

logger = logging.getLogger(__name__)


class ScrapeStatus(str, Enum):
    """Scraping result status"""
    SUCCESS = "success"
    PAYWALL = "paywall"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"


@dataclass
class ScrapeResult:
    """Result of scraping operation"""
    content: Optional[str]
    word_count: int
    status: ScrapeStatus
    error_message: Optional[str] = None
    method_used: Optional[str] = None

    # Additional structured data (from newspaper4k)
    extracted_title: Optional[str] = None
    extracted_authors: Optional[List[str]] = None
    extracted_publish_date: Optional[Any] = None  # datetime
    extracted_metadata: Optional[Dict[str, Any]] = None
    extracted_links: Optional[List[Dict[str, Any]]] = None


class ContentScraper:
    """
    Multi-strategy content scraper.

    Supports httpx (fast) and Playwright (JavaScript support).

    Features:
    - Proper browser lifecycle management (fixes memory leak)
    - Exponential backoff retry logic with jitter
    - Rate limiting integration
    - User-Agent rotation
    - Trafilatura fallback extraction
    - Source Registry integration (Phase 2: Intelligence)
    - Intelligent method selection via Strategy Selector
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.browser_context: Optional[BrowserContext] = None
        self.playwright: Optional[Playwright] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self._browser_lock = None  # Will be initialized in start()
        self._ua_pool = None       # User-Agent pool
        self._trafilatura = None   # Trafilatura extractor
        self._source_registry: Optional[SourceRegistry] = None  # Phase 2: Intelligence
        self._strategy_selector: Optional[StrategySelector] = None  # Phase 2: Intelligence
        self._stealth_browser: Optional[StealthBrowser] = None  # Phase 3: Anti-Detection
        self._fingerprint_generator: Optional[FingerprintGenerator] = None  # Phase 3: Anti-Detection
        self._dlq_handler: Optional[DLQHandler] = None  # Phase 4: Robustness
        self._jsonld_extractor: Optional[JSONLDExtractor] = None  # Phase 4: Robustness
        self._metrics_collector: Optional[MetricsCollector] = None  # Phase 5: Observability
        self._quality_scorer: Optional[ContentQualityScorer] = None  # Phase 5: Observability
        self._proxy_manager: Optional[ProxyManager] = None  # Phase 6: Scale
        self._http_cache: Optional[HTTPCache] = None  # Phase 6: Scale
        self._auto_profiler: Optional[AutoProfiler] = None  # Phase 7: Auto-Profiling

    async def start(self):
        """Initialize scraper resources"""
        import asyncio
        self._browser_lock = asyncio.Lock()

        # Initialize User-Agent pool for rotation
        if settings.ENABLE_UA_ROTATION:
            self._ua_pool = get_user_agent_pool()
            logger.info("User-Agent rotation enabled")

        # Initialize trafilatura extractor for fallback
        if settings.ENABLE_TRAFILATURA_FALLBACK:
            self._trafilatura = TrafilaturaExtractor()
            logger.info(f"Trafilatura fallback {'enabled' if self._trafilatura.is_available else 'unavailable'}")

        # Initialize HTTP client WITHOUT static User-Agent
        # UA will be set per-request based on domain
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.SCRAPING_TIMEOUT),
            follow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )

        # Phase 2: Initialize Source Registry and Strategy Selector
        if settings.ENABLE_SOURCE_REGISTRY:
            self._source_registry = get_source_registry()
            self._strategy_selector = get_strategy_selector()
            logger.info("Source Registry and Strategy Selector enabled")

        # Phase 3: Initialize Stealth Browser and Fingerprint Generator
        self._stealth_browser = get_stealth_browser()
        self._fingerprint_generator = get_fingerprint_generator()
        logger.info(f"Stealth mode initialized (playwright-stealth available: {self._stealth_browser._stealth_available})")

        # Phase 4: Initialize DLQ Handler and JSON-LD Extractor
        self._dlq_handler = get_dlq_handler()
        self._jsonld_extractor = get_jsonld_extractor()
        logger.info("DLQ Handler and JSON-LD Extractor initialized")

        # Phase 5: Initialize Metrics Collector and Quality Scorer
        self._metrics_collector = get_metrics_collector()
        self._quality_scorer = get_quality_scorer()
        logger.info("Metrics Collector and Quality Scorer initialized")

        # Phase 6: Initialize Proxy Manager and HTTP Cache
        if settings.ENABLE_PROXY_ROTATION:
            self._proxy_manager = get_proxy_manager()
            logger.info(f"Proxy Manager enabled (rotation: {self._proxy_manager.config.enabled})")

        if settings.ENABLE_HTTP_CACHE:
            self._http_cache = get_http_cache()
            logger.info("HTTP Cache enabled")

        # Phase 7: Initialize Auto-Profiler
        if settings.ENABLE_AUTO_PROFILING and settings.ENABLE_SOURCE_REGISTRY:
            self._auto_profiler = get_auto_profiler()
            logger.info("Auto-Profiler enabled for new domain detection")

        logger.info("Content scraper initialized with Phase 1-7 enhancements")

    def _get_ua_for_url(self, url: str) -> str:
        """Get domain-consistent User-Agent for URL"""
        if settings.ENABLE_UA_ROTATION and self._ua_pool:
            domain = urlparse(url).netloc
            return self._ua_pool.get_for_domain(domain)
        return settings.SCRAPING_USER_AGENT

    async def stop(self):
        """Cleanup scraper resources"""
        if self.http_client:
            await self.http_client.aclose()

        # Properly cleanup browser resources (fixes memory leak)
        if self.browser_context:
            await self.browser_context.close()
            logger.debug("Browser context closed")

        if self.browser:
            await self.browser.close()
            logger.debug("Browser closed")

        if self.playwright:
            await self.playwright.stop()
            logger.debug("Playwright stopped")

        logger.info("✅ Content scraper stopped")

    async def scrape(self, url: str, method: str = "auto", skip_cache: bool = False, extract_links: bool = False) -> ScrapeResult:
        """
        Scrape content from URL with retry logic and intelligent method selection.

        Args:
            url: URL to scrape
            method: Scraping method. Use 'auto' for intelligent selection based on
                    Source Registry profile. Other values: 'newspaper4k', 'playwright'
            skip_cache: If True, bypass HTTP cache (Phase 6)

        Returns:
            ScrapeResult with content and metadata
        """
        start_time = time.time()
        domain = urlparse(url).netloc

        # Phase 6: Check HTTP cache first
        if not skip_cache and not extract_links and self._http_cache:
            cached = self._http_cache.get(url)
            if cached:
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"📦 Cache HIT: url={url}, "
                    f"duration={duration_ms:.0f}ms, "
                    f"words={cached.word_count}, "
                    f"hits={cached.hit_count}"
                )
                # Record cache hit in metrics
                if self._metrics_collector:
                    self._metrics_collector.record_scrape(
                        method="cache",
                        status="success",
                        domain=domain,
                        duration_seconds=duration_ms / 1000,
                        content_size=cached.size_bytes,
                        word_count=cached.word_count
                    )
                return ScrapeResult(
                    content=cached.content,
                    word_count=cached.word_count,
                    status=ScrapeStatus.SUCCESS,
                    method_used="cache",
                    extracted_metadata=cached.metadata
                )

        # Phase 7: Auto-profile new domains before method selection
        if method == "auto" and self._auto_profiler and self._source_registry:
            if self._source_registry.needs_profiling(url):
                try:
                    logger.info(f"🔍 Auto-profiling new domain: {domain}")
                    profile = await self._auto_profiler.profile_domain(url, self)
                    await self._source_registry.apply_profile(profile)
                    logger.info(
                        f"✅ Auto-profile complete: domain={domain}, "
                        f"method={profile.scrape_method.value}, "
                        f"paywall={profile.paywall_type.value}"
                    )
                except Exception as e:
                    logger.warning(f"Auto-profiling failed for {domain}: {e}")

        # Phase 2: Intelligent method selection
        selected_method = method
        source_config = None

        if method == "auto" and self._source_registry and self._strategy_selector:
            source_config = self._source_registry.get_scrape_config(url)
            selected_method = self._strategy_selector.select(source_config).value
            logger.info(f"🧠 Intelligent selection: url={url}, method={selected_method}")
        elif method == "auto":
            selected_method = "newspaper4k"  # Default fallback

        logger.info(f"🚀 Starting scrape: url={url}, method={selected_method}")

        try:
            # Use retry handler for all scraping methods
            retry_config = RetryConfig(
                max_retries=settings.SCRAPING_MAX_RETRIES,
                base_delay=1.0,
                max_delay=4.0,
                exponential_base=2.0
            )

            if selected_method == "newspaper4k":
                result = await retry_handler.execute_with_retry(
                    func=self._scrape_with_newspaper4k,
                    args=(url,),
                    config=retry_config,
                    context=f"newspaper4k scrape {url}"
                )
            elif selected_method == "playwright":
                result = await retry_handler.execute_with_retry(
                    func=self._scrape_with_playwright,
                    args=(url,),
                    config=retry_config,
                    context=f"playwright scrape {url}"
                )
            elif selected_method == "trafilatura":
                result = await self._scrape_with_trafilatura(url)
            elif selected_method == "playwright_stealth":
                result = await retry_handler.execute_with_retry(
                    func=self._scrape_with_playwright_stealth,
                    args=(url,),
                    config=retry_config,
                    context=f"playwright_stealth scrape {url}"
                )
            else:
                result = ScrapeResult(
                    content=None,
                    word_count=0,
                    status=ScrapeStatus.ERROR,
                    error_message=f"Invalid scraping method: {selected_method}. Use 'auto', 'newspaper4k', 'playwright', or 'playwright_stealth'."
                )

            # Performance logging
            duration_ms = (time.time() - start_time) * 1000
            duration_seconds = duration_ms / 1000
            content_size = len(result.content) if result.content else 0
            domain = urlparse(url).netloc
            logger.info(
                f"📊 Scrape complete: url={url}, "
                f"status={result.status.value}, "
                f"method={result.method_used or selected_method}, "
                f"duration={duration_ms:.0f}ms, "
                f"words={result.word_count}, "
                f"bytes={content_size}"
            )

            # Phase 2: Update Source Registry metrics
            if self._source_registry:
                await self._update_source_metrics(url, result, int(duration_ms))

            # Phase 5: Record Prometheus metrics
            if self._metrics_collector:
                self._metrics_collector.record_scrape(
                    method=result.method_used or selected_method,
                    status=result.status.value,
                    domain=domain,
                    duration_seconds=duration_seconds,
                    content_size=content_size,
                    word_count=result.word_count
                )

                # Calculate and record quality score if successful
                if result.status == ScrapeStatus.SUCCESS and result.content:
                    quality_score = self._calculate_quality_score(result, url)
                    if quality_score is not None:
                        self._metrics_collector.record_quality_score(domain, quality_score)
                        logger.debug(f"📈 Quality score for {domain}: {quality_score:.3f}")

            # Phase 6: Cache successful results
            if result.status == ScrapeStatus.SUCCESS and result.content and self._http_cache:
                try:
                    # Build metadata for cache
                    cache_metadata = result.extracted_metadata or {}
                    if result.extracted_title:
                        cache_metadata["title"] = result.extracted_title
                    if result.extracted_authors:
                        cache_metadata["authors"] = result.extracted_authors

                    self._http_cache.set(
                        url=url,
                        content=result.content,
                        word_count=result.word_count,
                        method=result.method_used or selected_method,
                        status="success",
                        metadata=cache_metadata
                    )
                    logger.debug(f"📦 Cached: url={url}, words={result.word_count}")
                except Exception as cache_error:
                    logger.warning(f"Failed to cache {url}: {cache_error}")

            # Link extraction if requested
            if extract_links and result.status == ScrapeStatus.SUCCESS:
                raw = getattr(self, "_last_raw_html", None)
                if raw:
                    try:
                        from app.services.link_extractor import extract_links as do_extract_links
                        links = do_extract_links(raw, url)
                        result.extracted_links = [
                            {"url": l.url, "anchor_text": l.anchor_text, "context": l.context,
                             "is_internal": l.is_internal, "position": l.position, "is_document": l.is_document}
                            for l in links
                        ]
                    except Exception as e:
                        logger.warning(f"Link extraction failed for {url}: {e}")

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            duration_seconds = duration_ms / 1000
            domain = urlparse(url).netloc
            logger.error(
                f"❌ Scrape failed: url={url}, method={selected_method}, "
                f"duration={duration_ms:.0f}ms, error={str(e)}"
            )

            # Phase 2: Update metrics on failure
            if self._source_registry:
                await self._update_source_metrics(
                    url,
                    ScrapeResult(
                        content=None,
                        word_count=0,
                        status=ScrapeStatus.ERROR,
                        error_message=str(e),
                        method_used=selected_method
                    ),
                    int(duration_ms)
                )

            # Phase 4: Add to Dead Letter Queue
            await self._add_to_dlq(url, e, selected_method)

            # Phase 5: Record failure metrics
            if self._metrics_collector:
                self._metrics_collector.record_scrape(
                    method=selected_method,
                    status="error",
                    domain=domain,
                    duration_seconds=duration_seconds
                )

            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used=selected_method
            )

    async def _update_source_metrics(self, url: str, result: ScrapeResult, response_time_ms: int):
        """Update Source Registry with scrape result metrics"""
        try:
            method_str = result.method_used or "newspaper4k"
            # Map string method to enum
            method_enum = ScrapeMethodEnum.NEWSPAPER4K
            if "trafilatura" in method_str:
                method_enum = ScrapeMethodEnum.TRAFILATURA
            elif method_str == "playwright_stealth":
                method_enum = ScrapeMethodEnum.PLAYWRIGHT_STEALTH
            elif method_str == "playwright":
                method_enum = ScrapeMethodEnum.PLAYWRIGHT

            metrics = SourceProfileMetricsUpdate(
                success=result.status == ScrapeStatus.SUCCESS,
                response_time_ms=response_time_ms,
                word_count=result.word_count,
                extraction_quality=min(1.0, result.word_count / 1000) if result.word_count > 0 else 0.0,
                method_used=method_enum,
                error_message=result.error_message
            )
            await self._source_registry.update_metrics(url, metrics)
        except Exception as e:
            logger.warning(f"Failed to update source metrics for {url}: {e}")

    def _calculate_quality_score(self, result: ScrapeResult, url: str) -> Optional[float]:
        """
        Calculate content quality score using the Quality Scorer.

        Phase 5: Observability

        Args:
            result: ScrapeResult with content
            url: Original URL (for logging)

        Returns:
            Quality score (0-1) or None if scoring fails
        """
        if not self._quality_scorer or not result.content:
            return None

        try:
            # Build metadata from extracted fields
            metadata = {}
            if result.extracted_title:
                metadata["title"] = result.extracted_title
            if result.extracted_authors:
                metadata["author"] = result.extracted_authors[0] if result.extracted_authors else None
            if result.extracted_publish_date:
                metadata["publish_date"] = str(result.extracted_publish_date)
            if result.extracted_metadata:
                # Merge additional metadata
                for key in ["description", "image", "top_image"]:
                    if key in result.extracted_metadata:
                        metadata[key] = result.extracted_metadata[key]

            # Score the content
            score_result = self._quality_scorer.score_content(
                content=result.content,
                metadata=metadata if metadata else None
            )

            # Log quality category
            category = self._quality_scorer.get_quality_category(score_result.overall_score)
            logger.debug(
                f"Quality assessment for {url}: "
                f"score={score_result.overall_score:.3f}, "
                f"category={category}, "
                f"word_count={score_result.details.get('word_count', 0)}"
            )

            return score_result.overall_score

        except Exception as e:
            logger.warning(f"Quality scoring failed for {url}: {e}")
            return None

    async def _scrape_with_trafilatura(self, url: str) -> ScrapeResult:
        """Scrape using trafilatura directly"""
        if not self._trafilatura or not self._trafilatura.is_available:
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message="Trafilatura not available",
                method_used="trafilatura"
            )

        try:
            response = await self.http_client.get(
                url,
                headers={"User-Agent": self._get_ua_for_url(url)}
            )
            response.raise_for_status()

            self._last_raw_html = response.text
            result = self._trafilatura.extract(
                response.text,
                url,
                min_word_count=settings.TRAFILATURA_MIN_WORD_COUNT
            )

            return ScrapeResult(
                content=result.content,
                word_count=result.word_count,
                status=ScrapeStatus.SUCCESS if result.status.value == "success" else ScrapeStatus.ERROR,
                method_used="trafilatura",
                extracted_title=result.extracted_title,
                extracted_authors=result.extracted_authors,
                extracted_publish_date=result.extracted_publish_date,
                extracted_metadata=result.extracted_metadata
            )

        except Exception as e:
            logger.error(f"Trafilatura error for {url}: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used="trafilatura"
            )

    async def _scrape_with_newspaper4k(self, url: str) -> ScrapeResult:
        """
        Scrape using newspaper4k with trafilatura fallback.

        Newspaper4k automatically handles:
        - Cookie banners (ignores non-content)
        - Article text extraction
        - Author detection
        - Image extraction
        - Publish date parsing

        If newspaper4k extraction is insufficient, falls back to trafilatura.
        """
        try:
            # Create Article object
            article = Article(url)

            # Set dynamic User-Agent for this request
            article.config.browser_user_agent = self._get_ua_for_url(url)

            # Download HTML (with timeout)
            article.download()

            # Parse article (NLP extraction)
            article.parse()

            # Store raw HTML for link extraction
            self._last_raw_html = getattr(article, "html", None) or ""

            # Extract text content
            text_content = article.text

            # Check minimum content length - try trafilatura fallback if insufficient
            if not text_content or len(text_content.split()) < settings.NEWSPAPER4K_MIN_WORD_COUNT:
                # Try trafilatura fallback if enabled
                if settings.ENABLE_TRAFILATURA_FALLBACK and self._trafilatura and self._trafilatura.is_available:
                    logger.info(f"newspaper4k extraction insufficient ({len(text_content.split()) if text_content else 0} words), trying trafilatura for {url}")

                    # Download HTML for trafilatura
                    try:
                        response = await self.http_client.get(
                            url,
                            headers={"User-Agent": self._get_ua_for_url(url)}
                        )
                        response.raise_for_status()

                        trafilatura_result = self._trafilatura.extract(
                            response.text,
                            url,
                            min_word_count=settings.TRAFILATURA_MIN_WORD_COUNT
                        )

                        if trafilatura_result.status.value == "success":
                            # Convert to our ScrapeResult type
                            return ScrapeResult(
                                content=trafilatura_result.content,
                                word_count=trafilatura_result.word_count,
                                status=ScrapeStatus.SUCCESS,
                                method_used="newspaper4k+trafilatura",
                                extracted_title=trafilatura_result.extracted_title,
                                extracted_authors=trafilatura_result.extracted_authors,
                                extracted_publish_date=trafilatura_result.extracted_publish_date,
                                extracted_metadata=trafilatura_result.extracted_metadata
                            )
                    except Exception as e:
                        logger.warning(f"Trafilatura fallback failed for {url}: {e}")

                # Both extractors failed or trafilatura not available
                return ScrapeResult(
                    content=text_content,
                    word_count=len(text_content.split()) if text_content else 0,
                    status=ScrapeStatus.ERROR,
                    error_message=f"Extracted content too short (< {settings.NEWSPAPER4K_MIN_WORD_COUNT} words)",
                    method_used="newspaper4k"
                )

            # Build metadata dictionary
            metadata = {
                "method": "newspaper4k",
                "top_image": article.top_image if article.top_image else None,
                "images": list(article.images) if article.images else [],
                "movies": article.movies if article.movies else [],
                "extracted_title": article.title if article.title else None,
                "extracted_authors": article.authors if article.authors else [],
                "extracted_publish_date": article.publish_date.isoformat() if article.publish_date else None,
            }

            word_count = len(text_content.split())

            return ScrapeResult(
                content=text_content,
                word_count=word_count,
                status=ScrapeStatus.SUCCESS,
                method_used="newspaper4k",
                extracted_title=article.title,
                extracted_authors=article.authors,
                extracted_publish_date=article.publish_date,
                extracted_metadata=metadata
            )

        except ArticleException as e:
            logger.error(f"Newspaper4k ArticleException for {url}: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=f"Article extraction failed: {str(e)}",
                method_used="newspaper4k"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                return ScrapeResult(
                    content=None,
                    word_count=0,
                    status=ScrapeStatus.BLOCKED,
                    error_message="Access blocked (403)",
                    method_used="newspaper4k"
                )
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=f"HTTP error: {e.response.status_code}",
                method_used="newspaper4k"
            )
        except Exception as e:
            logger.error(f"Error scraping {url} with newspaper4k: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used="newspaper4k"
            )

    async def _scrape_with_httpx(self, url: str) -> ScrapeResult:
        """Scrape using httpx (fast, no JavaScript)"""
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()

            # Store raw HTML for link extraction
            self._last_raw_html = response.text

            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract main content
            content = self._extract_content(soup)

            # Check for paywall indicators
            if self._is_paywall(soup, content):
                return ScrapeResult(
                    content=content,
                    word_count=len(content.split()),
                    status=ScrapeStatus.PAYWALL,
                    method_used="httpx"
                )

            word_count = len(content.split())

            return ScrapeResult(
                content=content,
                word_count=word_count,
                status=ScrapeStatus.SUCCESS,
                method_used="httpx"
            )

        except httpx.TimeoutException:
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.TIMEOUT,
                error_message="Request timeout",
                method_used="httpx"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                return ScrapeResult(
                    content=None,
                    word_count=0,
                    status=ScrapeStatus.BLOCKED,
                    error_message="Access blocked (403)",
                    method_used="httpx"
                )
            raise

    async def _scrape_with_playwright(self, url: str) -> ScrapeResult:
        """
        Scrape using Playwright (JavaScript support).

        MEMORY LEAK FIX:
        - Create new browser context for each scrape (isolated sessions)
        - Always close context after use
        - Prevents memory accumulation from cookies, cache, sessions
        """
        context = None
        page = None

        try:
            # Initialize browser if needed (thread-safe)
            async with self._browser_lock:
                if not self.browser:
                    self.playwright = await async_playwright().start()
                    self.browser = await self.playwright.chromium.launch(
                        headless=settings.PLAYWRIGHT_HEADLESS,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',  # Prevents /dev/shm memory issues
                            '--disable-gpu',
                            '--disable-software-rasterizer',
                        ]
                    )
                    logger.info("✅ Playwright browser launched")

            # Create new context for this scrape (MEMORY LEAK FIX)
            # Each context is isolated and cleaned up properly
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                # Use dynamic User-Agent from pool for better anti-detection
                user_agent=self._get_ua_for_url(url)
            )

            # Create new page in this context
            page = await context.new_page()

            # Navigate to URL
            await page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT)

            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Get page content
            html = await page.content()
            self._last_raw_html = html
            soup = BeautifulSoup(html, 'lxml')

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract main content
            content = self._extract_content(soup)

            # Check for paywall
            if self._is_paywall(soup, content):
                return ScrapeResult(
                    content=content,
                    word_count=len(content.split()),
                    status=ScrapeStatus.PAYWALL,
                    method_used="playwright"
                )

            word_count = len(content.split())

            return ScrapeResult(
                content=content,
                word_count=word_count,
                status=ScrapeStatus.SUCCESS,
                method_used="playwright"
            )

        except PlaywrightTimeout:
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.TIMEOUT,
                error_message="Page load timeout",
                method_used="playwright"
            )
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used="playwright"
            )
        finally:
            # CRITICAL: Always close page and context to prevent memory leak
            if page:
                await page.close()
            if context:
                await context.close()
                logger.debug("Browser context closed (memory leak prevention)")

    async def _scrape_with_playwright_stealth(self, url: str) -> ScrapeResult:
        """
        Scrape using Playwright with stealth anti-detection measures.

        Phase 3: Anti-Detection

        Applies:
        - playwright-stealth patches
        - Fingerprint randomization
        - Human-like behavior simulation
        - Random viewports, timezones, locales
        """
        context = None
        page = None

        try:
            # Get domain for consistent fingerprint
            domain = urlparse(url).netloc

            # Generate fingerprint for this domain
            fingerprint = self._fingerprint_generator.generate_for_domain(domain)
            logger.debug(f"Using fingerprint for {domain}: UA={fingerprint['user_agent'][:50]}...")

            # Initialize browser if needed (thread-safe)
            async with self._browser_lock:
                if not self.browser:
                    # Use fingerprint-aware browser args
                    browser_args = [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                        '--disable-blink-features=AutomationControlled',
                    ]
                    browser_args.extend(self._fingerprint_generator.get_browser_args(fingerprint))

                    self.playwright = await async_playwright().start()
                    self.browser = await self.playwright.chromium.launch(
                        headless=settings.PLAYWRIGHT_HEADLESS,
                        args=browser_args
                    )
                    logger.info("✅ Playwright stealth browser launched")

            # Create stealth context with fingerprint
            context_options = self._fingerprint_generator.get_context_options(fingerprint)
            context_options["user_agent"] = fingerprint["user_agent"]

            context = await self.browser.new_context(**context_options)

            # Create stealth page
            page = await self._stealth_browser.create_stealth_page(context)

            # Apply fingerprint scripts
            for script in self._fingerprint_generator.get_page_scripts(fingerprint):
                await page.add_init_script(script)

            # Navigate to URL
            await page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT)

            # Simulate human behavior before extracting content
            await self._stealth_browser.simulate_mouse_movement(page)
            await self._stealth_browser.simulate_human_scroll(page, scroll_amount=300)

            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Get page content
            html = await page.content()
            self._last_raw_html = html
            soup = BeautifulSoup(html, 'lxml')

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract main content
            content = self._extract_content(soup)

            # Check for paywall
            if self._is_paywall(soup, content):
                return ScrapeResult(
                    content=content,
                    word_count=len(content.split()),
                    status=ScrapeStatus.PAYWALL,
                    method_used="playwright_stealth"
                )

            word_count = len(content.split())

            return ScrapeResult(
                content=content,
                word_count=word_count,
                status=ScrapeStatus.SUCCESS,
                method_used="playwright_stealth"
            )

        except PlaywrightTimeout:
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.TIMEOUT,
                error_message="Page load timeout",
                method_used="playwright_stealth"
            )
        except Exception as e:
            logger.error(f"Playwright stealth error for {url}: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used="playwright_stealth"
            )
        finally:
            # CRITICAL: Always close page and context to prevent memory leak
            if page:
                await page.close()
            if context:
                await context.close()
                logger.debug("Stealth browser context closed (memory leak prevention)")

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from parsed HTML"""
        # Try common article selectors
        selectors = [
            "article",
            '[role="main"]',
            ".article-content",
            ".post-content",
            ".entry-content",
            "main",
            "#content"
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)

        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        return '\n\n'.join(p.get_text(strip=True) for p in paragraphs)

    def _is_paywall(self, soup: BeautifulSoup, content: str) -> bool:
        """Detect paywall indicators"""
        paywall_indicators = [
            "subscribe",
            "subscription",
            "paywall",
            "premium content",
            "member exclusive",
            "subscribers only"
        ]

        # Check for paywall keywords in HTML
        html_text = soup.get_text().lower()
        for indicator in paywall_indicators:
            if indicator in html_text and len(content.split()) < 200:
                return True

        return False

    # Phase 4: Robustness Methods

    async def _add_to_dlq(
        self,
        url: str,
        error: Exception,
        method: str
    ) -> None:
        """
        Add failed scrape to Dead Letter Queue.

        Args:
            url: Failed URL
            error: Exception that occurred
            method: Scraping method that was used
        """
        if not self._dlq_handler:
            return

        try:
            # Classify failure reason
            failure_reason = self._classify_failure(error)

            create_data = DeadLetterCreate(
                url=url,
                failure_reason=failure_reason,
                error_message=str(error),
                error_details={
                    "exception_type": type(error).__name__,
                    "method_used": method,
                },
                original_payload={
                    "method": method,
                }
            )

            entry = await self._dlq_handler.add_entry(create_data)
            logger.info(
                f"📥 Added to DLQ: url={url}, reason={failure_reason.value}, "
                f"retry_count={entry.retry_count}"
            )
        except Exception as e:
            logger.warning(f"Failed to add to DLQ: {e}")

    def _classify_failure(self, error: Exception) -> FailureReasonEnum:
        """Classify exception into DLQ failure reason"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        if "timeout" in error_type or "timeout" in error_str:
            return FailureReasonEnum.TIMEOUT
        elif "403" in error_str or "blocked" in error_str or "forbidden" in error_str:
            return FailureReasonEnum.BLOCKED
        elif "paywall" in error_str or "subscription" in error_str:
            return FailureReasonEnum.PAYWALL
        elif "429" in error_str or "rate limit" in error_str or "too many" in error_str:
            return FailureReasonEnum.RATE_LIMITED
        elif "connection" in error_type or "connection" in error_str:
            return FailureReasonEnum.CONNECTION_ERROR
        elif "extract" in error_str or "parse" in error_str:
            return FailureReasonEnum.EXTRACTION_FAILED
        elif "invalid" in error_str or "malformed" in error_str:
            return FailureReasonEnum.INVALID_CONTENT
        else:
            return FailureReasonEnum.UNKNOWN

    def extract_jsonld(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD article metadata from HTML.

        Args:
            html: HTML content

        Returns:
            Extracted JSON-LD metadata or None
        """
        if not self._jsonld_extractor:
            return None

        try:
            return self._jsonld_extractor.extract(html)
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
            return None

    async def get_dlq_stats(self) -> Optional[Dict[str, Any]]:
        """Get Dead Letter Queue statistics"""
        if not self._dlq_handler:
            return None
        return await self._dlq_handler.get_stats()

    async def get_dlq_pending(
        self,
        limit: int = 100,
        domain: Optional[str] = None
    ) -> List[Any]:
        """Get pending DLQ entries ready for retry"""
        if not self._dlq_handler:
            return []
        return await self._dlq_handler.get_pending_entries(limit, domain)


# Global scraper instance
scraper = ContentScraper()
