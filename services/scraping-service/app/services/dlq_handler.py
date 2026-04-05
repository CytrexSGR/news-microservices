"""
Dead Letter Queue Handler

Manages failed scrape jobs with exponential backoff retry logic.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from app.models.dlq import (
    DeadLetterEntry,
    DeadLetterCreate,
    DeadLetterUpdate,
    FailureReasonEnum,
    DeadLetterStatusEnum
)

logger = logging.getLogger(__name__)


class DLQHandler:
    """Handles dead letter queue operations with retry logic"""

    # Base delay for exponential backoff (in seconds)
    BASE_DELAY = 60  # 1 minute

    # Maximum delay cap (in seconds)
    MAX_DELAY = 86400  # 24 hours

    # Jitter factor for randomization
    JITTER_FACTOR = 0.2

    # Max retries by failure reason
    MAX_RETRIES_BY_REASON = {
        FailureReasonEnum.TIMEOUT: 5,
        FailureReasonEnum.BLOCKED: 3,
        FailureReasonEnum.PAYWALL: 2,
        FailureReasonEnum.EXTRACTION_FAILED: 5,
        FailureReasonEnum.RATE_LIMITED: 10,
        FailureReasonEnum.CONNECTION_ERROR: 5,
        FailureReasonEnum.INVALID_CONTENT: 2,
        FailureReasonEnum.STRUCTURE_CHANGED: 1,
        FailureReasonEnum.UNKNOWN: 3,
    }

    def __init__(self):
        self._entries: Dict[int, DeadLetterEntry] = {}
        self._url_index: Dict[str, int] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()

    async def add_entry(self, create_data: DeadLetterCreate) -> DeadLetterEntry:
        """
        Add a new entry to the dead letter queue.

        Args:
            create_data: Data for creating the entry

        Returns:
            Created DeadLetterEntry
        """
        async with self._lock:
            # Check if URL already exists
            existing_id = self._url_index.get(create_data.url)
            if existing_id:
                # Update existing entry
                existing = self._entries[existing_id]
                return await self._update_existing_entry(existing, create_data)

            # Extract domain from URL
            domain = self._extract_domain(create_data.url)

            # Determine max retries based on failure reason
            max_retries = self.MAX_RETRIES_BY_REASON.get(
                create_data.failure_reason,
                create_data.max_retries
            )

            # Calculate next retry time
            next_retry = self._calculate_next_retry(0)

            # Create new entry
            entry = DeadLetterEntry(
                id=self._next_id,
                url=create_data.url,
                domain=domain,
                failure_reason=create_data.failure_reason,
                error_message=create_data.error_message,
                error_details=create_data.error_details,
                retry_count=0,
                max_retries=max_retries,
                original_payload=create_data.original_payload,
                status=DeadLetterStatusEnum.PENDING,
                next_retry_at=next_retry,
                created_at=datetime.utcnow()
            )

            self._entries[self._next_id] = entry
            self._url_index[create_data.url] = self._next_id
            self._next_id += 1

            logger.info(
                f"Added DLQ entry for {create_data.url}: "
                f"reason={create_data.failure_reason.value}, "
                f"next_retry={next_retry}"
            )

            return entry

    async def _update_existing_entry(
        self,
        existing: DeadLetterEntry,
        create_data: DeadLetterCreate
    ) -> DeadLetterEntry:
        """Update existing entry with new failure info"""
        new_retry_count = existing.retry_count + 1

        # Check if max retries exceeded
        if new_retry_count >= existing.max_retries:
            status = DeadLetterStatusEnum.ABANDONED
            next_retry = None
            logger.warning(
                f"DLQ entry {existing.id} abandoned after {new_retry_count} retries"
            )
        else:
            status = DeadLetterStatusEnum.PENDING
            next_retry = self._calculate_next_retry(new_retry_count)

        # Update entry
        updated = DeadLetterEntry(
            id=existing.id,
            url=existing.url,
            domain=existing.domain,
            job_id=existing.job_id,
            failure_reason=create_data.failure_reason,
            error_message=create_data.error_message,
            error_details=create_data.error_details,
            retry_count=new_retry_count,
            max_retries=existing.max_retries,
            last_retry_at=datetime.utcnow(),
            next_retry_at=next_retry,
            status=status,
            original_payload=create_data.original_payload or existing.original_payload,
            created_at=existing.created_at,
            updated_at=datetime.utcnow()
        )

        self._entries[existing.id] = updated
        return updated

    async def get_entry(self, entry_id: int) -> Optional[DeadLetterEntry]:
        """Get entry by ID"""
        return self._entries.get(entry_id)

    async def get_entry_by_url(self, url: str) -> Optional[DeadLetterEntry]:
        """Get entry by URL"""
        entry_id = self._url_index.get(url)
        if entry_id:
            return self._entries.get(entry_id)
        return None

    async def update_entry(
        self,
        entry_id: int,
        update_data: DeadLetterUpdate
    ) -> Optional[DeadLetterEntry]:
        """Update an existing entry"""
        async with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return None

            # Build updated entry
            updated = DeadLetterEntry(
                id=entry.id,
                url=entry.url,
                domain=entry.domain,
                job_id=entry.job_id,
                failure_reason=entry.failure_reason,
                error_message=entry.error_message,
                error_details=entry.error_details,
                retry_count=update_data.retry_count if update_data.retry_count is not None else entry.retry_count,
                max_retries=entry.max_retries,
                last_retry_at=entry.last_retry_at,
                next_retry_at=update_data.next_retry_at if update_data.next_retry_at is not None else entry.next_retry_at,
                status=update_data.status if update_data.status is not None else entry.status,
                original_payload=entry.original_payload,
                resolved_at=datetime.utcnow() if update_data.status == DeadLetterStatusEnum.RESOLVED else entry.resolved_at,
                resolution_notes=update_data.resolution_notes if update_data.resolution_notes is not None else entry.resolution_notes,
                created_at=entry.created_at,
                updated_at=datetime.utcnow()
            )

            self._entries[entry_id] = updated
            return updated

    async def mark_resolved(
        self,
        entry_id: int,
        notes: Optional[str] = None
    ) -> Optional[DeadLetterEntry]:
        """Mark entry as resolved"""
        update = DeadLetterUpdate(
            status=DeadLetterStatusEnum.RESOLVED,
            resolution_notes=notes
        )
        return await self.update_entry(entry_id, update)

    async def mark_processing(self, entry_id: int) -> Optional[DeadLetterEntry]:
        """Mark entry as currently being processed"""
        update = DeadLetterUpdate(status=DeadLetterStatusEnum.PROCESSING)
        return await self.update_entry(entry_id, update)

    async def mark_manual(
        self,
        entry_id: int,
        notes: Optional[str] = None
    ) -> Optional[DeadLetterEntry]:
        """Mark entry as requiring manual intervention"""
        update = DeadLetterUpdate(
            status=DeadLetterStatusEnum.MANUAL,
            resolution_notes=notes
        )
        return await self.update_entry(entry_id, update)

    async def get_pending_entries(
        self,
        limit: int = 100,
        domain: Optional[str] = None
    ) -> List[DeadLetterEntry]:
        """
        Get pending entries ready for retry.

        Args:
            limit: Maximum entries to return
            domain: Optional domain filter

        Returns:
            List of entries ready for retry
        """
        now = datetime.utcnow()
        pending = []

        for entry in self._entries.values():
            if entry.status != DeadLetterStatusEnum.PENDING:
                continue

            if entry.next_retry_at and entry.next_retry_at > now:
                continue

            if domain and entry.domain != domain:
                continue

            pending.append(entry)

            if len(pending) >= limit:
                break

        # Sort by next_retry_at (oldest first)
        pending.sort(key=lambda e: e.next_retry_at or datetime.min)

        return pending

    async def get_entries_by_status(
        self,
        status: DeadLetterStatusEnum,
        limit: int = 100
    ) -> List[DeadLetterEntry]:
        """Get entries by status"""
        entries = [
            e for e in self._entries.values()
            if e.status == status
        ]
        return entries[:limit]

    async def get_entries_by_domain(
        self,
        domain: str,
        limit: int = 100
    ) -> List[DeadLetterEntry]:
        """Get entries by domain"""
        entries = [
            e for e in self._entries.values()
            if e.domain == domain
        ]
        return entries[:limit]

    async def get_entries_by_failure_reason(
        self,
        reason: FailureReasonEnum,
        limit: int = 100
    ) -> List[DeadLetterEntry]:
        """Get entries by failure reason"""
        entries = [
            e for e in self._entries.values()
            if e.failure_reason == reason
        ]
        return entries[:limit]

    async def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry"""
        async with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return False

            del self._entries[entry_id]
            if entry.url in self._url_index:
                del self._url_index[entry.url]

            return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        stats = {
            "total_entries": len(self._entries),
            "by_status": {},
            "by_failure_reason": {},
            "by_domain": {},
        }

        for entry in self._entries.values():
            # Count by status
            status = entry.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Count by failure reason
            reason = entry.failure_reason.value
            stats["by_failure_reason"][reason] = stats["by_failure_reason"].get(reason, 0) + 1

            # Count by domain (top domains)
            domain = entry.domain
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1

        # Sort domains by count, keep top 10
        sorted_domains = sorted(
            stats["by_domain"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        stats["by_domain"] = dict(sorted_domains)

        return stats

    def _calculate_next_retry(self, retry_count: int) -> datetime:
        """
        Calculate next retry time using exponential backoff with jitter.

        Formula: base_delay * 2^retry_count + jitter

        Args:
            retry_count: Current retry count

        Returns:
            Next retry datetime
        """
        import random

        # Exponential backoff
        delay = self.BASE_DELAY * (2 ** retry_count)

        # Cap at max delay
        delay = min(delay, self.MAX_DELAY)

        # Add jitter (±20%)
        jitter = delay * self.JITTER_FACTOR
        delay = delay + random.uniform(-jitter, jitter)

        return datetime.utcnow() + timedelta(seconds=delay)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"

    async def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Remove resolved/abandoned entries older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of entries removed
        """
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            to_remove = []

            for entry_id, entry in self._entries.items():
                if entry.status in [DeadLetterStatusEnum.RESOLVED, DeadLetterStatusEnum.ABANDONED]:
                    if entry.updated_at and entry.updated_at < cutoff:
                        to_remove.append(entry_id)
                    elif entry.created_at < cutoff:
                        to_remove.append(entry_id)

            for entry_id in to_remove:
                entry = self._entries[entry_id]
                del self._entries[entry_id]
                if entry.url in self._url_index:
                    del self._url_index[entry.url]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old DLQ entries")

            return len(to_remove)


# Singleton instance
_dlq_handler: Optional[DLQHandler] = None


def get_dlq_handler() -> DLQHandler:
    """Get singleton DLQ handler instance"""
    global _dlq_handler
    if _dlq_handler is None:
        _dlq_handler = DLQHandler()
    return _dlq_handler
