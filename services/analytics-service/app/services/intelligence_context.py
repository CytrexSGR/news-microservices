"""Intelligence Context Service - Returns raw data for Claude interpretation.

Unlike RAGService which generates LLM answers, this service returns
structured context data that Claude Desktop can interpret directly.

This eliminates the redundant LLM call:
  Before: Claude -> ask_intelligence -> GPT-4o-mini -> Answer
  After:  Claude -> get_intelligence_context -> Raw Data -> Claude interprets
"""

import httpx
import structlog
from typing import Optional, List, Dict, Any

from app.core.config import settings

logger = structlog.get_logger()


class IntelligenceContextService:
    """
    Service for retrieving intelligence context without LLM interpretation.

    Returns raw, structured data that Claude can interpret directly,
    following the iterative drill-down pattern.
    """

    def __init__(self):
        self.search_url = getattr(settings, 'SEARCH_SERVICE_URL', 'http://search-service:8006')
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_context(
        self,
        question: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        entity_filter: Optional[str] = None,
        sector_filter: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get intelligence context for a question.

        Args:
            question: Natural language question (used for semantic search)
            limit: Maximum articles to return (default: 10)
            min_similarity: Minimum similarity threshold (default: 0.5)
            entity_filter: Optional entity to focus on
            sector_filter: Optional sector to focus on
            days: Time window in days (default: 7)

        Returns:
            Structured context with articles and intelligence summary
        """
        # Step 1: Semantic search for relevant articles
        all_articles = await self._semantic_search(
            query=question,
            limit=limit + 5,  # Fetch extra for filtering
            min_similarity=min_similarity,
        )

        # Step 2: Apply filters
        filtered = all_articles
        if entity_filter:
            filtered = [
                a for a in filtered
                if entity_filter.lower() in str(a.get("entities", [])).lower()
            ]
        # TODO: Implement sector_filter when articles have sector metadata
        # TODO: Implement days filter via search-service date range parameter

        # Step 3: Get intelligence summary
        intel_summary = await self._get_intelligence_summary()

        # Step 4: Build response with pagination info
        total_found = len(filtered)
        limited_articles = filtered[:limit]

        return {
            "question": question,
            "articles": [
                {
                    "title": a.get("title", "Untitled"),
                    "url": a.get("url"),
                    "content_snippet": (a.get("content", "")[:300] + "..."
                                       if len(a.get("content", "")) > 300
                                       else a.get("content", "")),
                    "published_at": a.get("published_at"),
                    "similarity": round(a.get("similarity", 0), 3),
                    "sentiment": a.get("sentiment"),
                    "entities": a.get("entities", []),
                }
                for a in limited_articles
            ],
            "total_found": total_found,
            "showing": len(limited_articles),
            "has_more": total_found > limit,
            "limit": limit,
            "filters_applied": {
                "entity": entity_filter,
                "sector": sector_filter,
                "days": days,
                "min_similarity": min_similarity,
            },
            "intelligence_summary": intel_summary,
        }

    async def _semantic_search(
        self,
        query: str,
        limit: int = 15,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search via search-service."""
        try:
            response = await self.http_client.post(
                f"{self.search_url}/api/v1/search/semantic",
                json={
                    "query": query,
                    "limit": limit,
                    "min_similarity": min_similarity,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            return []

    async def _get_intelligence_summary(self) -> Dict[str, Any]:
        """Get current intelligence summary (internal call, no auth required)."""
        try:
            response = await self.http_client.get(
                "http://localhost:8107/api/v1/intelligence/summary",
                params={"hours": 24}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Intelligence summary unavailable", error=str(e))
            return {"bursts": {"count": 0}, "momentum": {}, "contrarian": {}}


# Singleton instance
_context_service: Optional[IntelligenceContextService] = None


def get_intelligence_context_service() -> IntelligenceContextService:
    """Get singleton context service instance."""
    global _context_service
    if _context_service is None:
        _context_service = IntelligenceContextService()
    return _context_service
