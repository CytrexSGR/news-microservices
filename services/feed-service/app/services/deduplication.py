# services/feed-service/app/services/deduplication.py
"""SimHash-based deduplication service.

Provides duplicate and near-duplicate detection using SimHash fingerprints
and Hamming distance calculations.

Thresholds:
    - Hamming <= 3: Duplicate (reject)
    - Hamming 4-7: Near-duplicate (flag for review)
    - Hamming > 7: Different content (allow)
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from uuid import UUID

from news_intelligence_common import SimHasher

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    """Result of deduplication check.

    Attributes:
        is_allowed: Whether the article should be ingested
        is_duplicate: Whether it's an exact duplicate (Hamming <= 3)
        is_near_duplicate: Whether it's a near-duplicate (Hamming 4-7)
        matching_article_id: UUID of the matching article (if any)
        matching_fingerprint: Fingerprint of the matching article
        hamming_distance: Distance to closest match (None if no match)
    """
    is_allowed: bool
    is_duplicate: bool
    is_near_duplicate: bool
    matching_article_id: Optional[UUID] = None
    matching_fingerprint: Optional[int] = None
    hamming_distance: Optional[int] = None


class DeduplicationService:
    """Service for SimHash-based duplicate detection.

    Uses SimHasher from news-intelligence-common library for
    Hamming distance calculations.

    Example:
        >>> service = DeduplicationService()
        >>> result = service.check_duplicate(fingerprint, existing_fps)
        >>> if not result.is_allowed:
        ...     logger.info(f"Duplicate detected: {result.hamming_distance} bits")
    """

    def __init__(self):
        self.hasher = SimHasher()

    def check_duplicate(
        self,
        fingerprint: int,
        existing_fingerprints: List[Tuple[UUID, int]],
    ) -> DeduplicationResult:
        """
        Check if fingerprint is duplicate/near-duplicate of existing articles.

        Args:
            fingerprint: SimHash fingerprint of new article
            existing_fingerprints: List of (article_id, fingerprint) tuples

        Returns:
            DeduplicationResult with detection status
        """
        if not existing_fingerprints:
            return DeduplicationResult(
                is_allowed=True,
                is_duplicate=False,
                is_near_duplicate=False,
            )

        # Find closest match
        closest_match: Optional[Tuple[UUID, int, int]] = None  # (id, fp, distance)

        for article_id, existing_fp in existing_fingerprints:
            distance = SimHasher.hamming_distance(fingerprint, existing_fp)

            if closest_match is None or distance < closest_match[2]:
                closest_match = (article_id, existing_fp, distance)

            # Early exit for exact duplicate
            if distance <= SimHasher.DUPLICATE_THRESHOLD:
                break

        if closest_match is None:
            return DeduplicationResult(
                is_allowed=True,
                is_duplicate=False,
                is_near_duplicate=False,
            )

        article_id, existing_fp, distance = closest_match

        # Check thresholds
        is_duplicate = distance <= SimHasher.DUPLICATE_THRESHOLD
        is_near_duplicate = (
            SimHasher.DUPLICATE_THRESHOLD < distance <= SimHasher.NEAR_DUPLICATE_THRESHOLD
        )

        return DeduplicationResult(
            is_allowed=not is_duplicate,  # Duplicates rejected, near-dups allowed
            is_duplicate=is_duplicate,
            is_near_duplicate=is_near_duplicate,
            matching_article_id=article_id,
            matching_fingerprint=existing_fp,
            hamming_distance=distance,
        )
