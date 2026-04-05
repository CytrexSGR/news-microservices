"""Wikidata API client for entity linking."""
import httpx
import logging
import asyncio
from typing import Optional, List, Dict, Any
from app.models.entities import WikidataMatch
from app.config import settings
from news_mcp_common.resilience import (
    ResilientHTTPClient,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)

logger = logging.getLogger(__name__)


class WikidataClient:
    """
    Client for Wikidata API.

    Uses Wikidata's wbsearchentities and wbgetentities APIs
    to search and link entities to canonical Wikidata entries.

    API Documentation: https://www.wikidata.org/w/api.php

    User-Agent Policy: https://meta.wikimedia.org/wiki/User-Agent_policy
    """

    def __init__(self):
        self.base_url = settings.WIKIDATA_API_URL
        self.timeout = settings.WIKIDATA_TIMEOUT

        # User-Agent per Wikimedia policy (prevents 403 errors)
        # Format: ProjectName/Version (Contact) Framework/Version
        user_agent = (
            f"{settings.SERVICE_NAME}/1.0 "
            f"(andreas@test.com) "
            f"httpx/{httpx.__version__}"
        )

        # Circuit breaker configuration for Wikidata API
        # Wikidata can be slow/unavailable, prevent cascade failures
        cb_config = CircuitBreakerConfig(
            failure_threshold=5,      # Open after 5 consecutive failures
            success_threshold=2,      # Close after 2 successes in half-open state
            timeout_seconds=60,       # Wait 60s before trying again
            enable_metrics=True,      # Track circuit breaker metrics
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="wikidata-api",
            base_url=self.base_url,
            config=cb_config,
            timeout=self.timeout,
        )

        # Store User-Agent for use in requests
        # ResilientHTTPClient doesn't support default headers, pass per-request
        self.headers = {"User-Agent": user_agent}

        # Rate limiting tracking
        self._rate_limit_delay = 0.1  # Start with 100ms between requests

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def search_entity(
        self,
        query: str,
        entity_type: str,
        language: str = "de",
        limit: int = 5
    ) -> Optional[WikidataMatch]:
        """
        Search for entity in Wikidata.

        Args:
            query: Entity name to search for
            entity_type: Expected entity type (PERSON, ORGANIZATION, LOCATION, etc.)
            language: Language code (de, en, etc.)
            limit: Maximum number of results to retrieve

        Returns:
            WikidataMatch if found with sufficient confidence, None otherwise
        """

        # 🔧 Feature Flag: Wikidata disabled until entity quality improves
        if not settings.WIKIDATA_ENABLED:
            logger.debug(f"Wikidata lookup disabled for '{query}' (WIKIDATA_ENABLED=False)")
            return None

        try:
            # Search for entities
            search_results = await self._search_entities(query, language, limit)

            if not search_results:
                logger.debug(f"No Wikidata results for '{query}'")
                return None

            # Get detailed information for top result
            top_result = search_results[0]
            entity_id = top_result["id"]

            entity_data = await self._get_entity_details(entity_id, language)

            if not entity_data:
                return None

            # Calculate confidence based on entity data
            confidence = self._calculate_confidence(
                entity_data,
                entity_type,
                query
            )

            # Extract aliases
            aliases = self._extract_aliases(entity_data, language)

            match = WikidataMatch(
                id=entity_id,
                label=top_result.get("label", query),
                description=top_result.get("description", ""),
                confidence=confidence,
                aliases=aliases,
                entity_type=entity_type
            )

            logger.info(
                f"Wikidata match: '{query}' → {match.id} ({match.label}) "
                f"confidence={confidence:.2f}"
            )

            return match

        except CircuitBreakerOpenError:
            logger.warning(
                f"Circuit breaker OPEN for Wikidata API - skipping query '{query}' "
                f"(service temporarily unavailable)"
            )
            return None
        except httpx.TimeoutException:
            logger.warning(f"Wikidata API timeout for query '{query}'")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Wikidata API error for query '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Wikidata search for '{query}': {e}")
            return None

    async def _search_entities(
        self,
        query: str,
        language: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Call wbsearchentities API.

        Endpoint: https://www.wikidata.org/w/api.php?action=wbsearchentities

        Note: Circuit breaker handles retries and failures automatically.
        """
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": limit,
            "format": "json"
        }

        try:
            # Rate limiting delay (basic throttling)
            await asyncio.sleep(self._rate_limit_delay)

            # ResilientHTTPClient handles circuit breaking and retries
            response = await self.client.get("", params=params, headers=self.headers)  # base_url already set

            # Handle rate limiting (429) - adjust delay
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning(
                    f"Rate limited by Wikidata API. "
                    f"Adjusting delay to {retry_after}s"
                )
                self._rate_limit_delay = max(self._rate_limit_delay, retry_after / 2)
                # Don't raise - let circuit breaker handle it
                return []

            # Handle forbidden (403) - User-Agent issue
            elif response.status_code == 403:
                logger.error(
                    f"Wikidata API returned 403 Forbidden. "
                    f"User-Agent: {self.client.headers.get('User-Agent')}"
                )
                return []

            response.raise_for_status()
            data = response.json()
            return data.get("search", [])

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} searching Wikidata")
            raise  # Let circuit breaker track this failure

    async def _get_entity_details(
        self,
        entity_id: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed entity information.

        Endpoint: https://www.wikidata.org/w/api.php?action=wbgetentities

        Note: Circuit breaker handles retries and failures automatically.
        """
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "languages": language,
            "props": "info|labels|descriptions|aliases|claims",
            "format": "json"
        }

        try:
            # Rate limiting delay (basic throttling)
            await asyncio.sleep(self._rate_limit_delay)

            # ResilientHTTPClient handles circuit breaking and retries
            response = await self.client.get("", params=params, headers=self.headers)  # base_url already set

            # Handle rate limiting (429) - adjust delay
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning(
                    f"Rate limited by Wikidata API (entity details). "
                    f"Adjusting delay to {retry_after}s"
                )
                self._rate_limit_delay = max(self._rate_limit_delay, retry_after / 2)
                return None

            response.raise_for_status()
            data = response.json()
            entities = data.get("entities", {})
            return entities.get(entity_id)

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} fetching entity {entity_id}")
            raise  # Let circuit breaker track this failure

    def _calculate_confidence(
        self,
        entity_data: Dict[str, Any],
        expected_type: str,
        original_query: str
    ) -> float:
        """
        Calculate confidence score for entity match.

        Factors:
        1. Has instance of property (P31) - +0.3
        2. Has description - +0.1
        3. Has aliases - +0.1
        4. Label similarity to query - up to +0.5

        Base confidence: 0.5
        """
        confidence = 0.5

        # Check instance of property (P31)
        claims = entity_data.get("claims", {})
        if "P31" in claims:
            confidence += 0.3

        # Has description
        descriptions = entity_data.get("descriptions", {})
        if descriptions:
            confidence += 0.1

        # Has aliases
        aliases = entity_data.get("aliases", {})
        if aliases:
            confidence += 0.1

        # Label similarity (very simple - exact match = +0.5, partial = proportional)
        labels = entity_data.get("labels", {})
        if labels:
            label_values = [label.get("value", "") for label in labels.values()]
            for label in label_values:
                if label.lower() == original_query.lower():
                    confidence += 0.5
                    break
                elif original_query.lower() in label.lower() or label.lower() in original_query.lower():
                    confidence += 0.25
                    break

        return min(confidence, 1.0)

    def _extract_aliases(
        self,
        entity_data: Dict[str, Any],
        language: str
    ) -> List[str]:
        """Extract all aliases for the entity."""
        aliases_set = set()

        # Add label
        labels = entity_data.get("labels", {})
        if language in labels:
            aliases_set.add(labels[language].get("value", ""))

        # Add aliases
        aliases = entity_data.get("aliases", {})
        if language in aliases:
            for alias in aliases[language]:
                aliases_set.add(alias.get("value", ""))

        return list(aliases_set)
