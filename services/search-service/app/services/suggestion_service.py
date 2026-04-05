"""
Suggestion service for autocomplete and query suggestions
"""
import logging
from typing import List
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import SearchAnalytics, ArticleIndex, SearchHistory
from app.core.redis_client import cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for generating search suggestions"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get autocomplete suggestions.

        Args:
            query: Partial query string
            limit: Maximum number of suggestions

        Returns:
            List[str]: List of suggested queries
        """
        # Check cache
        cache_key = f"suggestions:{query}:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        suggestions = []

        # Get suggestions from popular queries
        popular_suggestions = await self._get_popular_suggestions(query, limit)
        suggestions.extend(popular_suggestions)

        # Get suggestions from article titles
        if len(suggestions) < limit:
            title_suggestions = await self._get_title_suggestions(query, limit - len(suggestions))
            suggestions.extend(title_suggestions)

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                seen.add(suggestion.lower())
                unique_suggestions.append(suggestion)

        # Limit results
        unique_suggestions = unique_suggestions[:limit]

        # Cache results
        await cache_set(cache_key, unique_suggestions, ttl=3600)

        return unique_suggestions

    async def get_related_searches(self, query: str, limit: int = 5) -> List[str]:
        """
        Get related searches based on query.

        Args:
            query: Current query
            limit: Maximum number of related searches

        Returns:
            List[str]: List of related queries
        """
        # Check cache
        cache_key = f"related:{query}:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        # Get similar queries from search history
        stmt = select(SearchAnalytics.query).where(
            and_(
                SearchAnalytics.query != query,
                or_(
                    func.similarity(SearchAnalytics.query, query) > 0.3,
                    SearchAnalytics.query.ilike(f'%{query}%')
                )
            )
        ).order_by(SearchAnalytics.hits.desc()).limit(limit)

        result = await self.db.execute(stmt)
        related = [row.query for row in result.all()]

        # Cache results
        await cache_set(cache_key, related, ttl=3600)

        return related

    async def get_popular_queries(self, limit: int = 10) -> List[dict]:
        """
        Get most popular search queries.

        Args:
            limit: Maximum number of queries

        Returns:
            List[dict]: List of popular queries with hit counts
        """
        # Check cache
        cache_key = f"popular_queries:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        stmt = select(
            SearchAnalytics.query,
            SearchAnalytics.hits
        ).order_by(
            SearchAnalytics.hits.desc()
        ).limit(limit)

        result = await self.db.execute(stmt)
        popular = [
            {'query': row.query, 'hits': row.hits}
            for row in result.all()
        ]

        # Cache results
        await cache_set(cache_key, popular, ttl=1800)

        return popular

    async def _get_popular_suggestions(self, query: str, limit: int) -> List[str]:
        """Get suggestions from popular searches"""
        stmt = select(SearchAnalytics.query).where(
            SearchAnalytics.query.ilike(f'{query}%')
        ).order_by(
            SearchAnalytics.hits.desc()
        ).limit(limit)

        result = await self.db.execute(stmt)
        return [row.query for row in result.all()]

    async def _get_title_suggestions(self, query: str, limit: int) -> List[str]:
        """Get suggestions from article titles using trigram similarity"""
        if not settings.ENABLE_FUZZY_SEARCH:
            return []

        stmt = select(ArticleIndex.title).where(
            func.similarity(ArticleIndex.title, query) > settings.FUZZY_SIMILARITY_THRESHOLD
        ).order_by(
            func.similarity(ArticleIndex.title, query).desc()
        ).limit(limit)

        result = await self.db.execute(stmt)
        return [row.title for row in result.all() if row.title]
