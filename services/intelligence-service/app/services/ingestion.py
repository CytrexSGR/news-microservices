"""
RSS Article Ingestion Service
Fetches articles from Feed Service and normalizes them into intelligence events
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup

from app.clients.feed_client import feed_client
from app.crud.events import create_event, find_duplicate_events
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Mapping from Content-Analysis-V3 Tier0 categories to Intelligence categories
# V3 categories: CONFLICT, FINANCE, POLITICS, HUMANITARIAN, SECURITY, TECHNOLOGY, HEALTH, OTHER
# Intelligence categories: geo, finance, tech
CATEGORY_MAPPING = {
    # Geopolitical/Political events
    "CONFLICT": "geo",
    "POLITICS": "geo",
    "HUMANITARIAN": "geo",
    "SECURITY": "geo",
    # Financial events
    "FINANCE": "finance",
    # Technology events
    "TECHNOLOGY": "tech",
    # Fallbacks (map to geo as default for news intelligence)
    "HEALTH": "geo",
    "OTHER": "geo",
}


def map_category(v3_category: str | None) -> str | None:
    """
    Map Content-Analysis-V3 Tier0 category to Intelligence category.

    Args:
        v3_category: Category from V3 analysis (e.g., "FINANCE", "CONFLICT")

    Returns:
        Mapped category (geo, finance, tech) or None if not mappable
    """
    if not v3_category:
        return None
    return CATEGORY_MAPPING.get(v3_category.upper(), "geo")


class IngestionService:
    """Service for ingesting RSS articles into intelligence events"""

    @staticmethod
    def clean_html(text: str) -> str:
        """Remove HTML tags and clean text"""
        if not text:
            return ""

        # Remove HTML tags
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def normalize_source(source_url: str) -> str:
        """Extract clean source name from URL"""
        if not source_url:
            return "Unknown"

        # Extract domain name
        match = re.search(r'https?://(?:www\.)?([^/]+)', source_url)
        if match:
            domain = match.group(1)
            # Remove TLD and return cleaned name
            return domain.split('.')[0].capitalize()

        return "Unknown"

    async def ingest_rss_articles(
        self,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Ingest recent RSS articles from Feed Service

        Args:
            db: Database session
            hours: Fetch articles from last N hours
            limit: Maximum articles to fetch

        Returns:
            Statistics about ingestion
        """
        logger.info(f"Starting RSS ingestion: last {hours} hours, limit {limit}")

        stats = {
            "fetched": 0,
            "created": 0,
            "duplicates": 0,
            "errors": 0,
        }

        try:
            # Fetch articles from Feed Service
            articles = await feed_client.get_recent_articles(hours=hours, limit=limit)
            stats["fetched"] = len(articles)

            logger.info(f"Fetched {len(articles)} articles from Feed Service")

            for article in articles:
                try:
                    await self._process_article(db, article, stats)
                except Exception as e:
                    logger.error(f"Error processing article {article.get('id')}: {e}")
                    stats["errors"] += 1

            logger.info(f"Ingestion complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to ingest articles: {e}")
            stats["errors"] += 1
            return stats

    async def _process_article(
        self,
        db: AsyncSession,
        article: Dict[str, Any],
        stats: Dict[str, Any]
    ):
        """Process a single article"""
        # Extract and normalize data
        title = self.clean_html(article.get("title", ""))
        description = self.clean_html(article.get("description", ""))
        source_url = article.get("link", article.get("url", ""))
        source = self.normalize_source(source_url)

        # Parse published date
        published_at_str = article.get("published_at") or article.get("pubDate") or article.get("published")
        if isinstance(published_at_str, str):
            try:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            except ValueError:
                published_at = datetime.utcnow()
        else:
            published_at = published_at_str or datetime.utcnow()

        # Extract analysis data
        keywords = article.get("keywords", [])
        topics = article.get("topics", [])
        entities = article.get("entities", [])

        # Extract category from v3_analysis or analysis_summary
        # V3 returns: CONFLICT, FINANCE, POLITICS, HUMANITARIAN, SECURITY, TECHNOLOGY, HEALTH, OTHER
        # Intelligence expects: geo, finance, tech
        category = None
        v3_analysis = article.get("v3_analysis", {})
        if v3_analysis:
            tier0 = v3_analysis.get("tier0", {})
            v3_category = tier0.get("category")
            category = map_category(v3_category)
            logger.debug(f"Mapped category: {v3_category} -> {category} from v3_analysis")

        # Check for duplicates
        duplicates = await find_duplicate_events(
            db,
            title=title,
            published_at=published_at,
            time_window_hours=24
        )

        if duplicates:
            logger.debug(f"Duplicate found for: {title[:50]}")
            stats["duplicates"] += 1
            return

        # Create new event with analysis data
        await create_event(
            db,
            title=title,
            description=description,
            source=source,
            source_url=source_url,
            published_at=published_at,
            language=article.get("language", "en"),
            category=category,
            keywords=keywords,
            entities=entities
        )

        stats["created"] += 1
        logger.debug(f"Created event: {title[:50]} (category: {category}, keywords: {len(keywords)}, entities: {len(entities)})")


# Global service instance
ingestion_service = IngestionService()
