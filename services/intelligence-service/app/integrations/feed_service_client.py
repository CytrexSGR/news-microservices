"""
Feed Service Integration Client.

Handles communication with feed-service for retrieving and processing feed data.

Service: feed-service (8101)
Base URL: http://feed-service:8101
"""

import logging
from typing import Optional, Dict, Any, List
import httpx

from app.core.http_client import ResilientHttpClient, HttpClientFactory

logger = logging.getLogger(__name__)


class FeedServiceClient:
    """
    Client for feed-service integration.

    Provides methods for:
    - Getting feeds
    - Retrieving articles
    - Getting feed analytics
    """

    def __init__(self, http_client: Optional[ResilientHttpClient] = None):
        """
        Initialize feed service client.

        Args:
            http_client: ResilientHttpClient instance (or None to use factory)
        """
        self.http_client = http_client or HttpClientFactory.get_client("feed-service")

    async def get_feeds(self) -> Dict[str, Any]:
        """
        Get list of active feeds.

        Returns:
            Dictionary with feeds information
        """
        try:
            async with self.http_client as client:
                response = await client.get("/api/v1/feeds")
                data = response.json()
                logger.debug(f"Retrieved {len(data.get('feeds', []))} feeds")
                return data
        except Exception as e:
            logger.error(f"Failed to get feeds: {e}")
            raise

    async def get_articles(
        self,
        feed_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get articles from feed.

        Args:
            feed_id: Specific feed ID (if None, gets all articles)
            limit: Maximum articles to retrieve
            offset: Pagination offset

        Returns:
            Dictionary with articles information
        """
        try:
            params = {"limit": limit, "offset": offset}
            path = "/api/v1/articles"

            async with self.http_client as client:
                response = await client.get(path, params=params)
                data = response.json()
                logger.debug(f"Retrieved {len(data.get('articles', []))} articles")
                return data
        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            raise

    async def get_article_by_id(self, article_id: str) -> Dict[str, Any]:
        """
        Get specific article by ID.

        Args:
            article_id: Article ID

        Returns:
            Article information
        """
        try:
            path = f"/api/v1/articles/{article_id}"

            async with self.http_client as client:
                response = await client.get(path)
                data = response.json()
                logger.debug(f"Retrieved article: {article_id}")
                return data
        except Exception as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            raise

    async def get_client_stats(self) -> Dict[str, Any]:
        """Get circuit breaker stats for feed service client"""
        return self.http_client.get_stats()


# Singleton instance
_feed_service_client: Optional[FeedServiceClient] = None


async def get_feed_service_client() -> FeedServiceClient:
    """Get or create feed service client"""
    global _feed_service_client
    if _feed_service_client is None:
        _feed_service_client = FeedServiceClient()
    return _feed_service_client
