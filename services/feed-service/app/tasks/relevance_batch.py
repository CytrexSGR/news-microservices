"""
Celery task for batch updating relevance scores.

Epic 2.2 Task 3: Batch processing for recalculating time-decay relevance
scores for articles. Designed to handle 22k+ articles efficiently.

Performance target: 22k articles < 30 seconds.

The task runs periodically via Celery Beat to keep relevance scores
up-to-date as articles age and decay in relevance.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import select

from app.celery_app import celery_app
from app.db import AsyncSessionLocal
from app.models import FeedItem
from app.services.relevance_calculator import get_relevance_calculator

logger = logging.getLogger(__name__)

# Batch processing settings
DEFAULT_BATCH_SIZE = 1000
DEFAULT_DAYS = 7  # Process articles from last 7 days by default


async def _batch_update_relevance_scores(
    days: int = DEFAULT_DAYS,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Dict[str, Any]:
    """
    Batch update relevance scores for recent articles.

    Fetches articles from the specified time window and recalculates
    their relevance scores based on time-decay algorithm.

    Args:
        days: Number of days to look back for articles (default: 7)
        batch_size: Number of articles to process per batch (default: 1000)

    Returns:
        Dict with statistics:
        - processed: Total articles processed
        - updated: Articles successfully updated
        - errors: Number of errors encountered
        - reference_time: Reference timestamp used for decay calculation
    """
    calculator = get_relevance_calculator()
    reference_time = datetime.now(timezone.utc)
    cutoff_date = reference_time - timedelta(days=days)

    processed_count = 0
    updated_count = 0
    error_count = 0

    logger.info(
        f"Starting batch relevance score update: "
        f"days={days}, batch_size={batch_size}, cutoff={cutoff_date.isoformat()}"
    )

    async with AsyncSessionLocal() as session:
        # Process in batches using offset pagination
        offset = 0

        while True:
            # Query articles within time window
            query = (
                select(FeedItem)
                .where(FeedItem.created_at >= cutoff_date)
                .order_by(FeedItem.created_at.desc())
                .offset(offset)
                .limit(batch_size)
            )

            result = await session.execute(query)
            articles = result.scalars().all()

            if not articles:
                logger.debug(f"No more articles to process at offset {offset}")
                break

            batch_updated = 0
            batch_errors = 0

            # Build article data for batch calculation
            article_data = []
            for article in articles:
                processed_count += 1

                if article.published_at is None:
                    logger.debug(f"Article {article.id} has no published_at, skipping")
                    continue

                article_data.append({
                    "id": str(article.id),
                    "published_at": article.published_at,
                    "category": getattr(article, "category", None),
                    "quality_score": getattr(article, "quality_score", None),
                })

            # Calculate scores for the batch
            if article_data:
                scores = calculator.calculate_batch(article_data, reference_time)

                # Update scores in database
                for article in articles:
                    if article.published_at is None:
                        continue

                    article_id = str(article.id)
                    if article_id in scores:
                        try:
                            article.relevance_score = scores[article_id]
                            article.relevance_calculated_at = reference_time
                            batch_updated += 1
                        except Exception as e:
                            logger.error(f"Error updating article {article_id}: {e}")
                            batch_errors += 1

                # Commit batch updates
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Error committing batch at offset {offset}: {e}")
                    await session.rollback()
                    batch_errors += len(article_data)
                    batch_updated = 0

            updated_count += batch_updated
            error_count += batch_errors
            offset += batch_size

            logger.debug(
                f"Batch complete: offset={offset}, "
                f"batch_updated={batch_updated}, total_updated={updated_count}"
            )

    logger.info(
        f"Batch relevance update complete: "
        f"processed={processed_count}, updated={updated_count}, errors={error_count}"
    )

    return {
        "processed": processed_count,
        "updated": updated_count,
        "errors": error_count,
        "reference_time": reference_time.isoformat(),
    }


@celery_app.task(
    name="feed.update_relevance_scores",
    bind=True,
    max_retries=1,
    default_retry_delay=300,  # Retry after 5 minutes
)
def update_relevance_scores_task(
    self,
    days: int = DEFAULT_DAYS,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Dict[str, Any]:
    """
    Celery task to update relevance scores in batch.

    This task runs periodically (via Celery Beat) to recalculate
    time-decay relevance scores for all recent articles.

    Args:
        days: Number of days to look back (default: 7)
        batch_size: Articles per batch (default: 1000)

    Returns:
        Dict with update statistics (processed, updated, errors)
    """
    try:
        logger.info(
            f"Starting relevance score update task: days={days}, batch_size={batch_size}"
        )

        # Get or create event loop for async execution
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _batch_update_relevance_scores(days=days, batch_size=batch_size)
        )

        logger.info(f"Relevance score update task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in relevance score update task: {e}", exc_info=True)
        raise self.retry(exc=e)
