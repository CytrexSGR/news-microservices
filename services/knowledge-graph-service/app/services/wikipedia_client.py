"""
Wikipedia Client for Knowledge Graph Enrichment

HTTP client that calls scraping-service Wikipedia API endpoints.
Provides entity enrichment through Wikipedia data extraction.
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WikipediaSearchResult:
    """Wikipedia search result"""
    title: str
    page_id: int
    snippet: str


@dataclass
class WikipediaArticle:
    """Wikipedia article data"""
    title: str
    extract: str
    url: str
    categories: List[str]
    infobox: Dict[str, Any]
    links: List[str]
    language: str
    page_id: int
    last_modified: Optional[str] = None


class WikipediaClient:
    """
    Client for Wikipedia data extraction via scraping-service.

    Calls scraping-service Wikipedia API endpoints to enrich
    Knowledge Graph entities with structured Wikipedia data.
    """

    def __init__(self, scraping_service_url: str):
        """
        Initialize Wikipedia client.

        Args:
            scraping_service_url: Base URL of scraping-service
                                  (e.g., "http://news-scraping-service:8009")
        """
        self.base_url = scraping_service_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"Wikipedia client initialized: {self.base_url}")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def search(
        self,
        query: str,
        language: str = "de",
        limit: int = 10
    ) -> List[WikipediaSearchResult]:
        """
        Search Wikipedia articles.

        Args:
            query: Search query (entity name)
            language: Wikipedia language (de, en)
            limit: Maximum number of results

        Returns:
            List of search results

        Example:
            results = await client.search("Elon Musk", language="en", limit=5)
            # [WikipediaSearchResult(title="Elon Musk", page_id=123, ...)]
        """
        url = f"{self.base_url}/api/v1/wikipedia/search"

        payload = {
            "query": query,
            "language": language,
            "limit": limit
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(WikipediaSearchResult(
                    title=item["title"],
                    page_id=item["page_id"],
                    snippet=item["snippet"]
                ))

            logger.info(f"Wikipedia search: query='{query}', results={len(results)}")
            return results

        except httpx.HTTPError as e:
            logger.error(f"Wikipedia search failed for '{query}': {e}")
            return []

    async def get_article(
        self,
        title: str,
        language: str = "de",
        include_infobox: bool = True,
        include_categories: bool = True,
        include_links: bool = True
    ) -> Optional[WikipediaArticle]:
        """
        Get full Wikipedia article data.

        Args:
            title: Article title (exact match)
            language: Wikipedia language (de, en)
            include_infobox: Extract infobox structured data
            include_categories: Extract article categories
            include_links: Extract related entity links

        Returns:
            WikipediaArticle with extracted data, or None if not found

        Example:
            article = await client.get_article("Tesla, Inc.", language="en")
            # WikipediaArticle(
            #     title="Tesla, Inc.",
            #     extract="Tesla, Inc. is an American automotive...",
            #     infobox={"Industry": "Automotive", ...},
            #     categories=["Electric vehicle manufacturers", ...],
            #     links=["Elon Musk", "SpaceX", ...]
            # )
        """
        url = f"{self.base_url}/api/v1/wikipedia/article"

        payload = {
            "title": title,
            "language": language,
            "include_infobox": include_infobox,
            "include_categories": include_categories,
            "include_links": include_links
        }

        try:
            response = await self.client.post(url, json=payload)

            if response.status_code == 404:
                logger.warning(f"Wikipedia article not found: {title}")
                return None

            response.raise_for_status()
            data = response.json()

            article = WikipediaArticle(
                title=data["title"],
                extract=data["extract"],
                url=data["url"],
                categories=data.get("categories", []),
                infobox=data.get("infobox", {}),
                links=data.get("links", []),
                language=data["language"],
                page_id=data["page_id"],
                last_modified=data.get("last_modified")
            )

            logger.info(
                f"Wikipedia article extracted: {title} "
                f"({len(article.extract)} chars, {len(article.infobox)} infobox fields)"
            )
            return article

        except httpx.HTTPError as e:
            logger.error(f"Wikipedia article extraction failed for '{title}': {e}")
            return None

    async def extract_relationships(
        self,
        title: str,
        language: str = "de",
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract relationship candidates from Wikipedia article.

        Args:
            title: Article title (entity name)
            language: Wikipedia language (de, en)
            entity_type: Entity type hint (PERSON, ORGANIZATION, etc.)

        Returns:
            List of relationship candidates with confidence scores

        Example:
            relationships = await client.extract_relationships("Tesla, Inc.")
            # [
            #     {"entity1": "Elon Musk", "entity2": "Tesla",
            #      "relationship_type": "CEO_of", "confidence": 0.95},
            #     {"entity1": "Tesla", "entity2": "Palo Alto",
            #      "relationship_type": "located_in", "confidence": 0.90}
            # ]
        """
        url = f"{self.base_url}/api/v1/wikipedia/relationships"

        payload = {
            "title": title,
            "language": language,
            "entity_type": entity_type
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            relationships = data.get("relationships", [])

            logger.info(
                f"Wikipedia relationships extracted: entity='{title}', "
                f"count={len(relationships)}"
            )
            return relationships

        except httpx.HTTPError as e:
            logger.error(f"Wikipedia relationship extraction failed for '{title}': {e}")
            return []
