"""
Proposal Queue for Graceful Degradation

Issue #8: Queues proposals that fail to submit and retries them later.

Provides graceful degradation when the Ontology Proposals API is unavailable.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import deque

from app.models.proposal import OntologyChangeProposal
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueuedProposal:
    """A proposal queued for retry."""
    proposal: OntologyChangeProposal
    queued_at: datetime
    retry_count: int = 0
    last_error: Optional[str] = None
    next_retry_at: datetime = field(default_factory=datetime.now)


class ProposalQueue:
    """
    Queue for failed proposal submissions.

    Issue #8: Implements graceful degradation by:
    1. Queuing proposals that fail to submit
    2. Retrying with exponential backoff
    3. Maintaining service health status

    Attributes:
        max_queue_size: Maximum proposals to queue (prevents memory issues)
        max_retries: Maximum retry attempts per proposal
        base_retry_delay_seconds: Initial retry delay (doubles each attempt)
    """

    def __init__(
        self,
        max_queue_size: int = 1000,
        max_retries: int = 5,
        base_retry_delay_seconds: int = 60
    ):
        self.max_queue_size = max_queue_size
        self.max_retries = max_retries
        self.base_retry_delay_seconds = base_retry_delay_seconds

        self._queue: deque[QueuedProposal] = deque(maxlen=max_queue_size)
        self._failed_permanently: List[QueuedProposal] = []
        self._lock = asyncio.Lock()

        # Stats tracking
        self._total_queued = 0
        self._total_retried = 0
        self._total_failed = 0

        logger.info(
            f"ProposalQueue initialized: max_size={max_queue_size}, "
            f"max_retries={max_retries}, base_delay={base_retry_delay_seconds}s"
        )

    async def enqueue(
        self,
        proposal: OntologyChangeProposal,
        error: str
    ) -> bool:
        """
        Add a failed proposal to the retry queue.

        Args:
            proposal: The proposal that failed to submit
            error: Error message from the submission attempt

        Returns:
            True if queued successfully, False if queue is full
        """
        async with self._lock:
            if len(self._queue) >= self.max_queue_size:
                logger.warning(
                    f"Proposal queue full ({self.max_queue_size}), "
                    f"dropping proposal {proposal.proposal_id}"
                )
                return False

            queued = QueuedProposal(
                proposal=proposal,
                queued_at=datetime.now(),
                retry_count=0,
                last_error=error,
                next_retry_at=datetime.now() + timedelta(
                    seconds=self.base_retry_delay_seconds
                )
            )

            self._queue.append(queued)
            self._total_queued += 1

            logger.info(
                f"Queued proposal {proposal.proposal_id} for retry "
                f"(queue size: {len(self._queue)})"
            )

            return True

    async def get_ready_for_retry(self) -> List[QueuedProposal]:
        """
        Get proposals that are ready for retry.

        Returns:
            List of proposals ready to retry
        """
        async with self._lock:
            now = datetime.now()
            ready = []

            # Find all ready proposals
            remaining = deque()
            while self._queue:
                item = self._queue.popleft()
                if item.next_retry_at <= now:
                    ready.append(item)
                else:
                    remaining.append(item)

            # Put back the ones not ready yet
            self._queue = remaining

            if ready:
                logger.debug(f"Found {len(ready)} proposals ready for retry")

            return ready

    async def requeue_failed(
        self,
        queued: QueuedProposal,
        error: str
    ) -> bool:
        """
        Re-queue a proposal that failed retry.

        Args:
            queued: The queued proposal that failed again
            error: Error message from retry attempt

        Returns:
            True if requeued, False if max retries exceeded
        """
        async with self._lock:
            queued.retry_count += 1
            queued.last_error = error
            self._total_retried += 1

            if queued.retry_count >= self.max_retries:
                logger.warning(
                    f"Proposal {queued.proposal.proposal_id} exceeded max retries "
                    f"({self.max_retries}), marking as permanently failed"
                )
                self._failed_permanently.append(queued)
                self._total_failed += 1

                # Keep only last 100 permanently failed
                if len(self._failed_permanently) > 100:
                    self._failed_permanently = self._failed_permanently[-100:]

                return False

            # Calculate exponential backoff
            delay = self.base_retry_delay_seconds * (2 ** queued.retry_count)
            # Cap at 1 hour
            delay = min(delay, 3600)

            queued.next_retry_at = datetime.now() + timedelta(seconds=delay)
            self._queue.append(queued)

            logger.info(
                f"Requeued proposal {queued.proposal.proposal_id} for retry "
                f"(attempt {queued.retry_count + 1}/{self.max_retries}, "
                f"next retry in {delay}s)"
            )

            return True

    async def mark_success(self, queued: QueuedProposal) -> None:
        """
        Mark a queued proposal as successfully submitted.

        Args:
            queued: The proposal that was successfully submitted
        """
        async with self._lock:
            logger.info(
                f"Queued proposal {queued.proposal.proposal_id} successfully "
                f"submitted after {queued.retry_count} retries"
            )

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get queue status for health checks.

        Returns:
            Queue statistics and status
        """
        return {
            "queue_size": len(self._queue),
            "max_queue_size": self.max_queue_size,
            "permanently_failed": len(self._failed_permanently),
            "total_queued": self._total_queued,
            "total_retried": self._total_retried,
            "total_failed": self._total_failed,
            "is_healthy": len(self._queue) < self.max_queue_size * 0.9,
            "has_pending_retries": len(self._queue) > 0
        }

    async def clear_queue(self) -> int:
        """
        Clear the retry queue.

        Returns:
            Number of items cleared
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            logger.info(f"Cleared {count} items from retry queue")
            return count

    def get_failed_proposals(self) -> List[Dict[str, Any]]:
        """
        Get list of permanently failed proposals.

        Returns:
            List of failed proposal info
        """
        return [
            {
                "proposal_id": qp.proposal.proposal_id,
                "queued_at": qp.queued_at.isoformat(),
                "retry_count": qp.retry_count,
                "last_error": qp.last_error,
                "change_type": qp.proposal.change_type.value
            }
            for qp in self._failed_permanently
        ]


# Global queue instance
proposal_queue = ProposalQueue(
    max_queue_size=1000,
    max_retries=5,
    base_retry_delay_seconds=60
)
