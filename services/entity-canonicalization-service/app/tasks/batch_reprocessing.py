"""
Celery task for batch reprocessing.

This task runs in a separate worker process, avoiding blocking the FastAPI service.
It wraps the BatchReprocessor and provides progress tracking via Celery state.

Usage:
    from app.tasks.batch_reprocessing import batch_reprocess_task

    # Start task
    task = batch_reprocess_task.delay(dry_run=True, min_confidence=0.7)

    # Check status
    result = batch_reprocess_task.AsyncResult(task.id)
    print(result.state)  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'
    print(result.info)   # Progress info
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.api.dependencies import get_db_session
from app.services.canonicalizer import EntityCanonicalizer
from app.services.alias_store import AliasStore
from app.services.wikidata_client import WikidataClient
from app.services.embedding_service import EmbeddingService
from app.services.fuzzy_matcher import FuzzyMatcher
from app.services.batch_reprocessor import BatchReprocessor

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """
    Custom Celery task base class with callbacks for state updates.

    Tracks task lifecycle and updates state with progress information.
    """

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(
    base=CallbackTask,
    bind=True,
    name='entity-canonicalization.batch_reprocess',
    max_retries=0,  # No auto-retry (manual control)
    ignore_result=False,
    track_started=True
)
def batch_reprocess_task(
    self,
    dry_run: bool = False,
    min_confidence: float = 0.7,
    max_duplicate_pairs: int = 30000
) -> Dict[str, Any]:
    """
    Execute batch reprocessing in background worker.

    Args:
        dry_run: If True, don't persist changes (testing mode)
        min_confidence: Minimum similarity score for duplicates (0.0-1.0)
        max_duplicate_pairs: Maximum duplicate pairs to track (memory limit)

    Returns:
        Dict with final statistics and status

    Raises:
        SoftTimeLimitExceeded: If task exceeds 55 minutes (soft limit)
        Exception: Any other error during processing
    """
    logger.info(
        f"Starting batch reprocessing task {self.request.id}: "
        f"dry_run={dry_run}, min_confidence={min_confidence}, max_duplicate_pairs={max_duplicate_pairs}"
    )

    # Update task state to STARTED with initial info
    self.update_state(
        state='STARTED',
        meta={
            'status': 'starting',
            'progress_percent': 0.0,
            'current_phase': 'initializing',
            'dry_run': dry_run
        }
    )

    try:
        # Run async code in new event loop (Celery worker is synchronous)
        result = asyncio.run(
            _run_batch_reprocessing_async(
                task=self,
                dry_run=dry_run,
                min_confidence=min_confidence,
                max_duplicate_pairs=max_duplicate_pairs
            )
        )

        logger.info(
            f"Batch reprocessing task {self.request.id} completed: "
            f"{result['stats']['duplicates_found']} duplicates found, "
            f"{result['stats']['qids_added']} Q-IDs added"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded soft time limit (55 minutes)")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'timeout',
                'error': 'Task exceeded 55 minute time limit'
            }
        )
        raise

    except Exception as e:
        logger.exception(f"Task {self.request.id} failed with exception: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        raise


async def _run_batch_reprocessing_async(
    task: Task,
    dry_run: bool,
    min_confidence: float,
    max_duplicate_pairs: int
) -> Dict[str, Any]:
    """
    Async wrapper for batch reprocessing with progress updates.

    This function runs in the Celery worker's event loop and periodically
    updates the task state with progress information from BatchReprocessor.

    Args:
        task: Celery task instance (for state updates)
        dry_run: Don't persist changes
        min_confidence: Minimum similarity score
        max_duplicate_pairs: Maximum pairs to track

    Returns:
        Final result dict with stats
    """
    # Get database session
    async for session in get_db_session():
        try:
            # Initialize ISOLATED dependencies (NO SINGLETONS!)
            # Each Celery worker gets its own instances to avoid blocking the API
            alias_store = AliasStore(session)
            wikidata_client = WikidataClient()  # Fresh instance, not singleton
            embedding_service = EmbeddingService()  # Fresh instance (OpenAI API, no model loading)
            fuzzy_matcher = FuzzyMatcher()  # Fresh instance (RapidFuzz, lightweight)

            logger.info("Celery worker: Created isolated dependency instances (no shared state with API)")

            # Initialize canonicalizer with isolated dependencies
            canonicalizer = EntityCanonicalizer(
                alias_store=alias_store,
                wikidata_client=wikidata_client,
                embedding_service=embedding_service,
                fuzzy_matcher=fuzzy_matcher
            )

            # Initialize reprocessor
            reprocessor = BatchReprocessor(
                db=session,
                canonicalizer=canonicalizer,
                max_duplicate_pairs=max_duplicate_pairs
            )

            # Start reprocessing (non-blocking)
            # Note: min_confidence is not used by BatchReprocessor.start()
            job_id = await reprocessor.start(dry_run=dry_run)

            # Poll status and update Celery state
            while True:
                status = reprocessor.get_status()

                # Update Celery task state with current progress
                if status.status == "running":
                    task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': status.status,
                            'progress_percent': status.progress_percent,
                            'current_phase': status.current_phase,
                            'stats': {
                                'duplicates_found': status.stats.duplicates_found,
                                'qids_added': status.stats.qids_added,
                                'entities_merged': status.stats.entities_merged,
                                'errors': status.stats.errors
                            },
                            'started_at': status.started_at,  # Already a string
                            'dry_run': dry_run
                        }
                    )

                    # Wait 2 seconds before next poll
                    await asyncio.sleep(2)

                elif status.status == "completed":
                    # Job finished successfully
                    return {
                        'job_id': job_id,
                        'status': status.status,
                        'progress_percent': 100.0,
                        'stats': {
                            'duplicates_found': status.stats.duplicates_found,
                            'qids_added': status.stats.qids_added,
                            'entities_merged': status.stats.entities_merged,
                            'errors': status.stats.errors
                        },
                        'started_at': status.started_at,  # Already a string
                        'completed_at': status.completed_at,  # Already a string
                        'duration_seconds': (
                            # Calculate duration from ISO8601 timestamps
                            (datetime.fromisoformat(status.completed_at) -
                             datetime.fromisoformat(status.started_at)).total_seconds()
                            if status.completed_at and status.started_at
                            else None
                        ),
                        'dry_run': dry_run
                    }

                elif status.status == "failed":
                    # Job failed
                    raise RuntimeError(f"Batch reprocessing failed: {status.error_message}")

                else:
                    # Unknown status
                    logger.warning(f"Unexpected status: {status.status}")
                    await asyncio.sleep(2)

        finally:
            # Session cleanup handled by async context manager
            pass
