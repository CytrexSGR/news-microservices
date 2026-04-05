"""Database operations for article clusters."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cluster import ArticleCluster, ClusterMembership

logger = logging.getLogger(__name__)


class ClusterRepository:
    """Repository for cluster database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create_cluster(
        self,
        title: str,
        centroid_vector: List[float],
        first_article_id: UUID,
        entities: Optional[List[Dict[str, Any]]] = None,
        tension_score: Optional[float] = None,
    ) -> UUID:
        """
        Create a new cluster.

        Args:
            title: Cluster title (from first article)
            centroid_vector: Initial centroid (first article's embedding)
            first_article_id: UUID of first article
            entities: Primary entities from first article
            tension_score: Initial tension score

        Returns:
            UUID of created cluster
        """
        now = datetime.now(timezone.utc)

        cluster = ArticleCluster(
            id=uuid4(),
            title=title[:500],  # Truncate to fit column
            status="active",
            article_count=1,
            first_seen_at=now,
            last_updated_at=now,
            centroid_vector=centroid_vector,
            primary_entities=entities,
            tension_score=tension_score,
            is_breaking=False,
        )

        self.session.add(cluster)
        await self.session.commit()
        await self.session.refresh(cluster)

        logger.info(f"Created cluster {cluster.id} with title: {title[:50]}...")

        return cluster.id

    async def get_active_clusters(
        self,
        max_age_hours: int = 72,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get active clusters for matching.

        Args:
            max_age_hours: Only return clusters updated within this window
            limit: Maximum clusters to return

        Returns:
            List of dicts with id, centroid, article_count
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        query = (
            select(ArticleCluster)
            .where(ArticleCluster.status == "active")
            .where(ArticleCluster.last_updated_at >= cutoff)
            .order_by(ArticleCluster.last_updated_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        clusters = result.scalars().all()

        return [
            {
                "id": c.id,
                "centroid": c.centroid_vector,
                "article_count": c.article_count,
                "title": c.title,
            }
            for c in clusters
            if c.centroid_vector is not None
        ]

    async def update_cluster(
        self,
        cluster_id: UUID,
        new_centroid: List[float],
        new_article_count: int,
        entities: Optional[List[Dict[str, Any]]] = None,
        tension_score: Optional[float] = None,
        is_breaking: bool = False,
    ) -> Optional[ArticleCluster]:
        """
        Update cluster with new article.

        Args:
            cluster_id: Cluster to update
            new_centroid: Updated centroid vector
            new_article_count: New total article count
            entities: Updated primary entities
            tension_score: Updated tension score
            is_breaking: Whether cluster is breaking news

        Returns:
            Updated cluster or None if not found
        """
        query = select(ArticleCluster).where(ArticleCluster.id == cluster_id)
        result = await self.session.execute(query)
        cluster = result.scalar_one_or_none()

        if cluster is None:
            logger.warning(f"Cluster {cluster_id} not found for update")
            return None

        cluster.centroid_vector = new_centroid
        cluster.article_count = new_article_count
        cluster.last_updated_at = datetime.now(timezone.utc)

        if entities:
            cluster.primary_entities = entities

        if tension_score is not None:
            cluster.tension_score = tension_score

        if is_breaking and not cluster.is_breaking:
            cluster.is_breaking = True
            cluster.burst_detected_at = datetime.now(timezone.utc)

        await self.session.commit()

        logger.debug(f"Updated cluster {cluster_id}: {new_article_count} articles")

        return cluster

    async def get_cluster_by_id(self, cluster_id: UUID) -> Optional[ArticleCluster]:
        """
        Get cluster by ID.

        Args:
            cluster_id: Cluster UUID

        Returns:
            ArticleCluster or None
        """
        query = select(ArticleCluster).where(ArticleCluster.id == cluster_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_clusters_paginated(
        self,
        status: str = "active",
        min_articles: int = 2,
        hours: int = 24,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ArticleCluster], int]:
        """
        Get clusters with pagination.

        Args:
            status: Filter by status (active, archived, all)
            min_articles: Minimum article count
            hours: Time window in hours
            limit: Page size
            offset: Page offset

        Returns:
            Tuple of (clusters, total_count)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Base query
        base_query = select(ArticleCluster).where(
            ArticleCluster.article_count >= min_articles,
            ArticleCluster.last_updated_at >= cutoff,
        )

        if status != "all":
            base_query = base_query.where(ArticleCluster.status == status)

        # Count query
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query with pagination
        data_query = (
            base_query
            .order_by(ArticleCluster.last_updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(data_query)
        clusters = list(result.scalars().all())

        return clusters, total

    async def is_article_processed(self, article_id: UUID) -> bool:
        """
        Check if article has already been assigned to a cluster.

        Used for idempotency - prevents duplicate processing of the same article.

        Args:
            article_id: UUID of the article to check

        Returns:
            True if article is already in a cluster
        """
        query = select(ClusterMembership.article_id).where(
            ClusterMembership.article_id == article_id
        ).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def add_article_to_cluster(
        self,
        cluster_id: UUID,
        article_id: UUID,
        similarity_score: Optional[float] = None,
    ) -> None:
        """
        Record article membership in a cluster.

        Args:
            cluster_id: Cluster the article belongs to
            article_id: Article being added
            similarity_score: Similarity at time of joining
        """
        membership = ClusterMembership(
            cluster_id=cluster_id,
            article_id=article_id,
            similarity_score=similarity_score,
        )

        self.session.add(membership)
        await self.session.flush()

        logger.debug(f"Added article {article_id} to cluster {cluster_id}")

    async def get_cluster_for_article(self, article_id: UUID) -> Optional[UUID]:
        """
        Get the cluster ID for an article if it exists.

        Args:
            article_id: Article UUID to look up

        Returns:
            Cluster UUID if found, None otherwise
        """
        query = select(ClusterMembership.cluster_id).where(
            ClusterMembership.article_id == article_id
        ).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_article_timestamps(
        self,
        cluster_id: UUID,
        hours: int = 1
    ) -> List[datetime]:
        """
        Get article arrival timestamps for a cluster.

        Used for velocity-based burst detection by providing article
        join times within a lookback window.

        Args:
            cluster_id: UUID of the cluster
            hours: Look back window in hours

        Returns:
            List of datetime timestamps (joined_at from memberships)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(ClusterMembership.joined_at)
            .where(ClusterMembership.cluster_id == cluster_id)
            .where(ClusterMembership.joined_at >= cutoff)
            .order_by(ClusterMembership.joined_at.desc())
        )

        result = await self.session.execute(query)
        return [row[0] for row in result.all()]

    async def get_cluster_article_range(
        self,
        cluster_id: UUID,
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get the first and last article timestamps for a cluster.

        Returns the actual time range of all articles in the cluster,
        not limited by a lookback window.

        Args:
            cluster_id: UUID of the cluster

        Returns:
            Tuple of (first_article_at, last_article_at) datetimes
        """
        query = select(
            func.min(ClusterMembership.joined_at),
            func.max(ClusterMembership.joined_at),
        ).where(ClusterMembership.cluster_id == cluster_id)

        result = await self.session.execute(query)
        row = result.one_or_none()

        if row:
            return row[0], row[1]
        return None, None

    async def get_cluster_articles(
        self,
        cluster_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get articles belonging to a cluster with pagination.

        Args:
            cluster_id: UUID of the cluster
            limit: Page size
            offset: Page offset

        Returns:
            Tuple of (articles list, total count)
        """
        from sqlalchemy import text

        # Count total articles in cluster
        count_sql = text("""
            SELECT COUNT(*) FROM cluster_memberships
            WHERE cluster_id = :cluster_id
        """)
        count_result = await self.session.execute(count_sql, {"cluster_id": cluster_id})
        total = count_result.scalar() or 0

        # Get articles with feed_items and feeds join
        articles_sql = text("""
            SELECT
                fi.id,
                fi.title,
                fi.link as url,
                fi.published_at,
                fd.name as source_name,
                cm.joined_at,
                cm.similarity_score
            FROM cluster_memberships cm
            JOIN feed_items fi ON cm.article_id = fi.id
            LEFT JOIN feeds fd ON fi.feed_id = fd.id
            WHERE cm.cluster_id = :cluster_id
            ORDER BY cm.joined_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.session.execute(
            articles_sql,
            {"cluster_id": cluster_id, "limit": limit, "offset": offset}
        )
        rows = result.fetchall()

        articles = [
            {
                "id": str(row.id),
                "title": row.title,
                "url": row.url,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "source_name": row.source_name,
                "joined_at": row.joined_at.isoformat() if row.joined_at else None,
                "similarity_score": row.similarity_score,
            }
            for row in rows
        ]

        return articles, total

    # ========================================
    # pgvector-based search methods (Task 4)
    # ========================================

    async def find_matching_cluster_pgvector(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.75,
        max_age_hours: int = 24,
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching cluster using pgvector similarity search.

        Uses cosine distance operator (<=>) for fast similarity lookup.
        Only searches clusters with centroid_vec (pgvector) populated.

        Args:
            embedding: 1536D article embedding
            similarity_threshold: Minimum cosine similarity (default 0.75)
            max_age_hours: Only search clusters active within this window

        Returns:
            Dict with cluster info and similarity, or None if no match
        """
        from sqlalchemy import text

        # Format embedding as pgvector string: "[0.1,0.2,...]"
        embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"

        query = text("""
            SELECT
                id,
                title,
                article_count,
                csai_status,
                1 - (centroid_vec <=> CAST(:embedding AS vector)) as similarity
            FROM article_clusters
            WHERE status = 'active'
              AND centroid_vec IS NOT NULL
              AND last_updated_at > NOW() - INTERVAL :hours
              AND 1 - (centroid_vec <=> CAST(:embedding AS vector)) > :threshold
            ORDER BY centroid_vec <=> CAST(:embedding AS vector)
            LIMIT 1
        """)

        result = await self.session.execute(
            query,
            {
                "embedding": embedding_str,
                "hours": f"{max_age_hours} hours",
                "threshold": similarity_threshold,
            }
        )
        row = result.fetchone()

        if row is None:
            return None

        return {
            "id": row.id,
            "title": row.title,
            "article_count": row.article_count,
            "csai_status": row.csai_status,
            "similarity": float(row.similarity),
        }

    async def update_cluster_pgvector(
        self,
        cluster_id: UUID,
        new_centroid: List[float],
        new_article_count: int,
    ) -> bool:
        """
        Update cluster with new centroid in both JSONB and pgvector formats.

        Args:
            cluster_id: Cluster UUID
            new_centroid: Updated centroid vector
            new_article_count: New article count

        Returns:
            True if updated, False if cluster not found
        """
        from sqlalchemy import text

        embedding_str = "[" + ",".join(str(f) for f in new_centroid) + "]"

        result = await self.session.execute(
            text("""
                UPDATE article_clusters
                SET centroid_vector = :centroid_json::jsonb,
                    centroid_vec = :centroid_vec::vector,
                    article_count = :count,
                    last_updated_at = NOW()
                WHERE id = :cluster_id
            """),
            {
                "centroid_json": embedding_str,
                "centroid_vec": embedding_str,
                "count": new_article_count,
                "cluster_id": cluster_id,
            }
        )

        return result.rowcount > 0

    async def update_csai_status(
        self,
        cluster_id: UUID,
        csai_score: float,
        csai_status: str,
    ) -> bool:
        """
        Update CSAI validation results for a cluster.

        Args:
            cluster_id: Cluster UUID
            csai_score: Calculated CSAI score
            csai_status: 'stable', 'unstable', or 'pending'

        Returns:
            True if updated, False if cluster not found
        """
        from sqlalchemy import text

        result = await self.session.execute(
            text("""
                UPDATE article_clusters
                SET csai_score = :score,
                    csai_status = :status,
                    csai_checked_at = NOW()
                WHERE id = :cluster_id
            """),
            {
                "score": csai_score,
                "status": csai_status,
                "cluster_id": cluster_id,
            }
        )

        return result.rowcount > 0

    async def create_cluster_with_pgvector(
        self,
        title: str,
        centroid_vector: List[float],
        first_article_id: UUID,
        entities: Optional[List[Dict[str, Any]]] = None,
        tension_score: Optional[float] = None,
    ) -> UUID:
        """
        Create a new cluster with both JSONB and pgvector centroids.

        Args:
            title: Cluster title
            centroid_vector: Initial centroid (1536D)
            first_article_id: UUID of first article
            entities: Primary entities
            tension_score: Initial tension score

        Returns:
            UUID of created cluster
        """
        from sqlalchemy import text
        import json

        cluster_id = uuid4()
        embedding_str = "[" + ",".join(str(f) for f in centroid_vector) + "]"

        # Serialize entities to JSON if provided
        entities_json = json.dumps(entities) if entities else None

        await self.session.execute(
            text("""
                INSERT INTO article_clusters (
                    id, title, status, article_count,
                    first_seen_at, last_updated_at,
                    centroid_vector, centroid_vec,
                    primary_entities, tension_score,
                    is_breaking, csai_status
                ) VALUES (
                    :id, :title, 'active', 1,
                    NOW(), NOW(),
                    :centroid_json::jsonb, :centroid_vec::vector,
                    :entities::jsonb, :tension,
                    false, 'pending'
                )
            """),
            {
                "id": cluster_id,
                "title": title[:500],  # Truncate to fit column
                "centroid_json": embedding_str,
                "centroid_vec": embedding_str,
                "entities": entities_json,
                "tension": tension_score,
            }
        )

        await self.session.commit()
        logger.info(f"Created cluster {cluster_id} with pgvector: {title[:50]}...")

        return cluster_id
