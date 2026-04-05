"""
Playwright Stealth Integration

Applies anti-detection patches to Playwright browser contexts.
"""
import logging
import random
from typing import Optional
from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

# Common viewport sizes (realistic desktop resolutions)
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 2560, "height": 1440},
]

# Common timezone IDs
TIMEZONES = [
    "Europe/Berlin",
    "Europe/London",
    "Europe/Paris",
    "America/New_York",
    "America/Los_Angeles",
]

# Common locales
LOCALES = ["de-DE", "en-US", "en-GB", "fr-FR"]


class StealthBrowser:
    """
    Stealth browser wrapper for anti-detection.

    Applies various patches to avoid headless detection:
    - playwright-stealth patches
    - Random viewport sizes
    - Realistic browser fingerprint
    - Human-like behavior simulation
    """

    def __init__(self):
        self._stealth_available = self._check_stealth_available()
        self._stealth_instance = None
        if self._stealth_available:
            self._stealth_instance = self._create_stealth_instance()

    def _check_stealth_available(self) -> bool:
        """Check if playwright-stealth is available (new API)"""
        try:
            from playwright_stealth import Stealth
            return True
        except ImportError:
            logger.warning("playwright-stealth not available, using basic evasion")
            return False

    def _create_stealth_instance(self):
        """Create Stealth instance with optimal settings"""
        try:
            from playwright_stealth import Stealth
            return Stealth(
                navigator_webdriver=True,  # Hide webdriver flag
                chrome_runtime=False,      # Don't modify chrome.runtime
            )
        except Exception as e:
            logger.warning(f"Failed to create Stealth instance: {e}")
            return None

    async def create_stealth_context(
        self,
        browser: Browser,
        timezone: Optional[str] = None,
        locale: Optional[str] = None
    ) -> BrowserContext:
        """
        Create a stealth browser context.

        Args:
            browser: Playwright browser instance
            timezone: Optional timezone override
            locale: Optional locale override

        Returns:
            Stealthy browser context
        """
        viewport = self._get_random_viewport()
        tz = timezone or random.choice(TIMEZONES)
        loc = locale or random.choice(LOCALES)

        context = await browser.new_context(
            viewport=viewport,
            locale=loc,
            timezone_id=tz,
            # Realistic browser settings
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            # Avoid common detection vectors
            extra_http_headers={
                "Accept-Language": f"{loc[:2]},{loc[:2].lower()};q=0.9,en;q=0.8",
            }
        )

        # Apply stealth patches
        await self._apply_stealth(context)

        logger.debug(f"Created stealth context: viewport={viewport}, timezone={tz}, locale={loc}")
        return context

    async def _apply_stealth(self, context: BrowserContext):
        """Apply stealth patches to context"""
        if self._stealth_available and self._stealth_instance:
            try:
                # Apply stealth to context (covers all pages)
                await self._stealth_instance.apply_stealth_async(context)
                logger.debug("Applied stealth patches to context")
            except Exception as e:
                logger.warning(f"Failed to apply stealth patches to context: {e}")

    async def _stealth_page(self, page: Page):
        """Apply stealth to individual page"""
        if not self._stealth_available or not self._stealth_instance:
            return
        try:
            await self._stealth_instance.apply_stealth_async(page)
            logger.debug("Applied stealth patches to page")
        except Exception as e:
            logger.warning(f"Stealth page patch failed: {e}")

    def _get_random_viewport(self) -> dict:
        """Get random realistic viewport size"""
        return random.choice(VIEWPORT_SIZES)

    async def create_stealth_page(self, context: BrowserContext) -> Page:
        """
        Create a new stealth page in context.

        Applies additional page-level evasions.
        """
        page = await context.new_page()

        # Apply page-level stealth
        if self._stealth_available:
            await self._stealth_page(page)

        # Add human-like behavior
        await self._add_human_behavior(page)

        return page

    async def _add_human_behavior(self, page: Page):
        """Add human-like behavior scripts"""
        # Override webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Add realistic plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Hide automation indicators
        await page.add_init_script("""
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)

    async def simulate_human_scroll(self, page: Page, scroll_amount: int = 500):
        """Simulate human-like scrolling behavior"""
        import asyncio

        # Random scroll increments
        current = 0
        while current < scroll_amount:
            increment = random.randint(50, 150)
            current += increment

            await page.evaluate(f"window.scrollBy(0, {increment})")
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # Sometimes scroll back a bit
        if random.random() > 0.7:
            await asyncio.sleep(random.uniform(0.2, 0.5))
            await page.evaluate(f"window.scrollBy(0, -{random.randint(50, 100)})")

    async def simulate_mouse_movement(self, page: Page):
        """Simulate random mouse movements"""
        import asyncio

        viewport = page.viewport_size
        if not viewport:
            return

        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)

            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))


# Singleton instance
_stealth_browser: Optional[StealthBrowser] = None


def get_stealth_browser() -> StealthBrowser:
    """Get singleton StealthBrowser instance"""
    global _stealth_browser
    if _stealth_browser is None:
        _stealth_browser = StealthBrowser()
    return _stealth_browser
