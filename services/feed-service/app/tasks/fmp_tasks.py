"""
FMP News Fetching Tasks

Celery tasks for fetching Financial Modeling Prep (FMP) news and publishing to RabbitMQ.

Staggered Scheduling (Rate Limit Safe):
- FMP Starter Plan: 300 calls/minute limit
- 5 Categories: general, stock, forex, crypto, mergers-acquisitions
- Schedule: 1 category per minute, offset by 1 minute each
- Peak Usage: 1 call/min = 0.33% of limit (very safe)
- Daily: 1,440 calls/day

Example Schedule:
    Minute 0: General  (1 call)
    Minute 1: Stock    (1 call)
    Minute 2: Forex    (1 call)
    Minute 3: Crypto   (1 call)
    Minute 4: M&A      (1 call)
    Then repeat every 5 minutes

Architecture:
- FMP news treated as "virtual RSS feed"
- Transformed to article.created events
- Published to RabbitMQ (news.events exchange)
- content-analysis-v2 processes automatically (ZERO code changes)
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from celery import current_task

from app.celery_app import celery_app
from app.adapters import FMPNewsAdapter
from app.services.event_publisher import get_event_publisher
from app.clients.fmp_client import FMPServiceClient

logger = logging.getLogger(__name__)


# FMP Categories (5 total)
FMP_CATEGORIES = [
    "general",                # General financial news
    "stock",                  # Stock market news
    "forex",                  # Foreign exchange news
    "crypto",                 # Cryptocurrency news
    "mergers-acquisitions",   # M&A and SEC filings
]


@celery_app.task(
    name="fmp.fetch_category",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def fetch_fmp_category_task(self, category: str, limit: int = 20) -> Dict[str, Any]:
    """
    Fetch FMP news for a single category and publish to RabbitMQ.

    Args:
        category: FMP category (general|stock|forex|crypto|mergers-acquisitions)
        limit: Number of articles to fetch (default: 20)

    Returns:
        Dictionary with fetch results

    Example:
        {
            "category": "general",
            "success": True,
            "fetched_count": 20,
            "published_count": 18,
            "failed_count": 2,
            "task_id": "abc-123",
            "timestamp": "2025-11-21T10:00:00Z"
        }
    """
    try:
        logger.info(f"Starting FMP news fetch for category: {category}")

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async fetch
        result = loop.run_until_complete(
            _fetch_and_publish_category(category, limit)
        )

        result["task_id"] = current_task.request.id
        result["timestamp"] = datetime.utcnow().isoformat()

        logger.info(f"FMP {category} fetch completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in FMP {category} fetch task: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e)


async def _fetch_and_publish_category(category: str, limit: int) -> Dict[str, Any]:
    """
    Async helper to fetch FMP news and publish to RabbitMQ.

    Args:
        category: FMP category
        limit: Number of articles

    Returns:
        Fetch statistics
    """
    fmp_client = None
    event_publisher = None

    try:
        # Initialize FMP adapter
        fmp_client = FMPServiceClient()
        adapter = FMPNewsAdapter(fmp_client)

        # Fetch news from FMP and transform to article events
        article_events = await adapter.fetch_news(category=category, limit=limit)
        fetched_count = len(article_events)

        if fetched_count == 0:
            logger.warning(f"No FMP {category} news fetched")
            return {
                "category": category,
                "success": True,
                "fetched_count": 0,
                "published_count": 0,
                "failed_count": 0,
            }

        # Get event publisher
        event_publisher = await get_event_publisher()

        # Publish article events to RabbitMQ
        published_count = 0
        failed_count = 0

        for article_event in article_events:
            try:
                success = await event_publisher.publish_event(
                    event_type=article_event["event_type"],
                    payload=article_event["payload"],
                )

                if success:
                    published_count += 1
                else:
                    failed_count += 1
                    logger.warning(
                        f"Failed to publish FMP {category} article",
                        extra={"article": article_event["payload"]["title"]}
                    )

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Error publishing FMP {category} article: {e}",
                    extra={"article": article_event["payload"].get("title", "unknown")}
                )

        logger.info(
            f"FMP {category} publish complete: "
            f"{published_count} published, {failed_count} failed"
        )

        return {
            "category": category,
            "success": True,
            "fetched_count": fetched_count,
            "published_count": published_count,
            "failed_count": failed_count,
        }

    except Exception as e:
        logger.error(f"Error fetching/publishing FMP {category}: {e}")
        return {
            "category": category,
            "success": False,
            "fetched_count": 0,
            "published_count": 0,
            "failed_count": 0,
            "error": str(e),
        }

    finally:
        # Cleanup
        if fmp_client:
            await fmp_client.close()


@celery_app.task(
    name="fmp.fetch_all_categories",
    bind=True,
)
def fetch_all_fmp_categories_task(self, limit: int = 20) -> Dict[str, Any]:
    """
    Master task to fetch all FMP categories with staggered scheduling.

    This task is scheduled every 5 minutes and spawns 5 subtasks with 1-minute offsets.

    Args:
        limit: Number of articles per category

    Returns:
        Summary of all category fetches

    Schedule:
        Minute 0: Spawn general task (executes immediately)
        Minute 1: Spawn stock task (1 min countdown)
        Minute 2: Spawn forex task (2 min countdown)
        Minute 3: Spawn crypto task (3 min countdown)
        Minute 4: Spawn M&A task (4 min countdown)

    Example:
        # Beat schedule in celery_app.py:
        "fmp-fetch-all": {
            "task": "fmp.fetch_all_categories",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        }
    """
    try:
        logger.info("Starting staggered FMP news fetch for all categories")

        # Spawn tasks with countdown (staggered execution)
        task_ids = []

        for idx, category in enumerate(FMP_CATEGORIES):
            # Countdown in seconds: 0, 60, 120, 180, 240
            countdown_seconds = idx * 60

            # Spawn subtask with countdown
            task = fetch_fmp_category_task.apply_async(
                args=(category, limit),
                countdown=countdown_seconds,
            )
            task_ids.append(task.id)

            logger.info(
                f"Spawned FMP {category} task (countdown: {countdown_seconds}s) "
                f"[task_id: {task.id}]"
            )

        result = {
            "success": True,
            "categories": FMP_CATEGORIES,
            "task_ids": task_ids,
            "total_categories": len(FMP_CATEGORIES),
            "master_task_id": current_task.request.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"All FMP category tasks spawned: {result}")
        return result

    except Exception as e:
        logger.error(f"Error spawning FMP category tasks: {e}")
        return {
            "success": False,
            "error": str(e),
            "master_task_id": current_task.request.id,
        }


@celery_app.task(name="fmp.test_single_category")
def test_fmp_fetch_task(category: str = "general", limit: int = 5) -> Dict[str, Any]:
    """
    Test task to fetch a single FMP category (for manual testing).

    Usage:
        >>> from app.tasks.fmp_tasks import test_fmp_fetch_task
        >>> result = test_fmp_fetch_task.delay("general", 5)
        >>> result.get()

    Args:
        category: FMP category (default: general)
        limit: Number of articles (default: 5)

    Returns:
        Fetch results
    """
    return fetch_fmp_category_task(category, limit)
