"""Repository for batch cluster database operations.

This module provides database operations for batch-computed UMAP+HDBSCAN clusters,
including listing, searching, similarity lookups, and feedback handling.

The repository follows the same patterns as ClusterRepository but operates on
the batch clustering tables (batch_clusters, batch_article_clusters, cluster_batches).

Key features:
- Batch versioning: Operations work on the latest completed batch by default
- pgvector similarity search: Uses <=> operator for centroid-based lookup
- Keyword search: Finds clusters by article title matching
- Feedback collection: Stores user corrections for learning

Note: For vector operations, raw SQL with text() is used since SQLAlchemy
doesn't directly support pgvector operations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch_cluster import (
    BatchArticleCluster,
    BatchCluster,
    ClusterBatch,
    ClusterFeedback,
)

logger = logging.getLogger(__name__)


class BatchClusterRepository:
    """Repository for batch-computed cluster operations.

    This repository provides database operations for topic clusters computed
    via periodic UMAP+HDBSCAN batch runs. It differs from ClusterRepository
    (real-time single-pass clustering) in that:

    1. Clusters are versioned by batch_id
    2. Centroids are stored as pgvector for efficient similarity search
    3. Operations default to the latest completed batch
    4. Supports keyword search and feedback collection
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def get_latest_batch_id(self) -> Optional[UUID]:
        """
        Get the most recent completed batch ID.

        Returns:
            UUID of latest completed batch, or None if no batches exist
        """
        query = (
            select(ClusterBatch.batch_id)
            .where(ClusterBatch.status == "completed")
            .order_by(ClusterBatch.completed_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        batch_id = result.scalar_one_or_none()

        if batch_id is None:
            logger.debug("No completed batch found")

        return batch_id

    async def list_clusters(
        self,
        batch_id: Optional[UUID] = None,
        min_size: int = 10,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[BatchCluster], int]:
        """
        List clusters from a batch with pagination.

        Args:
            batch_id: Specific batch to query (defaults to latest completed)
            min_size: Minimum article count to include
            limit: Maximum clusters to return
            offset: Pagination offset

        Returns:
            Tuple of (clusters, total_count)
        """
        if batch_id is None:
            batch_id = await self.get_latest_batch_id()
            if batch_id is None:
                return [], 0

        # Build base query
        base_query = (
            select(BatchCluster)
            .where(BatchCluster.batch_id == batch_id)
            .where(BatchCluster.article_count >= min_size)
        )

        # Count total matching clusters
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated data sorted by article count
        data_query = (
            base_query
            .order_by(BatchCluster.article_count.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(data_query)
        clusters = list(result.scalars().all())

        logger.debug(
            f"Listed {len(clusters)}/{total} clusters from batch {batch_id} "
            f"(min_size={min_size}, limit={limit}, offset={offset})"
        )

        return clusters, total

    async def get_cluster_by_id(self, cluster_id: int) -> Optional[BatchCluster]:
        """
        Get a single cluster by ID.

        Args:
            cluster_id: Primary key of the cluster

        Returns:
            BatchCluster or None if not found
        """
        query = select(BatchCluster).where(BatchCluster.id == cluster_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_clusters_by_keyword(
        self,
        keywords: List[str],
        batch_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Find clusters containing articles with matching keywords.

        Searches article titles in batch_article_clusters joined with feed_items.
        Returns clusters ranked by number of matching articles.

        Args:
            keywords: List of keywords to search for (case-insensitive)
            batch_id: Specific batch to search (defaults to latest completed)
            limit: Maximum results to return

        Returns:
            List of dicts with cluster_id, label, article_count, keywords, match_count
        """
        if batch_id is None:
            batch_id = await self.get_latest_batch_id()
            if batch_id is None:
                return []

        if not keywords:
            return []

        # Build LIKE patterns for case-insensitive matching
        patterns = [f"%{kw.lower()}%" for kw in keywords if kw.strip()]

        if not patterns:
            return []

        # Raw SQL for complex join with LIKE ANY
        # PostgreSQL array comparison for multiple patterns
        query = text("""
            SELECT
                bc.id as cluster_id,
                bc.label,
                bc.article_count,
                bc.keywords,
                COUNT(*) as match_count
            FROM batch_article_clusters bac
            JOIN feed_items fi ON bac.article_id = fi.id
            JOIN batch_clusters bc ON bac.cluster_id = bc.id
            WHERE bac.batch_id = :batch_id
              AND LOWER(fi.title) LIKE ANY(:patterns)
            GROUP BY bc.id, bc.label, bc.article_count, bc.keywords
            ORDER BY match_count DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {
                "batch_id": str(batch_id),
                "patterns": patterns,
                "limit": limit,
            }
        )

        results = [
            {
                "cluster_id": row.cluster_id,
                "label": row.label,
                "article_count": row.article_count,
                "keywords": row.keywords,
                "match_count": row.match_count,
            }
            for row in result
        ]

        logger.debug(
            f"Keyword search for {keywords} found {len(results)} clusters "
            f"in batch {batch_id}"
        )

        return results

    async def get_cluster_articles(
        self,
        cluster_id: int,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get sample articles from a cluster.

        Articles are sorted by distance to centroid (most representative first).

        Args:
            cluster_id: ID of the cluster
            limit: Maximum articles to return

        Returns:
            List of dicts with article_id, title, url, distance, assigned_at
        """
        query = text("""
            SELECT
                fi.id as article_id,
                fi.title,
                fi.link as url,
                fi.published_at,
                bac.distance_to_centroid,
                bac.assigned_at
            FROM batch_article_clusters bac
            JOIN feed_items fi ON bac.article_id = fi.id
            WHERE bac.cluster_id = :cluster_id
            ORDER BY bac.distance_to_centroid ASC NULLS LAST
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {"cluster_id": cluster_id, "limit": limit}
        )

        return [
            {
                "article_id": str(row.article_id),
                "title": row.title,
                "url": row.url,
                "distance": row.distance_to_centroid,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
            }
            for row in result
        ]

    async def find_similar_clusters(
        self,
        embedding: List[float],
        batch_id: Optional[UUID] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find clusters with centroids similar to given embedding.

        Uses pgvector's <=> operator (cosine distance) on centroid_vec column.
        Similarity is computed as 1 - distance.

        Args:
            embedding: 1536-dimensional embedding vector
            batch_id: Specific batch to search (defaults to latest completed)
            limit: Maximum clusters to return

        Returns:
            List of dicts with cluster_id, label, article_count, keywords, similarity
        """
        if batch_id is None:
            batch_id = await self.get_latest_batch_id()
            if batch_id is None:
                return []

        # Format embedding as pgvector string
        emb_str = "[" + ",".join(str(f) for f in embedding) + "]"

        # pgvector cosine distance: <=> returns distance, similarity = 1 - distance
        # Note: We embed the vector directly in SQL since asyncpg has issues with
        # parameterized pgvector queries through SQLAlchemy
        query = text(f"""
            SELECT
                id,
                label,
                article_count,
                keywords,
                1 - (centroid_vec <=> '{emb_str}'::vector) as similarity
            FROM batch_clusters
            WHERE batch_id = :batch_id
              AND centroid_vec IS NOT NULL
            ORDER BY centroid_vec <=> '{emb_str}'::vector
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {
                "batch_id": str(batch_id),
                "limit": limit,
            }
        )

        results = [
            {
                "cluster_id": row.id,
                "label": row.label,
                "article_count": row.article_count,
                "keywords": row.keywords,
                "similarity": float(row.similarity) if row.similarity else 0.0,
            }
            for row in result
        ]

        logger.debug(
            f"Found {len(results)} similar clusters in batch {batch_id}"
        )

        return results

    async def search_clusters_semantic(
        self,
        query_embedding: List[float],
        batch_id: Optional[UUID] = None,
        limit: int = 20,
        min_similarity: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Search clusters by embedding similarity with minimum threshold.

        Uses pgvector cosine similarity on centroid_vec.
        Filters results below min_similarity threshold.

        Args:
            query_embedding: 1536-dimensional embedding vector from search query
            batch_id: Specific batch to search (defaults to latest completed)
            limit: Maximum clusters to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of dicts with cluster_id, label, article_count, keywords, similarity
            Sorted by similarity (highest first)
        """
        if batch_id is None:
            batch_id = await self.get_latest_batch_id()
            if batch_id is None:
                return []

        # Format embedding as pgvector string
        emb_str = "[" + ",".join(str(f) for f in query_embedding) + "]"

        # pgvector cosine distance: <=> returns distance, similarity = 1 - distance
        # Filter by minimum similarity threshold
        query = text(f"""
            SELECT
                id,
                label,
                article_count,
                keywords,
                1 - (centroid_vec <=> '{emb_str}'::vector) as similarity
            FROM batch_clusters
            WHERE batch_id = :batch_id
              AND centroid_vec IS NOT NULL
              AND (1 - (centroid_vec <=> '{emb_str}'::vector)) >= :min_similarity
            ORDER BY centroid_vec <=> '{emb_str}'::vector
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {
                "batch_id": str(batch_id),
                "limit": limit,
                "min_similarity": min_similarity,
            }
        )

        results = [
            {
                "cluster_id": row.id,
                "label": row.label,
                "article_count": row.article_count,
                "keywords": row.keywords,
                "similarity": float(row.similarity) if row.similarity else 0.0,
            }
            for row in result
        ]

        logger.info(
            f"Semantic search found {len(results)} clusters "
            f"(min_similarity={min_similarity}, batch={batch_id})"
        )

        return results

    async def get_article_cluster(self, article_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the cluster for a specific article.

        Returns cluster info from the latest batch assignment.

        Args:
            article_id: UUID of the article

        Returns:
            Dict with cluster_id, label, article_count, keywords, distance
            or None if article not in any cluster
        """
        query = text("""
            SELECT
                bc.id as cluster_id,
                bc.label,
                bc.article_count,
                bc.keywords,
                bac.distance_to_centroid,
                bac.batch_id
            FROM batch_article_clusters bac
            JOIN batch_clusters bc ON bac.cluster_id = bc.id
            WHERE bac.article_id = :article_id
            ORDER BY bac.assigned_at DESC
            LIMIT 1
        """)

        result = await self.session.execute(
            query,
            {"article_id": str(article_id)}
        )
        row = result.first()

        if row is None:
            logger.debug(f"Article {article_id} not found in any batch cluster")
            return None

        return {
            "cluster_id": row.cluster_id,
            "label": row.label,
            "article_count": row.article_count,
            "keywords": row.keywords,
            "distance": row.distance_to_centroid,
            "batch_id": str(row.batch_id),
        }

    async def submit_feedback(
        self,
        cluster_id: int,
        feedback_type: str,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        created_by: Optional[str] = None,
    ) -> int:
        """
        Submit feedback for a cluster.

        Feedback types:
        - label_correction: User corrected the cluster label
        - merge: User suggested merging with another cluster
        - split: User suggested splitting the cluster
        - quality_rating: User rated cluster quality

        Args:
            cluster_id: ID of the cluster
            feedback_type: Type of feedback (label_correction, merge, split, etc.)
            old_value: Previous value being corrected (JSONB)
            new_value: New corrected value (JSONB)
            created_by: User identifier who submitted feedback

        Returns:
            ID of the created feedback record
        """
        feedback = ClusterFeedback(
            cluster_id=cluster_id,
            feedback_type=feedback_type,
            old_value=old_value,
            new_value=new_value,
            created_by=created_by,
        )

        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)

        logger.info(
            f"Recorded {feedback_type} feedback for cluster {cluster_id} "
            f"by {created_by or 'anonymous'}"
        )

        return feedback.id

    async def update_cluster_label(
        self,
        cluster_id: int,
        label: str,
        confidence: float = 1.0,
    ) -> bool:
        """
        Update cluster label (after feedback).

        Args:
            cluster_id: ID of the cluster to update
            label: New label text
            confidence: Confidence score (0.0-1.0), default 1.0 for user corrections

        Returns:
            True if cluster was found and updated, False otherwise
        """
        # Use update statement for efficiency
        stmt = (
            update(BatchCluster)
            .where(BatchCluster.id == cluster_id)
            .values(
                label=label[:255],  # Truncate to fit column
                label_confidence=confidence,
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        updated = result.rowcount > 0

        if updated:
            logger.info(f"Updated cluster {cluster_id} label to: {label[:50]}...")
        else:
            logger.warning(f"Cluster {cluster_id} not found for label update")

        return updated

    async def get_batch_info(self, batch_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific batch.

        Args:
            batch_id: Batch UUID (defaults to latest completed)

        Returns:
            Dict with batch info or None if not found
        """
        if batch_id is None:
            batch_id = await self.get_latest_batch_id()
            if batch_id is None:
                return None

        query = select(ClusterBatch).where(ClusterBatch.batch_id == batch_id)
        result = await self.session.execute(query)
        batch = result.scalar_one_or_none()

        if batch is None:
            return None

        return {
            "batch_id": str(batch.batch_id),
            "status": batch.status,
            "article_count": batch.article_count,
            "cluster_count": batch.cluster_count,
            "noise_count": batch.noise_count,
            "csai_score": batch.csai_score,
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        }

    async def list_batches(
        self,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List recent batches.

        Args:
            status: Filter by status (running, completed, failed) or None for all
            limit: Maximum batches to return

        Returns:
            List of batch info dicts
        """
        query = select(ClusterBatch).order_by(ClusterBatch.started_at.desc())

        if status is not None:
            query = query.where(ClusterBatch.status == status)

        query = query.limit(limit)

        result = await self.session.execute(query)
        batches = result.scalars().all()

        return [
            {
                "batch_id": str(b.batch_id),
                "status": b.status,
                "article_count": b.article_count,
                "cluster_count": b.cluster_count,
                "noise_count": b.noise_count,
                "csai_score": b.csai_score,
                "started_at": b.started_at.isoformat() if b.started_at else None,
                "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            }
            for b in batches
        ]
