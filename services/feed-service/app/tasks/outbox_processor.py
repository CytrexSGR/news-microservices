"""
Outbox Processor - Celery Task

Implements the Outbox Pattern for reliable event publishing.
Reads pending events from event_outbox table and publishes them to RabbitMQ.

Runs every 5 seconds to ensure fast event delivery while guaranteeing
at-least-once delivery even if RabbitMQ is temporarily unavailable.

Architecture:
1. Feed Service writes events to outbox table (transactional with domain changes)
2. This processor reads pending events and publishes to RabbitMQ
3. Marks events as 'published' on success
4. Retries failed events with exponential backoff

Benefits:
- Transactional event publishing (atomicity with DB changes)
- Resilient to RabbitMQ outages
- No lost events
- Observable (can query outbox for pending/failed events)
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.celery_app import celery_app
from app.services.event_publisher import EventPublisher
from celery.signals import worker_shutdown


logger = logging.getLogger(__name__)

# Worker-process level event publisher and its event loop
# Stored per-worker to reuse connection across tasks in the same loop
_worker_publisher: Optional[EventPublisher] = None
_worker_loop_id: Optional[int] = None


async def get_or_create_publisher() -> EventPublisher:
    """
    Get or create event publisher for current event loop.

    This ensures the publisher is always created in the same event loop
    that's calling it, avoiding "attached to different loop" errors.

    The publisher is reused across tasks in the same worker process
    as long as they use the same event loop.
    """
    global _worker_publisher, _worker_loop_id

    current_loop = asyncio.get_event_loop()
    current_loop_id = id(current_loop)

    # Create new publisher if:
    # - No publisher exists yet
    # - Event loop has changed (shouldn't happen but defensive)
    if _worker_publisher is None or _worker_loop_id != current_loop_id:
        logger.info(f"Creating new event publisher for loop {current_loop_id}")

        # Close old publisher if it exists (event loop changed)
        if _worker_publisher is not None:
            try:
                await _worker_publisher.disconnect()
            except Exception as e:
                logger.warning(f"Failed to close old publisher: {e}")

        # Create new publisher in current event loop
        _worker_publisher = EventPublisher()
        await _worker_publisher.connect()
        _worker_loop_id = current_loop_id

        logger.info(f"Event publisher created and connected for loop {current_loop_id}")

    return _worker_publisher


class OutboxProcessor:
    """
    Processes events from outbox table and publishes to RabbitMQ.

    Uses persistent RabbitMQ connection (per-worker) to avoid connection overhead
    and prevent message loss during connection teardown.
    """

    def __init__(self):
        """Initialize outbox processor."""
        self.max_retries = 10  # Max retry attempts before marking as 'failed'
        self.batch_size = 100  # Process up to 100 events per run

    async def process_outbox(self) -> Dict[str, int]:
        """
        Process pending events from outbox.

        Returns:
            Dict with processing statistics
        """
        stats = {
            "processed": 0,
            "published": 0,
            "failed": 0,
            "retried": 0,
        }

        async with AsyncSessionLocal() as session:
            try:
                # Get pending events (ordered by creation time for FIFO)
                events = await self._get_pending_events(session)

                if not events:
                    logger.debug("No pending events in outbox")
                    return stats

                logger.info(f"Processing {len(events)} pending events from outbox")

                # Process each event
                for event in events:
                    stats["processed"] += 1
                    success = await self._publish_event(session, event)

                    if success:
                        stats["published"] += 1
                    else:
                        # Event publish failed, will retry next run
                        stats["retried"] += 1

                # Commit all status updates
                await session.commit()

                logger.info(
                    f"Outbox processing complete: {stats['published']} published, "
                    f"{stats['retried']} retried, {stats['failed']} failed"
                )

                return stats

            except Exception as e:
                logger.error(f"Outbox processing error: {e}", exc_info=True)
                await session.rollback()
                raise

    async def _get_pending_events(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Get pending events from outbox.

        Args:
            session: Database session

        Returns:
            List of pending events
        """
        query = text("""
            SELECT
                id,
                event_type,
                payload,
                retry_count,
                correlation_id
            FROM event_outbox
            WHERE status = 'pending'
              AND retry_count < :max_retries
            ORDER BY created_at
            LIMIT :batch_size
        """)

        result = await session.execute(
            query,
            {"max_retries": self.max_retries, "batch_size": self.batch_size}
        )

        events = []
        for row in result:
            events.append({
                "id": row[0],
                "event_type": row[1],
                "payload": row[2],  # Already deserialized from JSONB
                "retry_count": row[3],
                "correlation_id": row[4],
            })

        return events

    async def _publish_event(
        self,
        session: AsyncSession,
        event: Dict[str, Any]
    ) -> bool:
        """
        Publish a single event to RabbitMQ.

        Args:
            session: Database session
            event: Event data from outbox

        Returns:
            True if published successfully, False otherwise
        """
        event_id = event["id"]
        event_type = event["event_type"]
        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        try:
            # Get or create publisher for current event loop
            publisher = await get_or_create_publisher()

            # Publish event to RabbitMQ (with publisher confirms)
            success = await publisher.publish_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
            )

            if success:
                # Mark as published
                await session.execute(
                    text("""
                        UPDATE event_outbox
                        SET status = 'published',
                            published_at = NOW()
                        WHERE id = :id
                    """),
                    {"id": event_id}
                )

                logger.debug(f"Published event {event_id} ({event_type})")
                return True
            else:
                # Publish failed, increment retry count
                await self._increment_retry(session, event_id)
                logger.warning(f"Failed to publish event {event_id} ({event_type})")
                return False

        except Exception as e:
            # Unexpected error, increment retry count
            await self._increment_retry(session, event_id, error=str(e))
            logger.error(
                f"Error publishing event {event_id} ({event_type}): {e}",
                exc_info=True
            )
            return False

    async def _increment_retry(
        self,
        session: AsyncSession,
        event_id: str,
        error: str = None
    ) -> None:
        """
        Increment retry count for failed event.

        Args:
            session: Database session
            event_id: Event ID
            error: Optional error message
        """
        # Check if max retries exceeded
        query = text("""
            UPDATE event_outbox
            SET retry_count = retry_count + 1,
                last_error = :error,
                status = CASE
                    WHEN retry_count + 1 >= :max_retries THEN 'failed'
                    ELSE status
                END
            WHERE id = :id
            RETURNING retry_count
        """)

        result = await session.execute(
            query,
            {
                "id": event_id,
                "error": error,
                "max_retries": self.max_retries
            }
        )

        row = result.fetchone()
        if row:
            retry_count = row[0]
            if retry_count >= self.max_retries:
                logger.error(
                    f"Event {event_id} marked as 'failed' after {retry_count} retries. "
                    f"Last error: {error}"
                )


# =============================================================================
# Celery Task
# =============================================================================

# Singleton processor per worker process (avoid creating 720 instances/hour)
_outbox_processor = None


def _get_outbox_processor() -> OutboxProcessor:
    """Get or create singleton OutboxProcessor for this worker process"""
    global _outbox_processor
    if _outbox_processor is None:
        _outbox_processor = OutboxProcessor()
    return _outbox_processor


@celery_app.task(name="outbox_processor.process_outbox")
def process_outbox_task():
    """
    Celery task wrapper for outbox processing.

    Runs every 5 seconds (configured in celerybeat schedule).
    """
    try:
        processor = _get_outbox_processor()

        # ✅ FIX: Reuse existing event loop instead of creating new one each time
        # Creating new_event_loop() for every task causes "different loop" errors
        # because async_engine and AsyncSessionLocal are bound to the first loop.
        #
        # Solution: Get existing loop or create one if needed, then reuse it.
        try:
            loop = asyncio.get_event_loop()
            # If loop is closed, we need a new one
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        stats = loop.run_until_complete(processor.process_outbox())

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Outbox processing task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# =============================================================================
# Celery Worker Shutdown Handler
# =============================================================================

@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """
    Disconnect RabbitMQ on Celery worker shutdown.

    Ensures the persistent connection is properly closed when
    the worker terminates, preventing connection leaks.
    """
    global _worker_publisher, _worker_loop_id

    logger.info("Celery worker shutting down - closing RabbitMQ connection")

    if _worker_publisher:
        try:
            # Try to get current event loop, or create one if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(_worker_publisher.disconnect())
            logger.info("Worker RabbitMQ connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection during shutdown: {e}", exc_info=True)
        finally:
            _worker_publisher = None
            _worker_loop_id = None
