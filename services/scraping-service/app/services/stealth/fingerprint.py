"""
Browser Fingerprint Generator

Generates realistic, consistent browser fingerprints.
"""
import hashlib
import random
from typing import Dict, Any, Optional

from app.core.user_agents import get_user_agent_pool

# WebGL vendors and renderers
WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
    "Google Inc. (AMD)",
    "Intel Inc.",
    "NVIDIA Corporation",
]

WEBGL_RENDERERS = [
    "ANGLE (NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    "Mesa DRI Intel(R) UHD Graphics 620",
]

# Screen resolutions
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080, "depth": 24},
    {"width": 2560, "height": 1440, "depth": 24},
    {"width": 1366, "height": 768, "depth": 24},
    {"width": 1536, "height": 864, "depth": 24},
    {"width": 3840, "height": 2160, "depth": 30},
]

# Hardware concurrency (CPU cores)
HARDWARE_CONCURRENCY = [4, 6, 8, 12, 16]

# Device memory (GB)
DEVICE_MEMORY = [4, 8, 16, 32]


class FingerprintGenerator:
    """
    Generates realistic browser fingerprints.

    Used to make scraped sessions look like real users.
    """

    def __init__(self):
        self._ua_pool = get_user_agent_pool()
        self._domain_cache: Dict[str, Dict[str, Any]] = {}

    def generate(self) -> Dict[str, Any]:
        """Generate a random browser fingerprint"""
        screen = random.choice(SCREEN_RESOLUTIONS)

        return {
            "user_agent": self._ua_pool.get_random(),
            "viewport": {
                "width": screen["width"],
                "height": screen["height"] - random.randint(50, 150)  # Account for browser chrome
            },
            "screen": screen,
            "timezone": random.choice([
                "Europe/Berlin", "Europe/London", "Europe/Paris",
                "America/New_York", "America/Chicago"
            ]),
            "locale": random.choice(["de-DE", "en-US", "en-GB", "fr-FR"]),
            "webgl_vendor": random.choice(WEBGL_VENDORS),
            "webgl_renderer": random.choice(WEBGL_RENDERERS),
            "hardware_concurrency": random.choice(HARDWARE_CONCURRENCY),
            "device_memory": random.choice(DEVICE_MEMORY),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "color_depth": screen["depth"],
            "touch_support": False,
            "do_not_track": random.choice([None, "1"]),
        }

    def generate_for_domain(self, domain: str) -> Dict[str, Any]:
        """
        Generate domain-consistent fingerprint.

        Same domain gets same fingerprint within session
        (simulates same user returning to site).
        """
        if domain not in self._domain_cache:
            # Use domain hash for deterministic but varied selection
            hash_val = int(hashlib.md5(domain.encode()).hexdigest(), 16)
            random.seed(hash_val)

            self._domain_cache[domain] = self.generate()

            # Reset random seed
            random.seed()

        return self._domain_cache[domain]

    def get_browser_args(self, fingerprint: Dict[str, Any]) -> list:
        """Get Playwright browser launch args from fingerprint"""
        return [
            f'--window-size={fingerprint["screen"]["width"]},{fingerprint["screen"]["height"]}',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
        ]

    def get_context_options(self, fingerprint: Dict[str, Any]) -> dict:
        """Get Playwright context options from fingerprint"""
        return {
            "viewport": fingerprint["viewport"],
            "locale": fingerprint["locale"],
            "timezone_id": fingerprint["timezone"],
            "color_scheme": "light",
            "extra_http_headers": {
                "Accept-Language": f'{fingerprint["locale"][:2]},{fingerprint["locale"]};q=0.9,en;q=0.8',
            }
        }

    def get_page_scripts(self, fingerprint: Dict[str, Any]) -> list:
        """Get init scripts to apply fingerprint to page"""
        return [
            # Override WebGL vendor/renderer
            f"""
            const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint["webgl_vendor"]}';
                if (parameter === 37446) return '{fingerprint["webgl_renderer"]}';
                return getParameterOrig.call(this, parameter);
            }};
            """,
            # Override hardware concurrency
            f"""
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint["hardware_concurrency"]}
            }});
            """,
            # Override device memory
            f"""
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint["device_memory"]}
            }});
            """,
            # Override platform
            f"""
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint["platform"]}'
            }});
            """,
        ]

    def clear_cache(self):
        """Clear domain fingerprint cache"""
        self._domain_cache.clear()


# Singleton instance
_fingerprint_generator: Optional[FingerprintGenerator] = None


def get_fingerprint_generator() -> FingerprintGenerator:
    """Get singleton FingerprintGenerator instance"""
    global _fingerprint_generator
    if _fingerprint_generator is None:
        _fingerprint_generator = FingerprintGenerator()
    return _fingerprint_generator
