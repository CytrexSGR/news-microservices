"""
Feed Service Client - Connects to existing Feed Service
"""
import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

FEED_SERVICE_URL = os.getenv("FEED_SERVICE_URL", "http://feed-service:8000")


class FeedClient:
    """Client for Feed Service API"""

    def __init__(self, base_url: str = FEED_SERVICE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def get_feeds(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all feeds from Feed Service

        Returns:
            List of feed objects
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/feeds",
                params={"skip": skip, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch feeds: {e}")
            return []

    def get_recent_articles_sync(
        self,
        hours: int = 24,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Get recent articles using shared sync engine (for Celery tasks).
        Avoids creating a new engine per call.

        Args:
            hours: Get articles from last N hours
            limit: Max articles to return

        Returns:
            List of article objects
        """
        try:
            from app.database import SyncSessionLocal
            from sqlalchemy import text
            import json

            time_threshold = datetime.utcnow() - timedelta(hours=hours)

            with SyncSessionLocal() as session:
                query = text("""
                    SELECT
                        fi.id,
                        fi.title,
                        fi.description,
                        fi.link,
                        fi.published_at,
                        fi.feed_id,
                        aa.tier1_results->>'topics' as topics_json,
                        aa.tier1_results->>'entities' as entities_json,
                        aa.tier1_results->>'summary' as summary
                    FROM feed_items fi
                    LEFT JOIN article_analysis aa ON fi.id = aa.article_id AND aa.success = true
                    WHERE fi.published_at >= :time_threshold
                    ORDER BY fi.published_at DESC
                    LIMIT :limit
                """)

                result = session.execute(
                    query,
                    {"time_threshold": time_threshold, "limit": limit}
                )

                items = []
                for row in result:
                    topics = json.loads(row.topics_json) if row.topics_json else []
                    entities = json.loads(row.entities_json) if row.entities_json else []

                    keywords = [
                        kw for kw in [
                            e.get("normalized_text", e.get("text", ""))
                            for e in entities
                            if e.get("type") in ["ORGANIZATION", "PERSON", "LOCATION", "PRODUCT"]
                        ]
                        if kw and kw.strip()
                    ]

                    items.append({
                        "id": str(row.id),
                        "title": row.title,
                        "description": row.description or row.summary or "",
                        "link": row.link,
                        "published_at": row.published_at.isoformat() if row.published_at else None,
                        "feed_id": str(row.feed_id) if row.feed_id else None,
                        "keywords": keywords,
                        "topics": topics,
                        "entities": entities,
                    })

                return items

        except Exception as e:
            logger.error(f"Failed to fetch recent articles: {e}")
            return []

    async def get_recent_articles(
        self,
        feed_id: Optional[str] = None,
        hours: int = 24,
        skip: int = 0,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Get recent articles (async wrapper for API endpoints).
        Delegates to sync implementation.
        """
        return self.get_recent_articles_sync(hours=hours, limit=limit)

    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get single article by ID

        Args:
            article_id: Article ID

        Returns:
            Article object or None
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/articles/{article_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch article {article_id}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Feed Service is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False


# Global client instance
feed_client = FeedClient()
