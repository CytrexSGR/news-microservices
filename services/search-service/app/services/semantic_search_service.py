"""
Semantic Search Service (Layer 1)

Provides vector-based semantic search using:
- OpenAI embeddings for query vectorization
- pgvector for similarity search on article_analysis.embedding
- HDBSCAN for result clustering

Usage:
    service = SemanticSearchService(db)
    results = await service.search(SemanticSearchRequest(query="market volatility"))
"""

import logging
import time
from typing import List, Optional, Dict, Any
import json

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.embedding_service import get_embedding_service
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    SemanticSearchCluster,
)

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantic search service using vector similarity.

    Searches article_analysis.embedding using pgvector cosine similarity,
    then optionally clusters results using HDBSCAN.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = get_embedding_service()

    async def search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        """
        Execute semantic search.

        Args:
            request: Semantic search request

        Returns:
            SemanticSearchResponse with results and optional clusters
        """
        start_time = time.time()

        # Check if embedding service is available
        if not self.embedding_service.is_available():
            logger.warning("Semantic search unavailable - no embedding service")
            return SemanticSearchResponse(
                query=request.query,
                total=0,
                results=[],
                clusters=None,
                embedding_available=False,
                execution_time_ms=0,
            )

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(request.query)

        if query_embedding is None:
            logger.error("Failed to generate query embedding")
            return SemanticSearchResponse(
                query=request.query,
                total=0,
                results=[],
                clusters=None,
                embedding_available=True,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Execute pgvector similarity search
        results = await self._vector_search(
            query_embedding=query_embedding,
            limit=request.limit,
            min_similarity=request.min_similarity,
            filters=request.filters,
        )

        # Cluster results if requested
        clusters = None
        if request.cluster_results and len(results) >= settings.HDBSCAN_MIN_CLUSTER_SIZE:
            clusters = await self._cluster_results(results, query_embedding)

        execution_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Semantic search completed: query='{request.query[:50]}...', "
            f"results={len(results)}, clusters={len(clusters) if clusters else 0}, "
            f"time={execution_time_ms:.1f}ms"
        )

        return SemanticSearchResponse(
            query=request.query,
            total=len(results),
            results=results,
            clusters=clusters,
            embedding_available=True,
            execution_time_ms=execution_time_ms,
        )

    async def _vector_search(
        self,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        filters: Optional[Any] = None,
    ) -> List[SemanticSearchResultItem]:
        """
        Execute pgvector similarity search on article_analysis table.

        Uses cosine distance operator (<=>).
        """
        # Build filter conditions
        filter_conditions = []
        filter_params: Dict[str, Any] = {
            "min_similarity": min_similarity,
            "limit": limit,
        }

        if filters:
            if filters.source:
                filter_conditions.append("ai.source = ANY(:sources)")
                filter_params["sources"] = filters.source
            if filters.sentiment:
                filter_conditions.append("ai.sentiment = ANY(:sentiments)")
                filter_params["sentiments"] = filters.sentiment
            if filters.date_from:
                filter_conditions.append("ai.published_at >= :date_from")
                filter_params["date_from"] = filters.date_from
            if filters.date_to:
                filter_conditions.append("ai.published_at <= :date_to")
                filter_params["date_to"] = filters.date_to

        where_clause = " AND ".join(filter_conditions) if filter_conditions else "1=1"

        # Format embedding as pgvector literal (safe: only floats)
        embedding_str = "[" + ",".join(str(f) for f in query_embedding) + "]"

        # Query article_analysis with embedding similarity
        # Note: article_analysis.embedding is the stored article embedding
        # We join with article_indexes to get full article data
        # Embedding is embedded directly as a literal since asyncpg doesn't handle ::vector cast
        query = text(f"""
            SELECT
                aa.article_id::text,
                COALESCE(ai.title, fi.title, aa.article_id::text) as title,
                COALESCE(ai.content, fi.content, fi.description, '') as content,
                COALESCE(ai.author, fi.author) as author,
                ai.source,
                COALESCE(ai.url, fi.link) as url,
                COALESCE(ai.published_at, fi.published_at) as published_at,
                ai.sentiment,
                ai.entities,
                1 - (aa.embedding <=> '{embedding_str}'::vector) as similarity,
                aa.embedding as article_embedding
            FROM public.article_analysis aa
            LEFT JOIN public.article_indexes ai ON aa.article_id::text = ai.article_id
            LEFT JOIN public.feed_items fi ON aa.article_id = fi.id
            WHERE aa.embedding IS NOT NULL
              AND aa.success = true
              AND 1 - (aa.embedding <=> '{embedding_str}'::vector) >= :min_similarity
              AND {where_clause}
            ORDER BY aa.embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(query, filter_params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Vector search query failed: {e}")
            return []

        # Convert to result items
        items = []
        for row in rows:
            # Parse entities from JSON string if present
            entities = None
            if row.entities:
                try:
                    entities = json.loads(row.entities) if isinstance(row.entities, str) else row.entities
                except (json.JSONDecodeError, TypeError):
                    entities = None

            items.append(SemanticSearchResultItem(
                article_id=row.article_id,
                title=row.title or "Untitled",
                content=row.content[:500] if row.content else "",
                author=row.author,
                source=row.source,
                url=row.url,
                published_at=row.published_at,
                sentiment=row.sentiment,
                entities=entities if isinstance(entities, list) else None,
                similarity=float(row.similarity),
                cluster_id=None,
            ))

        return items

    async def _cluster_results(
        self,
        results: List[SemanticSearchResultItem],
        query_embedding: List[float],
    ) -> Optional[List[SemanticSearchCluster]]:
        """
        Cluster search results using HDBSCAN.

        Groups semantically similar results together.
        """
        if len(results) < settings.HDBSCAN_MIN_CLUSTER_SIZE:
            return None

        try:
            import hdbscan
        except ImportError:
            logger.warning("HDBSCAN not available - skipping clustering")
            return None

        # Re-fetch embeddings for clustering (we need the vectors)
        article_ids = [r.article_id for r in results]

        query = text("""
            SELECT article_id::text, embedding
            FROM public.article_analysis
            WHERE article_id::text = ANY(:article_ids)
              AND embedding IS NOT NULL
        """)

        try:
            result = await self.db.execute(query, {"article_ids": article_ids})
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch embeddings for clustering: {e}")
            return None

        # Build embedding matrix
        embedding_map = {str(row.article_id): row.embedding for row in rows}
        embeddings = []
        valid_results = []

        for r in results:
            if r.article_id in embedding_map:
                emb = embedding_map[r.article_id]
                if emb is not None:
                    # Parse pgvector string format: "[0.123,0.456,...]"
                    if isinstance(emb, str):
                        try:
                            emb = json.loads(emb)
                        except json.JSONDecodeError:
                            continue
                    embeddings.append(emb)
                    valid_results.append(r)

        if len(embeddings) < settings.HDBSCAN_MIN_CLUSTER_SIZE:
            return None

        # Convert to numpy array
        try:
            X = np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed to create embedding matrix: {e}")
            return None

        # Run HDBSCAN clustering
        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
                min_samples=settings.HDBSCAN_MIN_SAMPLES,
                metric="euclidean",
                cluster_selection_method="eom",
            )
            cluster_labels = clusterer.fit_predict(X)
        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return None

        # Assign cluster IDs to results
        for i, r in enumerate(valid_results):
            r.cluster_id = int(cluster_labels[i]) if cluster_labels[i] >= 0 else -1

        # Group results by cluster
        cluster_map: Dict[int, List[SemanticSearchResultItem]] = {}
        for r in valid_results:
            if r.cluster_id >= 0:  # Ignore noise points (-1)
                if r.cluster_id not in cluster_map:
                    cluster_map[r.cluster_id] = []
                cluster_map[r.cluster_id].append(r)

        # Build cluster response objects
        clusters = []
        for cluster_id, articles in sorted(cluster_map.items()):
            # Find representative (highest similarity)
            representative = max(articles, key=lambda a: a.similarity)
            avg_similarity = sum(a.similarity for a in articles) / len(articles)

            clusters.append(SemanticSearchCluster(
                cluster_id=cluster_id,
                size=len(articles),
                representative_title=representative.title,
                avg_similarity=avg_similarity,
                articles=sorted(articles, key=lambda a: -a.similarity),
            ))

        # Sort clusters by average similarity
        clusters.sort(key=lambda c: -c.avg_similarity)

        logger.info(f"Clustered {len(valid_results)} results into {len(clusters)} clusters")

        return clusters if clusters else None
