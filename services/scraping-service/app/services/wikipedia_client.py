"""
Wikipedia MediaWiki API Client

Implements Wikipedia data extraction using MediaWiki API.
Supports both Query API and REST API (MediaWiki 1.35+).

Issue P1-2: Rate limiting added for polite API usage.

References:
- Query API: https://www.mediawiki.org/wiki/API:Query
- REST API: https://www.mediawiki.org/wiki/API:REST_API
- API Etiquette: https://www.mediawiki.org/wiki/API:Etiquette
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class WikipediaLanguage(str, Enum):
    """Supported Wikipedia languages"""
    GERMAN = "de"
    ENGLISH = "en"


@dataclass
class WikipediaArticle:
    """Wikipedia article data"""
    title: str
    extract: str  # Plain text summary
    url: str
    categories: List[str]
    infobox: Dict[str, Any]
    links: List[str]  # Related entity links
    language: str

    # Metadata
    page_id: int
    last_modified: Optional[str] = None


@dataclass
class WikipediaSearchResult:
    """Wikipedia search result"""
    title: str
    page_id: int
    snippet: str  # HTML snippet with search term highlighted


class WikipediaClient:
    """
    Wikipedia MediaWiki API client.

    Provides entity enrichment through Wikipedia data extraction:
    - Article summaries and full text
    - Infobox structured data
    - Categories and related entities
    - Relationship extraction from article text

    Issue P1-2: Rate limiting integrated for polite API usage (~1 req/sec).
    """

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.base_urls = {
            WikipediaLanguage.GERMAN: "https://de.wikipedia.org",
            WikipediaLanguage.ENGLISH: "https://en.wikipedia.org"
        }

    async def _check_rate_limit(self, language: WikipediaLanguage) -> bool:
        """
        Check rate limit before making Wikipedia API request.

        Args:
            language: Wikipedia language for rate limit key

        Returns:
            True if request allowed, raises exception if rate limited

        Raises:
            httpx.HTTPStatusError: If rate limit exceeded (429)
        """
        allowed, remaining, retry_after = await rate_limiter.is_allowed(
            key=f"wikipedia:{language.value}",
            limit=settings.WIKIPEDIA_RATE_LIMIT,
            window=settings.WIKIPEDIA_RATE_LIMIT_WINDOW
        )

        if not allowed:
            logger.warning(
                f"Wikipedia API rate limit exceeded for {language.value}. "
                f"Retry after {retry_after}s"
            )
            # Wait and retry instead of failing immediately
            if retry_after and retry_after <= 5:
                logger.info(f"Waiting {retry_after}s for rate limit reset...")
                await asyncio.sleep(retry_after)
                return await self._check_rate_limit(language)  # Retry
            raise httpx.HTTPStatusError(
                f"Rate limit exceeded. Retry after {retry_after} seconds",
                request=None,
                response=None
            )

        return True

    async def search(
        self,
        query: str,
        language: WikipediaLanguage = WikipediaLanguage.GERMAN,
        limit: int = 10
    ) -> List[WikipediaSearchResult]:
        """
        Search Wikipedia articles.

        Args:
            query: Search query (entity name)
            language: Wikipedia language
            limit: Maximum number of results

        Returns:
            List of search results with snippets

        Example:
            results = await client.search("Elon Musk", limit=5)
            # [WikipediaSearchResult(title="Elon Musk", page_id=123, ...)]
        """
        base_url = self.base_urls[language]
        api_url = f"{base_url}/w/api.php"

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1
        }

        try:
            # Check rate limit before making request
            await self._check_rate_limit(language)

            response = await self.http_client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("query", {}).get("search", []):
                results.append(WikipediaSearchResult(
                    title=item["title"],
                    page_id=item["pageid"],
                    snippet=item["snippet"]
                ))

            logger.info(f"Wikipedia search for '{query}': {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Wikipedia search failed for '{query}': {e}")
            return []

    async def get_article(
        self,
        title: str,
        language: WikipediaLanguage = WikipediaLanguage.GERMAN,
        include_infobox: bool = True,
        include_categories: bool = True,
        include_links: bool = True
    ) -> Optional[WikipediaArticle]:
        """
        Get full Wikipedia article data.

        Args:
            title: Article title (exact match)
            language: Wikipedia language
            include_infobox: Extract infobox structured data
            include_categories: Extract article categories
            include_links: Extract related entity links

        Returns:
            WikipediaArticle with extracted data, or None if not found

        Example:
            article = await client.get_article("Tesla, Inc.")
            # WikipediaArticle(
            #     title="Tesla, Inc.",
            #     extract="Tesla, Inc. is an American automotive and clean energy company...",
            #     infobox={"Industry": "Automotive", "Founded": "2003", ...},
            #     categories=["Electric vehicle manufacturers", ...],
            #     links=["Elon Musk", "SpaceX", ...]
            # )
        """
        base_url = self.base_urls[language]
        api_url = f"{base_url}/w/api.php"

        # Build prop parameter based on requested data
        props = ["extracts", "info", "revisions"]
        if include_categories:
            props.append("categories")
        if include_links:
            props.append("links")

        params = {
            "action": "query",
            "titles": title,
            "prop": "|".join(props),
            "exintro": 1,  # Extract only intro section
            "explaintext": 1,  # Plain text (no HTML)
            "inprop": "url",  # Include URL
            "rvprop": "timestamp",  # Last modified timestamp
            "format": "json",
            "utf8": 1
        }

        # Add category/link limits
        if include_categories:
            params["cllimit"] = 50
        if include_links:
            params["pllimit"] = 100

        try:
            # Check rate limit before making request
            await self._check_rate_limit(language)

            response = await self.http_client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract page data
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                logger.warning(f"Wikipedia article not found: {title}")
                return None

            # Get first (and only) page
            page = list(pages.values())[0]

            # Check if page exists
            if "missing" in page:
                logger.warning(f"Wikipedia article not found: {title}")
                return None

            # Extract categories
            categories = []
            if include_categories and "categories" in page:
                categories = [cat["title"].replace("Category:", "")
                             for cat in page["categories"]]

            # Extract links (related entities)
            links = []
            if include_links and "links" in page:
                links = [link["title"] for link in page["links"]]

            # Get last modified timestamp
            last_modified = None
            if "revisions" in page and len(page["revisions"]) > 0:
                last_modified = page["revisions"][0].get("timestamp")

            # Extract infobox (requires HTML parse)
            infobox = {}
            if include_infobox:
                infobox = await self._extract_infobox(title, language)

            article = WikipediaArticle(
                title=page["title"],
                extract=page.get("extract", ""),
                url=page.get("fullurl", f"{base_url}/wiki/{title}"),
                categories=categories,
                infobox=infobox,
                links=links,
                language=language.value,
                page_id=page["pageid"],
                last_modified=last_modified
            )

            logger.info(f"Wikipedia article extracted: {title} ({len(article.extract)} chars)")
            return article

        except Exception as e:
            logger.error(f"Wikipedia article extraction failed for '{title}': {e}")
            return None

    async def _extract_infobox(
        self,
        title: str,
        language: WikipediaLanguage
    ) -> Dict[str, Any]:
        """
        Extract infobox structured data from Wikipedia article.

        Infoboxes contain key-value pairs like:
        - Industry, Founded, Founder (for companies)
        - Born, Occupation, Known for (for people)
        - Location, Type (for places)

        Args:
            title: Article title
            language: Wikipedia language

        Returns:
            Dictionary of infobox key-value pairs
        """
        base_url = self.base_urls[language]
        api_url = f"{base_url}/w/api.php"

        # Get HTML parse of article
        params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "utf8": 1
        }

        try:
            # Check rate limit before making request
            await self._check_rate_limit(language)

            response = await self.http_client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check if page exists
            if "error" in data:
                logger.warning(f"Wikipedia infobox extraction failed: {title}")
                return {}

            # Parse HTML
            html = data.get("parse", {}).get("text", {}).get("*", "")
            soup = BeautifulSoup(html, 'html.parser')

            # Find infobox table
            infobox = soup.find("table", {"class": "infobox"})
            if not infobox:
                logger.debug(f"No infobox found for: {title}")
                return {}

            # Extract key-value pairs from infobox rows
            infobox_data = {}
            for row in infobox.find_all("tr"):
                # Look for header cells (th) and data cells (td)
                header = row.find("th")
                data = row.find("td")

                if header and data:
                    key = header.get_text(strip=True)
                    value = data.get_text(separator=" ", strip=True)

                    # Clean up value (remove references [1], [2], etc.)
                    value = value.split("[")[0].strip()

                    if key and value:
                        infobox_data[key] = value

            logger.debug(f"Infobox extracted for {title}: {len(infobox_data)} fields")
            return infobox_data

        except Exception as e:
            logger.error(f"Infobox extraction failed for '{title}': {e}")
            return {}

    async def extract_relationships(
        self,
        title: str,
        language: WikipediaLanguage = WikipediaLanguage.GERMAN,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract potential relationships from Wikipedia article.

        Analyzes article text and infobox to identify relationships:
        - CEO, Founder → works_for, founded
        - Headquarters, Based in → located_in
        - Subsidiary, Owner → owns, owned_by

        Args:
            title: Article title (entity name)
            language: Wikipedia language
            entity_type: Hint for relationship extraction (PERSON, ORGANIZATION, etc.)

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
        article = await self.get_article(
            title=title,
            language=language,
            include_infobox=True,
            include_links=True
        )

        if not article:
            return []

        relationships = []

        # Extract relationships from infobox
        if article.infobox:
            relationships.extend(
                self._extract_relationships_from_infobox(
                    entity_name=title,
                    infobox=article.infobox,
                    entity_type=entity_type
                )
            )

        # Extract relationships from first paragraph
        if article.extract:
            relationships.extend(
                self._extract_relationships_from_text(
                    entity_name=title,
                    text=article.extract,
                    entity_type=entity_type
                )
            )

        logger.info(f"Extracted {len(relationships)} relationship candidates from {title}")
        return relationships

    def _extract_relationships_from_infobox(
        self,
        entity_name: str,
        infobox: Dict[str, Any],
        entity_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from infobox structured data.

        Maps infobox fields to relationship types:
        - Founded → founded
        - Founder → founded_by
        - CEO → CEO_of
        - Headquarters → located_in
        - Industry → operates_in
        """
        relationships = []

        # Relationship mappings (infobox_key → relationship_type)
        mappings = {
            # Organization relationships
            "Founded": ("founded", 0.95),
            "Founder": ("founded_by", 0.95),
            "Founders": ("founded_by", 0.95),
            "CEO": ("CEO_of", 0.95),
            "Headquarters": ("located_in", 0.90),
            "Location": ("located_in", 0.85),
            "Industry": ("operates_in", 0.80),
            "Parent": ("owned_by", 0.90),
            "Subsidiaries": ("owns", 0.85),

            # Person relationships
            "Born": ("born_in", 0.90),
            "Occupation": ("works_as", 0.80),
            "Known for": ("associated_with", 0.75),
            "Employer": ("works_for", 0.90),
            "Organization": ("member_of", 0.85),
        }

        for infobox_key, value in infobox.items():
            if infobox_key in mappings:
                relationship_type, confidence = mappings[infobox_key]

                # Split multiple values (comma-separated)
                entities = [v.strip() for v in value.split(",")]

                for related_entity in entities:
                    if related_entity and related_entity != entity_name:
                        relationships.append({
                            "entity1": entity_name,
                            "entity2": related_entity,
                            "relationship_type": relationship_type,
                            "confidence": confidence,
                            "evidence": f"Wikipedia infobox: {infobox_key}={value}",
                            "source": "wikipedia_infobox"
                        })

        return relationships

    def _extract_relationships_from_text(
        self,
        entity_name: str,
        text: str,
        entity_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from article text using pattern matching.

        Identifies relationship patterns in first paragraph:
        - "X is the CEO of Y" → CEO_of
        - "X founded Y" → founded
        - "X is located in Y" → located_in
        """
        relationships = []

        # Simple pattern matching (can be extended with NLP)
        patterns = {
            "CEO_of": ["is the CEO of", "serves as CEO of", "CEO of"],
            "founded": ["founded", "co-founded", "established"],
            "located_in": ["is located in", "based in", "headquartered in"],
            "works_for": ["works for", "employed by", "works at"],
            "owns": ["owns", "acquired", "purchased"],
        }

        # Extract first 500 characters for pattern matching
        intro = text[:500].lower()

        for relationship_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.lower() in intro:
                    # Extract context around pattern
                    idx = intro.index(pattern.lower())
                    context = text[max(0, idx-50):min(len(text), idx+100)]

                    relationships.append({
                        "entity1": entity_name,
                        "entity2": "UNKNOWN",  # Requires NER to extract
                        "relationship_type": relationship_type,
                        "confidence": 0.70,  # Lower confidence without full NER
                        "evidence": context,
                        "source": "wikipedia_text_pattern"
                    })
                    break  # Only one match per type

        return relationships
