# services/feed-service/app/services/dedup_repository.py
"""Repository for deduplication database operations.

Provides efficient queries for SimHash fingerprint lookup
and near-duplicate flagging for human review.

This is part of Epic 1.2: Deduplication Pipeline.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed import FeedItem, DuplicateCandidate

logger = logging.getLogger(__name__)


class DeduplicationRepository:
    """Repository for deduplication operations.

    Provides database access for:
    - Retrieving recent article fingerprints for comparison
    - Flagging near-duplicates for human review
    - Checking pending review counts
    - Detecting already-flagged article pairs

    Attributes:
        session: SQLAlchemy async session

    Example:
        >>> repo = DeduplicationRepository(session)
        >>> fingerprints = await repo.get_recent_fingerprints(hours=72)
        >>> if dedup_result.is_near_duplicate:
        ...     await repo.flag_near_duplicate(...)
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session

    async def get_recent_fingerprints(
        self,
        hours: int = 72,
        limit: int = 10000,
    ) -> List[Tuple[UUID, int]]:
        """Get recent article fingerprints for duplicate checking.

        Uses time-bounded query to limit candidate set for performance.
        Only returns articles that have a simhash_fingerprint set.

        Args:
            hours: Look back window in hours (default 72 = 3 days)
            limit: Maximum fingerprints to return (default 10000)

        Returns:
            List of (article_id, simhash_fingerprint) tuples,
            ordered by created_at descending (most recent first)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(FeedItem.id, FeedItem.simhash_fingerprint)
            .where(FeedItem.simhash_fingerprint.isnot(None))
            .where(FeedItem.created_at >= cutoff)
            .order_by(FeedItem.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [(row[0], row[1]) for row in rows]

    async def flag_near_duplicate(
        self,
        new_article_id: UUID,
        existing_article_id: UUID,
        hamming_distance: int,
        simhash_new: int,
        simhash_existing: int,
    ) -> UUID:
        """Flag a near-duplicate for human review.

        Creates a DuplicateCandidate record with status='pending'.
        These records can be reviewed via the /api/v1/duplicates endpoints.

        Args:
            new_article_id: ID of newly ingested article
            existing_article_id: ID of matching existing article
            hamming_distance: Hamming distance between fingerprints (4-7)
            simhash_new: Fingerprint of new article
            simhash_existing: Fingerprint of existing article

        Returns:
            UUID of created duplicate_candidate record
        """
        candidate = DuplicateCandidate(
            new_article_id=new_article_id,
            existing_article_id=existing_article_id,
            hamming_distance=hamming_distance,
            simhash_new=simhash_new,
            simhash_existing=simhash_existing,
            status="pending",
        )

        self.session.add(candidate)
        await self.session.flush()

        logger.info(
            f"Flagged near-duplicate: {new_article_id} ~ {existing_article_id} "
            f"(Hamming: {hamming_distance})"
        )

        return candidate.id

    async def get_pending_review_count(self) -> int:
        """Get count of pending near-duplicate reviews.

        Returns:
            Number of duplicate candidates with status='pending'
        """
        query = select(DuplicateCandidate).where(
            DuplicateCandidate.status == "pending"
        )
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def check_article_already_flagged(
        self,
        new_article_id: UUID,
        existing_article_id: UUID,
    ) -> bool:
        """Check if this article pair was already flagged.

        Prevents duplicate flagging of the same article pair.

        Args:
            new_article_id: ID of the new article
            existing_article_id: ID of the existing article

        Returns:
            True if pair already has a duplicate_candidate record
        """
        query = (
            select(DuplicateCandidate)
            .where(
                DuplicateCandidate.new_article_id == new_article_id,
                DuplicateCandidate.existing_article_id == existing_article_id,
            )
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
