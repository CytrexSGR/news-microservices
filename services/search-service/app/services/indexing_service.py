"""
Indexing service for syncing articles from Feed Service

Fetches articles via HTTP from Feed Service, but reads analysis data
directly from database for better performance and reduced coupling.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.models.search import ArticleIndex
from app.core.config import settings

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing articles"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_articles(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Sync articles from Feed Service.

        Args:
            batch_size: Number of articles to fetch per batch

        Returns:
            Dict with sync results
        """
        logger.info("Starting article sync...")

        # Get last indexed article timestamp
        stmt = select(func.max(ArticleIndex.indexed_at))
        result = await self.db.execute(stmt)
        last_indexed_at = result.scalar()

        # Fetch articles from Feed Service
        articles = await self._fetch_articles(last_indexed_at, batch_size)

        if not articles:
            logger.info("No new articles to index")
            return {'indexed': 0, 'updated': 0, 'errors': 0}

        # Index articles
        indexed_count = 0
        updated_count = 0
        error_count = 0

        for article in articles:
            try:
                await self._index_article(article)

                # Check if article exists
                stmt = select(ArticleIndex).where(
                    ArticleIndex.article_id == article['id']
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    updated_count += 1
                else:
                    indexed_count += 1

            except Exception as e:
                logger.error(f"Error indexing article {article.get('id')}: {e}")
                error_count += 1

        await self.db.commit()

        logger.info(f"Sync complete: {indexed_count} indexed, {updated_count} updated, {error_count} errors")

        return {
            'indexed': indexed_count,
            'updated': updated_count,
            'errors': error_count,
            'total': len(articles),
        }

    async def index_article(self, article_data: Dict[str, Any]) -> ArticleIndex:
        """
        Index a single article.

        Args:
            article_data: Article data

        Returns:
            ArticleIndex: Indexed article
        """
        return await self._index_article(article_data)

    async def reindex_all(self) -> Dict[str, Any]:
        """
        Reindex all articles.

        Returns:
            Dict with reindex results
        """
        logger.info("Starting full reindex...")

        # Delete existing indexes
        await self.db.execute(text("DELETE FROM article_indexes"))
        await self.db.commit()

        # Sync all articles
        total_indexed = 0
        total_errors = 0
        page = 1

        while True:
            articles = await self._fetch_articles(None, settings.BATCH_SIZE, page)

            if not articles:
                break

            for article in articles:
                try:
                    await self._index_article(article)
                    total_indexed += 1
                except Exception as e:
                    logger.error(f"Error indexing article {article.get('id')}: {e}")
                    total_errors += 1
                    # Rollback failed transaction to continue with next article
                    await self.db.rollback()

            try:
                await self.db.commit()
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                await self.db.rollback()

            page += 1

        logger.info(f"Reindex complete: {total_indexed} indexed, {total_errors} errors")

        return {
            'indexed': total_indexed,
            'errors': total_errors,
        }

    async def _index_article(self, article_data: Dict[str, Any]) -> ArticleIndex:
        """Index a single article with full-text search vector"""
        article_id = article_data.get('id')

        # Check if article exists
        stmt = select(ArticleIndex).where(ArticleIndex.article_id == article_id)
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()

        # Get sentiment and entities from database (not HTTP)
        sentiment, entities = await self._fetch_analysis_from_db(article_id)

        # Prepare data
        title = article_data.get('title', '')
        # Fallback chain: content -> description -> summary -> title (to satisfy NOT NULL)
        content = (
            article_data.get('content') or
            article_data.get('description') or
            article_data.get('summary') or
            title or
            ''  # Last resort
        )

        # Parse published_at from ISO string to datetime (naive, UTC)
        published_at = article_data.get('published_at')
        if published_at and isinstance(published_at, str):
            try:
                # Parse to timezone-aware then convert to naive UTC
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                published_at = dt.replace(tzinfo=None)  # Remove timezone info for DB
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse published_at: {published_at}")
                published_at = None

        if article:
            # Update existing
            article.title = title
            article.content = content
            article.author = article_data.get('author')
            article.source = article_data.get('source', article_data.get('feed_name'))
            article.url = article_data.get('url')
            article.published_at = published_at
            article.sentiment = sentiment
            article.entities = json.dumps(entities) if entities else None
            article.updated_at = datetime.utcnow()
        else:
            # Create new
            article = ArticleIndex(
                article_id=article_id,
                title=title,
                content=content,
                author=article_data.get('author'),
                source=article_data.get('source', article_data.get('feed_name')),
                url=article_data.get('url'),
                published_at=published_at,
                sentiment=sentiment,
                entities=json.dumps(entities) if entities else None,
            )
            self.db.add(article)

        # Update search vector
        await self.db.flush()

        # Create tsvector from title and content
        await self.db.execute(
            text("""
                UPDATE article_indexes
                SET search_vector = to_tsvector('english',
                    coalesce(title, '') || ' ' || coalesce(content, '')
                )
                WHERE article_id = :article_id
            """),
            {'article_id': article_id}
        )

        return article

    async def _fetch_articles(
        self,
        since: datetime = None,
        limit: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch articles from all feeds in Feed Service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First, get all feeds
                feeds_response = await client.get(
                    f"{settings.FEED_SERVICE_URL}/api/v1/feeds"
                )
                feeds_response.raise_for_status()
                feeds = feeds_response.json()

                # Collect articles from all feeds
                all_articles = []

                for feed in feeds:
                    feed_id = feed.get('id')
                    if not feed_id:
                        continue

                    try:
                        # Get items from this feed
                        items_response = await client.get(
                            f"{settings.FEED_SERVICE_URL}/api/v1/feeds/{feed_id}/items",
                            params={'page': page, 'limit': limit}
                        )
                        items_response.raise_for_status()
                        items = items_response.json()  # API returns list directly

                        # Add feed info to each item
                        if isinstance(items, list):
                            for item in items:
                                item['feed_name'] = feed.get('name')
                                item['feed_id'] = feed_id
                                # Use 'description' or 'content' as summary
                                if not item.get('summary') and item.get('description'):
                                    item['summary'] = item['description']
                                all_articles.append(item)

                    except Exception as e:
                        logger.warning(f"Error fetching items from feed {feed_id}: {e}")
                        continue

                # Filter by date if needed
                if since:
                    all_articles = [
                        art for art in all_articles
                        if art.get('published_at') and
                        datetime.fromisoformat(art['published_at'].replace('Z', '+00:00')) > since
                    ]

                return all_articles[:limit]

        except Exception as e:
            logger.error(f"Error fetching articles from Feed Service: {e}")
            return []

    async def _fetch_analysis_from_db(self, article_id: str) -> tuple[Optional[str], Optional[list]]:
        """
        Fetch analysis data directly from database.

        Reads from public.article_analysis (unified table) which contains
        triage_results (category, priority_score) and tier1_results (entities, sentiment).

        Args:
            article_id: Article UUID

        Returns:
            Tuple of (sentiment, entities) where:
            - sentiment: Category from triage_results (e.g., PANORAMA, CRYPTO, etc.)
            - entities: Extracted entities list from tier1_results
        """
        try:
            # Query from unified article_analysis table
            query = text("""
                SELECT
                    triage_results,
                    tier1_results
                FROM public.article_analysis
                WHERE article_id = :article_id
                  AND success = true
                ORDER BY created_at DESC
                LIMIT 1
            """)

            result = await self.db.execute(query, {"article_id": str(article_id)})
            row = result.fetchone()

            if not row:
                logger.debug(f"No analysis found for article {article_id}")
                return None, None

            triage_results, tier1_results = row

            # Extract category from triage_results as sentiment
            sentiment = None
            if triage_results and isinstance(triage_results, dict):
                category = triage_results.get('category', '')
                sentiment = category.lower() if category else None

            # Extract entities from tier1_results
            entities = []
            if tier1_results and isinstance(tier1_results, dict):
                entities_data = tier1_results.get('entities', [])
                if isinstance(entities_data, list):
                    # Extract just entity text for simple list
                    entities = [e.get('text', '') for e in entities_data if isinstance(e, dict)]

            return sentiment, entities

        except Exception as e:
            logger.error(f"Error fetching analysis from DB for article {article_id}: {e}")
            return None, None
