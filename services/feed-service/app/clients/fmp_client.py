"""
FMP Service Client for feed-service
Communicates with fmp-service to fetch financial news
"""
import httpx
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class FMPServiceClient:
    """
    Client to communicate with fmp-service (port 8113)
    NOT the FMP API directly - we use our internal service
    """

    def __init__(self, base_url: str = "http://fmp-service:8113/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_news(self, category: str, page: int = 0, limit: int = 20) -> List[Dict]:
        """
        Fetch news from fmp-service internal API

        Args:
            category: general | stock | forex | crypto | ma
            page: Page number
            limit: Results per page

        Returns:
            List of news items in FMP format

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/news/live/{category}"
        params = {'page': page, 'limit': limit}

        logger.debug(f"Fetching FMP {category} news: {url}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched {len(data)} FMP {category} news items")
            return data

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch FMP {category} news: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
