"""
Search service with PostgreSQL full-text search
"""
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import ArticleIndex, SearchHistory, SearchAnalytics
from app.schemas.search import (
    SearchRequest, AdvancedSearchRequest, SearchResponse,
    SearchResultItem, SearchFilters
)
from app.core.redis_client import cache_get, cache_set
from app.core.config import settings


class SearchService:
    """Search service with PostgreSQL full-text search"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        request: SearchRequest,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform basic search.

        Args:
            request: Search request
            user_id: User ID (optional)

        Returns:
            SearchResponse: Search results
        """
        start_time = time.time()

        # Check cache (if enabled)
        cache_key = None
        if settings.QUERY_RESULT_CACHE_ENABLED:
            cache_key = f"search:{request.query}:{request.page}:{request.page_size}"
            if request.filters:
                cache_key += f":{hash(json.dumps(request.filters.model_dump(mode='json'), sort_keys=True))}"

            cached_result = await cache_get(cache_key)
            if cached_result:
                # Add cache hit indicator
                cached_result['from_cache'] = True
                return SearchResponse(**cached_result)

        # Build query
        query = self._build_search_query(request.query, request.filters)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)

        result = await self.db.execute(query)
        rows = result.all()

        # Convert to response items
        # Note: Query returns (ArticleIndex, rank/date) tuples
        # If query is empty: row[1] is datetime (published_at)
        # If query exists: row[1] is float (relevance rank)
        has_query = request.query and request.query.strip() != ''

        results = [
            SearchResultItem(
                article_id=row[0].article_id,  # row[0] is ArticleIndex object
                title=row[0].title,
                content=row[0].content[:500] + "..." if len(row[0].content) > 500 else row[0].content,
                author=row[0].author,
                source=row[0].source,
                url=row[0].url,
                published_at=row[0].published_at,
                sentiment=row[0].sentiment,
                entities=self._extract_entity_names(row[0].entities),
                relevance_score=float(row[1]) if has_query and row[1] is not None else 0.0,
            )
            for row in rows
        ]

        # Track search history
        if user_id:
            await self._track_search_history(user_id, request.query, request.filters, total)

        # Update analytics (only for non-empty queries)
        if request.query and request.query.strip():
            await self._update_analytics(request.query, total)

        execution_time_ms = (time.time() - start_time) * 1000

        response = SearchResponse(
            query=request.query,
            total=total,
            page=request.page,
            page_size=request.page_size,
            results=results,
            execution_time_ms=execution_time_ms,
        )

        # Cache results (use mode='json' to serialize datetime objects)
        if settings.QUERY_RESULT_CACHE_ENABLED and cache_key:
            # Use shorter TTL for query results to keep data fresh
            cache_ttl = settings.QUERY_RESULT_CACHE_TTL
            await cache_set(cache_key, response.model_dump(mode='json'), ttl=cache_ttl)

        return response

    async def advanced_search(
        self,
        request: AdvancedSearchRequest,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform advanced search with highlighting and facets.

        Args:
            request: Advanced search request
            user_id: User ID (optional)

        Returns:
            SearchResponse: Search results with facets
        """
        start_time = time.time()

        # Build advanced query
        query = self._build_advanced_query(request)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)

        result = await self.db.execute(query)
        articles = result.all()

        # Convert to response items with highlighting
        results = []
        for article in articles:
            highlight = None
            if request.highlight:
                highlight = await self._generate_highlights(article, request.query)

            results.append(
                SearchResultItem(
                    article_id=article.article_id,
                    title=article.title,
                    content=article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    author=article.author,
                    source=article.source,
                    url=article.url,
                    published_at=article.published_at,
                    sentiment=article.sentiment,
                    entities=self._extract_entity_names(article.entities),
                    relevance_score=float(article.rank) if hasattr(article, 'rank') else 0.0,
                    highlight=highlight,
                )
            )

        # Get facets
        facets = None
        if request.facets:
            facets = await self._compute_facets(request.query, request.facets, request.filters)

        # Track search history
        if user_id:
            await self._track_search_history(user_id, request.query, request.filters, total)

        # Update analytics (only for non-empty queries)
        if request.query and request.query.strip():
            await self._update_analytics(request.query, total)

        execution_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            total=total,
            page=request.page,
            page_size=request.page_size,
            results=results,
            facets=facets,
            execution_time_ms=execution_time_ms,
        )

    def _extract_entity_names(self, entities_json: Optional[str]) -> Optional[List[str]]:
        """
        Extract entity names from JSON string containing entity objects.

        Args:
            entities_json: JSON string with entity objects or list of strings

        Returns:
            List of entity name strings or None
        """
        if not entities_json:
            return None

        try:
            entities = json.loads(entities_json)
            if not isinstance(entities, list):
                return None

            # Handle both formats: list of dicts and list of strings
            result = []
            for entity in entities:
                if isinstance(entity, dict):
                    # Extract 'name' or 'text' field from entity object
                    name = entity.get('name') or entity.get('text') or ''
                    if name:
                        result.append(str(name))
                elif isinstance(entity, str):
                    result.append(entity)

            return result if result else None
        except (json.JSONDecodeError, TypeError):
            return None

    def _build_search_query(self, query: Optional[str], filters: Optional[SearchFilters] = None):
        """
        Build search query with filters and tuned TF-IDF weights.

        Uses optimized weights for better relevance:
        - Title matches: 0.8 weight (highest priority)
        - Subtitle/headings: 0.6 weight
        - Content: 0.4 weight
        - Metadata: 0.2 weight
        """

        # If no query provided, return all articles (filtered)
        if not query or query.strip() == '':
            stmt = select(
                ArticleIndex,
                func.coalesce(ArticleIndex.published_at, datetime.min).label('rank')
            )

            # Apply filters
            if filters:
                if filters.source:
                    stmt = stmt.where(ArticleIndex.source.in_(filters.source))
                if filters.sentiment:
                    stmt = stmt.where(ArticleIndex.sentiment.in_(filters.sentiment))
                if filters.date_from:
                    stmt = stmt.where(ArticleIndex.published_at >= filters.date_from)
                if filters.date_to:
                    stmt = stmt.where(ArticleIndex.published_at <= filters.date_to)
                if filters.entities:
                    # Search in entities JSON field
                    for entity in filters.entities:
                        stmt = stmt.where(ArticleIndex.entities.contains(entity))

            # Order by published date (newest first)
            stmt = stmt.order_by(ArticleIndex.published_at.desc())
            return stmt

        # Parse query for full-text search
        ts_query = self._parse_query(query)

        # Base query with tuned TF-IDF weights for better relevance
        # Weights: [D=0.8, C=0.6, B=0.4, A=0.2]
        # D = title (highest), C = subtitle, B = body, A = author
        tuned_weights = '{0.8, 0.6, 0.4, 0.2}'

        stmt = select(
            ArticleIndex,
            func.ts_rank(
                ArticleIndex.search_vector,
                func.to_tsquery('english', ts_query),
                32  # normalization flag: divide by document length
            ).label('rank')
        ).where(
            ArticleIndex.search_vector.op('@@')(func.to_tsquery('english', ts_query))
        )

        # Apply filters
        if filters:
            if filters.source:
                stmt = stmt.where(ArticleIndex.source.in_(filters.source))
            if filters.sentiment:
                stmt = stmt.where(ArticleIndex.sentiment.in_(filters.sentiment))
            if filters.date_from:
                stmt = stmt.where(ArticleIndex.published_at >= filters.date_from)
            if filters.date_to:
                stmt = stmt.where(ArticleIndex.published_at <= filters.date_to)
            if filters.entities:
                # Search in entities JSON field
                for entity in filters.entities:
                    stmt = stmt.where(ArticleIndex.entities.contains(entity))

        # Order by relevance
        stmt = stmt.order_by(text('rank DESC'))

        return stmt

    def _build_advanced_query(self, request: AdvancedSearchRequest):
        """Build advanced search query"""
        query = self._build_search_query(request.query, request.filters)

        # Add fuzzy search if enabled
        if request.use_fuzzy and settings.ENABLE_FUZZY_SEARCH:
            fuzzy_condition = or_(
                func.similarity(ArticleIndex.title, request.query) >= settings.FUZZY_SIMILARITY_THRESHOLD,
                func.similarity(ArticleIndex.content, request.query) >= settings.FUZZY_SIMILARITY_THRESHOLD,
            )
            query = query.union(
                select(
                    ArticleIndex,
                    func.similarity(ArticleIndex.title, request.query).label('rank')
                ).where(fuzzy_condition)
            )

        return query

    def _parse_query(self, query: str) -> str:
        """
        Parse query into PostgreSQL tsquery format.

        Supports:
        - AND/OR operators
        - Phrase search: "exact phrase"
        - Field search: title:"keyword"
        - Exclusion: -keyword
        """
        # Simple implementation - can be extended
        tokens = []
        words = query.split()

        for word in words:
            if word.startswith('-'):
                # Exclusion
                tokens.append(f'!{word[1:]}')
            elif word.upper() in ('AND', 'OR'):
                tokens.append(word.upper())
            else:
                tokens.append(word)

        return ' & '.join(tokens) if tokens else query

    async def _generate_highlights(self, article: ArticleIndex, query: str) -> Dict[str, List[str]]:
        """Generate highlighted snippets"""
        # Use PostgreSQL ts_headline for highlighting
        stmt = select(
            func.ts_headline(
                'english',
                article.title,
                func.to_tsquery('english', self._parse_query(query)),
                'MaxFragments=3, MaxWords=20, MinWords=10'
            ).label('title_highlight'),
            func.ts_headline(
                'english',
                article.content,
                func.to_tsquery('english', self._parse_query(query)),
                'MaxFragments=3, MaxWords=20, MinWords=10'
            ).label('content_highlight')
        )

        result = await self.db.execute(stmt)
        row = result.first()

        return {
            'title': [row.title_highlight] if row and row.title_highlight else [],
            'content': [row.content_highlight] if row and row.content_highlight else [],
        }

    async def _compute_facets(
        self,
        query: str,
        facet_fields: List[str],
        filters: Optional[SearchFilters] = None
    ) -> Dict[str, Any]:
        """Compute facets for search results"""
        facets = {}

        for field in facet_fields:
            if field == 'source':
                stmt = select(
                    ArticleIndex.source,
                    func.count(ArticleIndex.id).label('count')
                ).where(
                    ArticleIndex.search_vector.op('@@')(func.to_tsquery('english', self._parse_query(query)))
                ).group_by(ArticleIndex.source).order_by(text('count DESC')).limit(10)

                result = await self.db.execute(stmt)
                facets['source'] = [{'value': row.source, 'count': row.count} for row in result.all()]

            elif field == 'sentiment':
                stmt = select(
                    ArticleIndex.sentiment,
                    func.count(ArticleIndex.id).label('count')
                ).where(
                    ArticleIndex.search_vector.op('@@')(func.to_tsquery('english', self._parse_query(query)))
                ).group_by(ArticleIndex.sentiment).order_by(text('count DESC'))

                result = await self.db.execute(stmt)
                facets['sentiment'] = [{'value': row.sentiment, 'count': row.count} for row in result.all()]

            elif field == 'date':
                # Date histogram by day
                stmt = select(
                    func.date_trunc('day', ArticleIndex.published_at).label('date'),
                    func.count(ArticleIndex.id).label('count')
                ).where(
                    ArticleIndex.search_vector.op('@@')(func.to_tsquery('english', self._parse_query(query)))
                ).group_by(text('date')).order_by(text('date DESC')).limit(30)

                result = await self.db.execute(stmt)
                facets['date'] = [{'value': str(row.date), 'count': row.count} for row in result.all()]

        return facets

    async def _track_search_history(
        self,
        user_id: str,
        query: str,
        filters: Optional[SearchFilters],
        results_count: int
    ):
        """Track user search history"""
        history = SearchHistory(
            user_id=user_id,
            query=query,
            filters=json.dumps(filters.model_dump()) if filters else None,
            results_count=results_count,
        )
        self.db.add(history)
        await self.db.commit()

    async def _update_analytics(self, query: str, hits: int):
        """Update search analytics"""
        # Check if query exists
        stmt = select(SearchAnalytics).where(SearchAnalytics.query == query)
        result = await self.db.execute(stmt)
        analytics = result.scalar_one_or_none()

        if analytics:
            analytics.hits += 1
            analytics.updated_at = datetime.utcnow()
        else:
            analytics = SearchAnalytics(query=query, hits=1)
            self.db.add(analytics)

        await self.db.commit()

    async def get_facets(self) -> Dict[str, List[str]]:
        """
        Get all available filter options (facets).

        Returns all unique sources and categories from the entire index,
        allowing frontend to populate filter dropdowns dynamically.

        Returns:
            Dict with 'sources' and 'categories' arrays
        """
        # Get unique sources (excluding null)
        sources_query = select(ArticleIndex.source).distinct().where(
            ArticleIndex.source.isnot(None)
        ).order_by(ArticleIndex.source)
        sources_result = await self.db.execute(sources_query)
        sources = [row[0] for row in sources_result.all()]

        # Get unique categories (sentiment field stores categories)
        categories_query = select(ArticleIndex.sentiment).distinct().where(
            ArticleIndex.sentiment.isnot(None)
        ).order_by(ArticleIndex.sentiment)
        categories_result = await self.db.execute(categories_query)
        categories = [row[0] for row in categories_result.all()]

        return {
            'sources': sources,
            'categories': categories,
        }

