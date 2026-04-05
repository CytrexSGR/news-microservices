# services/clustering-service/app/services/profile_service.py
"""
Topic Profile Service for Semantic Category Matching.

Manages topic profiles that define semantic categories via descriptive text.
Profiles are embedded using OpenAI text-embedding-3-small, enabling mathematical
cluster matching via cosine similarity instead of hardcoded categories.

Example:
    profile_service = ProfileService(session, embedding_service)

    # Create finance profile
    profile = await profile_service.create_profile(
        name="finance",
        display_name="Financial Markets",
        description_text="Stocks, bonds, ETFs, Federal Reserve, interest rates..."
    )

    # Find matching clusters
    matches = await profile_service.find_matching_clusters(
        profile_name="finance",
        limit=20,
        min_similarity=0.40
    )
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch_cluster import TopicProfile
from app.services.embedding_service import EmbeddingService
from app.config import settings

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Service for managing topic profiles and cluster matching.

    Topic profiles replace hardcoded category assignments (CONFLICT, FINANCE, etc.)
    with mathematically-derived semantic categories. Each profile:
    1. Has a descriptive text that captures the topic domain
    2. Is embedded into the same 1536D space as cluster centroids
    3. Matches clusters via cosine similarity (default threshold: 0.40)
    """

    def __init__(self, session: AsyncSession, embedding_service: EmbeddingService):
        """
        Initialize ProfileService.

        Args:
            session: Async SQLAlchemy database session
            embedding_service: Service for generating embeddings
        """
        self.session = session
        self.embedding_service = embedding_service

    async def create_profile(
        self,
        name: str,
        description_text: str,
        display_name: Optional[str] = None,
        min_similarity: float = 0.40,
        priority: int = 0,
        embed_now: bool = True,
    ) -> TopicProfile:
        """
        Create a new topic profile.

        Args:
            name: Unique profile identifier (e.g., "finance", "conflict")
            description_text: Descriptive text to embed (keywords, concepts)
            display_name: Human-readable name for UI display
            min_similarity: Threshold for cluster matching (0.0-1.0)
            priority: Sort order (higher = more prominent)
            embed_now: Generate embedding immediately (default: True)

        Returns:
            Created TopicProfile

        Raises:
            ValueError: If profile with name already exists
        """
        # Check for duplicate
        existing = await self.get_profile_by_name(name)
        if existing:
            raise ValueError(f"Profile '{name}' already exists")

        profile = TopicProfile(
            name=name,
            display_name=display_name or name.title(),
            description_text=description_text,
            min_similarity=min_similarity,
            priority=priority,
            is_active=True,
        )

        self.session.add(profile)
        await self.session.flush()

        logger.info(f"Created profile '{name}' (id={profile.id})")

        # Generate and store embedding
        if embed_now:
            await self.update_profile_embedding(profile.id)

        return profile

    async def get_profile_by_name(self, name: str) -> Optional[TopicProfile]:
        """Get profile by unique name."""
        query = select(TopicProfile).where(TopicProfile.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, profile_id: int) -> Optional[TopicProfile]:
        """Get profile by ID."""
        query = select(TopicProfile).where(TopicProfile.id == profile_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_profiles(
        self,
        active_only: bool = True,
        order_by_priority: bool = True,
    ) -> List[TopicProfile]:
        """
        List all topic profiles.

        Args:
            active_only: Only return active profiles
            order_by_priority: Sort by priority descending

        Returns:
            List of TopicProfile objects
        """
        query = select(TopicProfile)

        if active_only:
            query = query.where(TopicProfile.is_active == True)  # noqa: E712

        if order_by_priority:
            query = query.order_by(TopicProfile.priority.desc(), TopicProfile.name)
        else:
            query = query.order_by(TopicProfile.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_profile(
        self,
        profile_id: int,
        description_text: Optional[str] = None,
        display_name: Optional[str] = None,
        min_similarity: Optional[float] = None,
        priority: Optional[int] = None,
        is_active: Optional[bool] = None,
        re_embed: bool = True,
    ) -> Optional[TopicProfile]:
        """
        Update profile fields.

        Args:
            profile_id: Profile ID to update
            description_text: New description (triggers re-embedding if re_embed=True)
            display_name: New display name
            min_similarity: New similarity threshold
            priority: New priority
            is_active: Activate/deactivate profile
            re_embed: Re-generate embedding if description changed

        Returns:
            Updated TopicProfile or None if not found
        """
        profile = await self.get_profile_by_id(profile_id)
        if not profile:
            return None

        updated_fields = []

        if description_text is not None:
            profile.description_text = description_text
            updated_fields.append("description_text")

        if display_name is not None:
            profile.display_name = display_name
            updated_fields.append("display_name")

        if min_similarity is not None:
            profile.min_similarity = min_similarity
            updated_fields.append("min_similarity")

        if priority is not None:
            profile.priority = priority
            updated_fields.append("priority")

        if is_active is not None:
            profile.is_active = is_active
            updated_fields.append("is_active")

        if updated_fields:
            await self.session.flush()
            logger.info(f"Updated profile '{profile.name}': {updated_fields}")

        # Re-embed if description changed
        if "description_text" in updated_fields and re_embed:
            await self.update_profile_embedding(profile_id)

        return profile

    async def delete_profile(self, profile_id: int) -> bool:
        """
        Delete a profile.

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        profile = await self.get_profile_by_id(profile_id)
        if not profile:
            return False

        profile_name = profile.name
        await self.session.delete(profile)
        await self.session.flush()

        logger.info(f"Deleted profile '{profile_name}' (id={profile_id})")
        return True

    async def update_profile_embedding(self, profile_id: int) -> bool:
        """
        Generate and store embedding for a profile's description_text.

        Uses the EmbeddingService to create a 1536D vector from the profile's
        description_text, then stores it in the embedding_vec column.

        Args:
            profile_id: Profile ID to update

        Returns:
            True if embedding updated, False if failed
        """
        profile = await self.get_profile_by_id(profile_id)
        if not profile:
            logger.warning(f"Profile {profile_id} not found for embedding update")
            return False

        if not self.embedding_service.is_available():
            logger.warning("EmbeddingService not available - skipping embedding")
            return False

        # Generate embedding
        embedding = await self.embedding_service.embed_query(profile.description_text)
        if embedding is None:
            logger.error(f"Failed to generate embedding for profile '{profile.name}'")
            return False

        # Store embedding via raw SQL (pgvector column)
        embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"

        await self.session.execute(
            text("""
                UPDATE topic_profiles
                SET embedding_vec = CAST(:embedding AS vector)
                WHERE id = :profile_id
            """),
            {"embedding": embedding_str, "profile_id": profile_id},
        )

        logger.info(
            f"Updated embedding for profile '{profile.name}' "
            f"(dim={len(embedding)})"
        )
        return True

    async def find_matching_clusters(
        self,
        profile_name: str,
        batch_id: Optional[str] = None,
        limit: int = 20,
        min_similarity: Optional[float] = None,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find clusters that match a topic profile by embedding similarity.

        If USE_ARTICLE_CLUSTERS feature flag is enabled (and no specific batch_id
        is requested), uses persistent article_clusters which eliminates duplicates.
        Otherwise, uses batch_clusters for backward compatibility.

        Args:
            profile_name: Name of the profile to match against
            batch_id: Specific batch ID (defaults to latest completed, forces batch_clusters)
            limit: Maximum clusters to return
            min_similarity: Override profile's min_similarity threshold
            hours: Filter to clusters from batches completed in last N hours
            since: Filter to clusters from batches completed after this datetime

        Returns:
            List of cluster dicts with similarity scores

        Example:
            matches = await service.find_matching_clusters("finance", limit=25)
            # [{"id": 1, "label": "Fed Rate Decision", "similarity": 0.52}, ...]

            # With time filter
            matches = await service.find_matching_clusters("conflict", hours=24)
        """
        # Use article_clusters if feature flag is enabled AND no specific batch_id requested
        # Explicit batch_id always routes to batch_clusters for backward compatibility
        if settings.USE_ARTICLE_CLUSTERS and batch_id is None:
            return await self.find_matching_clusters_article_clusters(
                profile_name=profile_name,
                limit=limit,
                min_similarity=min_similarity,
                hours=hours,
                since=since,
            )

        # Original batch_clusters implementation
        profile = await self.get_profile_by_name(profile_name)
        if not profile:
            logger.warning(f"Profile '{profile_name}' not found")
            return []

        threshold = min_similarity if min_similarity is not None else profile.min_similarity

        # Build query based on filters
        params: Dict[str, Any] = {"profile_id": profile.id, "limit": limit}

        if batch_id:
            # Specific batch
            batch_filter = "bc.batch_id = :batch_id"
            params["batch_id"] = batch_id
        elif hours is not None:
            # Time-based filter: last N hours
            batch_filter = """
                bc.batch_id IN (
                    SELECT batch_id FROM cluster_batches
                    WHERE status = 'completed'
                      AND completed_at >= NOW() - INTERVAL '1 hour' * :hours
                )
            """
            params["hours"] = hours
        elif since is not None:
            # Time-based filter: since datetime
            batch_filter = """
                bc.batch_id IN (
                    SELECT batch_id FROM cluster_batches
                    WHERE status = 'completed'
                      AND completed_at >= :since
                )
            """
            params["since"] = since
        else:
            # Default: latest completed batch only
            batch_filter = """
                bc.batch_id = (
                    SELECT batch_id FROM cluster_batches
                    WHERE status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                )
            """

        query = text(f"""
            SELECT
                bc.id,
                bc.cluster_idx,
                bc.label,
                bc.article_count,
                bc.keywords,
                1 - (bc.centroid_vec <=> tp.embedding_vec) as similarity
            FROM batch_clusters bc
            CROSS JOIN topic_profiles tp
            WHERE tp.id = :profile_id
              AND bc.centroid_vec IS NOT NULL
              AND tp.embedding_vec IS NOT NULL
              AND {batch_filter}
            ORDER BY bc.centroid_vec <=> tp.embedding_vec
            LIMIT :limit
        """)

        result = await self.session.execute(query, params)
        rows = result.fetchall()

        # Filter by threshold and format response
        matches = []
        for row in rows:
            similarity = float(row.similarity) if row.similarity else 0.0
            if similarity >= threshold:
                matches.append({
                    "id": row.id,
                    "cluster_idx": row.cluster_idx,
                    "label": row.label,
                    "article_count": row.article_count,
                    "keywords": row.keywords,
                    "similarity": round(similarity, 4),
                })

        logger.info(
            f"Found {len(matches)} batch_clusters matching profile '{profile_name}' "
            f"(threshold={threshold:.0%})"
        )
        return matches

    async def find_matching_clusters_article_clusters(
        self,
        profile_name: str,
        limit: int = 20,
        min_similarity: Optional[float] = None,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find clusters matching a profile using article_clusters (persistent).

        Uses pgvector cosine distance on article_clusters.centroid_vec.
        This eliminates duplicates that occur with batch_clusters because
        article_clusters are persistent and not recreated every 2 hours.

        Args:
            profile_name: Name of the profile to match against
            limit: Maximum clusters to return
            min_similarity: Override profile's min_similarity threshold
            hours: Filter to clusters active in last N hours
            since: Filter to clusters active after this datetime

        Returns:
            List of cluster dicts with similarity scores and CSAI status

        Example:
            matches = await service.find_matching_clusters_article_clusters(
                "finance", hours=24, limit=20
            )
            # [{"id": "uuid", "label": "Fed Rate", "csai_status": "stable", ...}, ...]
        """
        profile = await self.get_profile_by_name(profile_name)
        if not profile:
            logger.warning(f"Profile '{profile_name}' not found")
            return []

        threshold = min_similarity if min_similarity is not None else profile.min_similarity

        # Build time filter
        time_filter = ""
        params: Dict[str, Any] = {"profile_id": profile.id, "limit": limit}

        if hours is not None:
            time_filter = "AND ac.last_updated_at > NOW() - INTERVAL '1 hour' * :hours"
            params["hours"] = hours
        elif since is not None:
            time_filter = "AND ac.last_updated_at >= :since"
            params["since"] = since

        query = text(f"""
            SELECT
                ac.id,
                ac.title as label,
                ac.article_count,
                ac.csai_status,
                ac.csai_score,
                1 - (ac.centroid_vec <=> tp.embedding_vec) as similarity
            FROM article_clusters ac
            CROSS JOIN topic_profiles tp
            WHERE tp.id = :profile_id
              AND ac.status = 'active'
              AND ac.centroid_vec IS NOT NULL
              AND tp.embedding_vec IS NOT NULL
              AND (ac.csai_status IS NULL OR ac.csai_status IN ('stable', 'pending'))
              {time_filter}
            ORDER BY ac.centroid_vec <=> tp.embedding_vec
            LIMIT :limit
        """)

        result = await self.session.execute(query, params)
        rows = result.fetchall()

        # Filter by threshold and format response
        matches = []
        for row in rows:
            similarity = float(row.similarity) if row.similarity else 0.0
            if similarity >= threshold:
                matches.append({
                    "id": str(row.id),  # UUID as string
                    "cluster_idx": 0,  # Not applicable for article_clusters
                    "label": row.label,
                    "article_count": row.article_count,
                    "keywords": None,  # Not available in article_clusters
                    "csai_status": row.csai_status,
                    "csai_score": row.csai_score,
                    "similarity": round(similarity, 4),
                })

        logger.info(
            f"Found {len(matches)} article_clusters matching profile '{profile_name}' "
            f"(threshold={threshold:.0%})"
        )
        return matches

    async def get_all_profile_matches(
        self,
        batch_id: Optional[str] = None,
        limit_per_profile: int = 10,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get matching clusters for all active profiles.

        Useful for generating category-based views or SITREP summaries.

        Args:
            batch_id: Specific batch ID (defaults to latest)
            limit_per_profile: Max clusters per profile
            hours: Filter to clusters from batches completed in last N hours
            since: Filter to clusters from batches completed after this datetime

        Returns:
            Dict mapping profile names to their matching clusters

        Example:
            all_matches = await service.get_all_profile_matches()
            # {
            #   "finance": [{"id": 1, "label": "Fed Rate", "similarity": 0.52}, ...],
            #   "conflict": [{"id": 5, "label": "Ukraine War", "similarity": 0.61}, ...],
            # }

            # With time filter
            all_matches = await service.get_all_profile_matches(hours=24)
        """
        profiles = await self.list_profiles(active_only=True)

        result = {}
        for profile in profiles:
            matches = await self.find_matching_clusters(
                profile_name=profile.name,
                batch_id=batch_id,
                limit=limit_per_profile,
                hours=hours,
                since=since,
            )
            result[profile.name] = matches

        return result

    async def embed_all_profiles(self) -> Dict[str, bool]:
        """
        Generate embeddings for all profiles that don't have one.

        Returns:
            Dict mapping profile names to success status
        """
        # Find profiles without embeddings via raw SQL
        query = text("""
            SELECT id, name FROM topic_profiles
            WHERE embedding_vec IS NULL AND is_active = true
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        results = {}
        for row in rows:
            success = await self.update_profile_embedding(row.id)
            results[row.name] = success

        logger.info(f"Embedded {sum(results.values())}/{len(results)} profiles")
        return results
