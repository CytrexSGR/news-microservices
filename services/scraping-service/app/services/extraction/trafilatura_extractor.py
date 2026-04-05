"""
Trafilatura Content Extractor

trafilatura is optimized for web content extraction with:
- Better handling of boilerplate removal
- Metadata extraction (author, date, title)
- XML/TEI output support
- Language detection
"""
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

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
    extracted_title: Optional[str] = None
    extracted_authors: Optional[list] = None
    extracted_publish_date: Optional[str] = None
    extracted_metadata: Optional[dict] = None


class TrafilaturaExtractor:
    """
    Content extractor using trafilatura library.

    Trafilatura excels at:
    - News articles
    - Blog posts
    - General web content

    Less suitable for:
    - JavaScript-heavy SPAs (need Playwright first)
    - Highly structured data (use JSON-LD extractor)
    """

    def __init__(self):
        self._trafilatura = None
        self._config = None
        self._init_trafilatura()

    def _init_trafilatura(self):
        """Initialize trafilatura with configuration"""
        try:
            import trafilatura
            from trafilatura.settings import use_config

            self._trafilatura = trafilatura
            # Configure trafilatura for optimal news extraction
            self._config = use_config()
            self._config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
            self._config.set("DEFAULT", "MIN_OUTPUT_SIZE", "50")
            self._config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")

            logger.info("trafilatura initialized successfully")
        except ImportError as e:
            logger.warning(f"trafilatura not available: {e}")
            self._trafilatura = None

    def extract(self, html: str, url: str, min_word_count: int = 50) -> ScrapeResult:
        """
        Extract content from HTML using trafilatura.

        Args:
            html: Raw HTML content
            url: Source URL (for metadata)
            min_word_count: Minimum words for success

        Returns:
            ScrapeResult with extracted content
        """
        if not self._trafilatura:
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message="trafilatura not available",
                method_used="trafilatura"
            )

        try:
            # Extract main content
            content = self._trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,  # Allow fallback extractors
                favor_precision=True,  # Prefer quality over quantity
                config=self._config
            )

            if not content or len(content.split()) < min_word_count:
                return ScrapeResult(
                    content=content,
                    word_count=len(content.split()) if content else 0,
                    status=ScrapeStatus.ERROR,
                    error_message="Extracted content too short or empty",
                    method_used="trafilatura"
                )

            # Extract metadata separately
            metadata_dict = self._extract_metadata(html, url)

            word_count = len(content.split())

            return ScrapeResult(
                content=content,
                word_count=word_count,
                status=ScrapeStatus.SUCCESS,
                method_used="trafilatura",
                extracted_title=metadata_dict.get("title"),
                extracted_authors=metadata_dict.get("authors"),
                extracted_publish_date=metadata_dict.get("date"),
                extracted_metadata=metadata_dict
            )

        except Exception as e:
            logger.error(f"Trafilatura extraction failed for {url}: {e}")
            return ScrapeResult(
                content=None,
                word_count=0,
                status=ScrapeStatus.ERROR,
                error_message=str(e),
                method_used="trafilatura"
            )

    def _extract_metadata(self, html: str, url: str) -> dict:
        """Extract metadata using trafilatura's metadata extractor"""
        try:
            metadata = self._trafilatura.extract_metadata(html, default_url=url)

            if metadata:
                return {
                    "method": "trafilatura",
                    "title": metadata.title,
                    "authors": [metadata.author] if metadata.author else [],
                    "date": metadata.date,
                    "sitename": metadata.sitename,
                    "categories": metadata.categories or [],
                    "tags": metadata.tags or [],
                    "description": metadata.description,
                    "license": getattr(metadata, 'license', None),
                }

            return {"method": "trafilatura"}

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
            return {"method": "trafilatura"}

    @property
    def is_available(self) -> bool:
        """Check if trafilatura is available"""
        return self._trafilatura is not None
