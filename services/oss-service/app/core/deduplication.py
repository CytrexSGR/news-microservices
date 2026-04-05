"""
Proposal Deduplication System

Issue #4: Prevents duplicate proposals from being submitted across analysis cycles.

Uses fingerprinting and TTL-based caching to detect duplicates without external dependencies.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
import asyncio
import httpx

from app.models.proposal import OntologyChangeProposal
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ProposalCacheEntry:
    """Cache entry for a submitted proposal."""
    fingerprint: str
    submitted_at: datetime
    proposal_id: str
    change_type: str  # ChangeType enum value as string
    expires_at: datetime


class ProposalDeduplicator:
    """
    Deduplication system for ontology change proposals.

    Uses a combination of:
    1. Local cache with TTL for recent proposals
    2. Fingerprinting based on proposal content (not ID)
    3. Optional API check for pending proposals

    Attributes:
        cache_ttl_hours: How long to remember submitted proposals
        max_cache_size: Maximum entries in cache before cleanup
    """

    def __init__(
        self,
        cache_ttl_hours: int = 24,
        max_cache_size: int = 10000
    ):
        self.cache_ttl_hours = cache_ttl_hours
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, ProposalCacheEntry] = {}
        self._lock = asyncio.Lock()

        logger.info(
            f"ProposalDeduplicator initialized: "
            f"TTL={cache_ttl_hours}h, max_size={max_cache_size}"
        )

    def _generate_fingerprint(self, proposal: OntologyChangeProposal) -> str:
        """
        Generate a unique fingerprint for a proposal based on its content.

        The fingerprint is based on:
        - Change type (NEW_ENTITY_TYPE, NEW_RELATIONSHIP_TYPE, etc.)
        - Title (contains pattern info)
        - Tags (contain entity type, relationship names)
        - Occurrence count

        This ensures the same underlying issue generates the same fingerprint
        even if detected in different analysis cycles.
        """
        from app.models.proposal import ChangeType

        # Build fingerprint components
        components = [
            proposal.change_type.value,  # Enum value as string
            proposal.title,  # Title contains the key pattern info
        ]

        # Add type-specific components based on change_type
        if proposal.change_type == ChangeType.NEW_ENTITY_TYPE:
            # For entity types, use tags which contain the type name
            if proposal.tags:
                components.extend(sorted(proposal.tags))
            # Also include occurrence count for uniqueness
            if proposal.occurrence_count:
                components.append(f"count:{proposal.occurrence_count}")

        elif proposal.change_type == ChangeType.NEW_RELATIONSHIP_TYPE:
            # For relationships, use tags and pattern query
            if proposal.tags:
                components.extend(sorted(proposal.tags))
            if proposal.pattern_query:
                # Extract key parts from pattern query
                components.append(proposal.pattern_query.strip()[:200])

        elif proposal.change_type == ChangeType.FLAG_INCONSISTENCY:
            # For inconsistencies, use title and evidence IDs
            if proposal.evidence:
                evidence_ids = sorted([e.example_id for e in proposal.evidence[:5]])
                components.extend(evidence_ids)

        elif proposal.change_type == ChangeType.MERGE_ENTITIES:
            # For merges, use evidence (duplicate pairs)
            if proposal.evidence:
                evidence_ids = sorted([e.example_id for e in proposal.evidence[:10]])
                components.extend(evidence_ids)

        else:
            # Fallback: use tags and occurrence count
            if proposal.tags:
                components.extend(sorted(proposal.tags))
            if proposal.occurrence_count:
                components.append(f"count:{proposal.occurrence_count}")

        # Generate hash
        fingerprint_string = "|".join(str(c) for c in components)
        fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]

        logger.debug(
            f"Generated fingerprint {fingerprint} for {proposal.change_type.value}"
        )

        return fingerprint

    async def is_duplicate(self, proposal: OntologyChangeProposal) -> bool:
        """
        Check if a proposal is a duplicate of a recently submitted one.

        Args:
            proposal: The proposal to check

        Returns:
            True if this is a duplicate, False otherwise
        """
        fingerprint = self._generate_fingerprint(proposal)

        async with self._lock:
            # Clean expired entries first
            await self._cleanup_expired()

            # Check cache
            if fingerprint in self._cache:
                entry = self._cache[fingerprint]
                if entry.expires_at > datetime.now():
                    logger.info(
                        f"Duplicate proposal detected: {proposal.proposal_type} "
                        f"(matches {entry.proposal_id} from {entry.submitted_at})"
                    )
                    return True
                else:
                    # Entry expired, remove it
                    del self._cache[fingerprint]

            return False

    async def is_duplicate_in_api(
        self,
        proposal: OntologyChangeProposal
    ) -> bool:
        """
        Check if a similar proposal already exists in the Proposals API.

        This is an optional additional check that queries the API for
        pending proposals of the same type.

        Args:
            proposal: The proposal to check

        Returns:
            True if a similar pending proposal exists
        """
        try:
            url = f"{settings.PROPOSALS_API_URL}/api/v1/ontology/proposals"
            params = {
                "status": "pending",
                "change_type": proposal.change_type.value,
                "limit": 100
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=5.0)

                if response.status_code != 200:
                    logger.warning(
                        f"Failed to check API for duplicates: {response.status_code}"
                    )
                    return False

                existing_proposals = response.json()
                fingerprint = self._generate_fingerprint(proposal)

                # Check each existing proposal
                for existing in existing_proposals:
                    # Convert to OntologyChangeProposal for fingerprinting
                    try:
                        existing_proposal = OntologyChangeProposal(**existing)
                        existing_fp = self._generate_fingerprint(existing_proposal)
                        if existing_fp == fingerprint:
                            logger.info(
                                f"Found matching pending proposal in API: "
                                f"{existing.get('proposal_id')}"
                            )
                            return True
                    except Exception:
                        continue

                return False

        except Exception as e:
            logger.warning(f"Error checking API for duplicates: {e}")
            return False

    async def mark_submitted(self, proposal: OntologyChangeProposal) -> None:
        """
        Mark a proposal as submitted, adding it to the deduplication cache.

        Args:
            proposal: The submitted proposal
        """
        fingerprint = self._generate_fingerprint(proposal)
        expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)

        async with self._lock:
            # Ensure cache doesn't grow too large
            if len(self._cache) >= self.max_cache_size:
                await self._cleanup_oldest()

            self._cache[fingerprint] = ProposalCacheEntry(
                fingerprint=fingerprint,
                submitted_at=datetime.now(),
                proposal_id=proposal.proposal_id,
                change_type=proposal.change_type.value,
                expires_at=expires_at
            )

            logger.debug(
                f"Cached proposal {proposal.proposal_id} with fingerprint {fingerprint}"
            )

    async def _cleanup_expired(self) -> int:
        """Remove expired entries from cache. Returns count of removed entries."""
        now = datetime.now()
        expired = [
            fp for fp, entry in self._cache.items()
            if entry.expires_at <= now
        ]

        for fp in expired:
            del self._cache[fp]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired cache entries")

        return len(expired)

    async def _cleanup_oldest(self) -> None:
        """Remove oldest 10% of cache entries when cache is full."""
        if not self._cache:
            return

        # Sort by submission time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].submitted_at
        )

        # Remove oldest 10%
        remove_count = max(1, len(sorted_entries) // 10)
        for fp, _ in sorted_entries[:remove_count]:
            del self._cache[fp]

        logger.info(f"Removed {remove_count} oldest cache entries (cache was full)")

    def get_stats(self) -> Dict:
        """Get deduplication cache statistics."""
        now = datetime.now()
        active_entries = sum(
            1 for entry in self._cache.values()
            if entry.expires_at > now
        )

        return {
            "total_cached": len(self._cache),
            "active_entries": active_entries,
            "cache_ttl_hours": self.cache_ttl_hours,
            "max_cache_size": self.max_cache_size
        }

    async def clear_cache(self) -> int:
        """Clear all cached entries. Returns count of cleared entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} entries from deduplication cache")
            return count


# Global deduplicator instance
deduplicator = ProposalDeduplicator(
    cache_ttl_hours=24,  # Remember proposals for 24 hours
    max_cache_size=10000  # Max 10k entries
)
