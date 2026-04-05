"""
Scraping Worker

Consumes scraping jobs from RabbitMQ and processes them.

Features:
- Rate limiting per domain and globally
- Concurrency control with job queue
- Retry logic with exponential backoff
- Memory leak prevention (Playwright context cleanup)
"""
import logging
import json
import uuid
from typing import Dict, Any, Optional
import aio_pika
import httpx

from app.core.config import settings
from app.services.scraper import scraper, ScrapeStatus
from app.services.failure_tracker import failure_tracker
from app.services.event_publisher import get_event_publisher
from app.core.rate_limiter import rate_limiter
from app.core.concurrency import concurrency_limiter

logger = logging.getLogger(__name__)


class ScrapingWorker:
    """
    RabbitMQ consumer that processes scraping jobs.

    Jobs are published by Feed Service when new items are created
    with scrape_full_content=True.
    """

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.event_publisher = None

    async def start(self):
        """Start worker and connect to RabbitMQ"""
        logger.info("Starting scraping worker...")

        # Initialize HTTP client for Feed Service API
        headers = {"X-Service-Name": "scraping-service"}
        if settings.FEED_SERVICE_API_KEY:
            headers["X-Service-Key"] = settings.FEED_SERVICE_API_KEY

        self.http_client = httpx.AsyncClient(
            base_url=settings.FEED_SERVICE_URL,
            headers=headers,
            timeout=30.0
        )

        # Initialize event publisher
        self.event_publisher = await get_event_publisher()

        # Initialize rate limiter
        await rate_limiter.connect()
        logger.info("✅ Rate limiter initialized")

        # Connect to RabbitMQ
        rabbitmq_url = (
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
            f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
        )

        self.connection = await aio_pika.connect_robust(rabbitmq_url)
        self.channel = await self.connection.channel()

        # Set QoS to process N messages at a time
        await self.channel.set_qos(prefetch_count=settings.SCRAPING_WORKER_CONCURRENCY)

        # Declare exchange
        exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        # Declare queue
        self.queue = await self.channel.declare_queue(
            settings.RABBITMQ_QUEUE,
            durable=True
        )
        logger.info(f"Declared queue: {settings.RABBITMQ_QUEUE}")

        # Bind queue to exchange
        # Feed Service publishes "article.created" events
        # Also keep legacy bindings for backwards compatibility
        routing_keys = ["article.created", "feed_item_created", "feed.item.created"]
        for routing_key in routing_keys:
            await self.queue.bind(exchange, routing_key=routing_key)
            logger.info(f"Bound queue to exchange {settings.RABBITMQ_EXCHANGE} with routing key: {routing_key}")

        # Start consuming
        await self.queue.consume(self._process_message)

        logger.info(f"✅ Scraping worker started. Listening on queue: {settings.RABBITMQ_QUEUE}")

    async def stop(self):
        """Stop worker and cleanup"""
        logger.info("Stopping scraping worker...")

        if self.http_client:
            await self.http_client.aclose()

        # Close rate limiter
        await rate_limiter.close()

        if self.connection:
            await self.connection.close()

        logger.info("✅ Scraping worker stopped")

    async def _process_message(self, message: aio_pika.IncomingMessage):
        """
        Process incoming scraping job.

        Message format:
        {
            "feed_id": "uuid",
            "item_id": "uuid",
            "url": "https://...",
            "scrape_method": "auto|httpx|playwright"
        }
        """
        async with message.process():
            try:
                # Parse message
                raw_body = message.body.decode()
                logger.debug(f"Received message: {raw_body[:200]}...")
                message_data = json.loads(raw_body)

                # Extract payload from message envelope
                # Feed Service publishes: {"event_type": "...", "payload": {...}}
                job = message_data.get("payload", message_data)
                logger.debug(f"Extracted job: {job}")

                feed_id = job["feed_id"]
                item_id = job["item_id"]
                url = job["url"]
                scrape_method = job.get("scrape_method", "auto")

                logger.info(f"Processing scraping job: {item_id} - {url}")

                # Check rate limiting
                allowed, reason, retry_after = await rate_limiter.check_scrape_allowed(
                    url=url,
                    feed_id=feed_id
                )

                if not allowed:
                    logger.warning(
                        f"🚦 Rate limit hit for {url}: {reason}. "
                        f"Retry after {retry_after}s"
                    )
                    # Requeue message for later (nack with requeue)
                    await message.nack(requeue=True)
                    return

                # Generate job ID for concurrency tracking
                job_id = str(uuid.uuid4())

                # Execute with concurrency limit
                result = await concurrency_limiter.execute_with_limit(
                    scraper.scrape,
                    url,
                    scrape_method,
                    job_id=job_id,
                    url=url,
                    feed_id=feed_id,
                    item_id=item_id
                )

                # Update Feed Service with results
                await self._update_feed_item(feed_id, item_id, result)

                # Publish events based on scraping result
                if result.status == ScrapeStatus.SUCCESS:
                    await failure_tracker.record_success(feed_id)

                    # Publish item_scraped event for downstream processing
                    await self._publish_item_scraped_event(
                        feed_id=feed_id,
                        item_id=item_id,
                        url=url,
                        word_count=result.word_count,
                        method_used=result.method_used
                    )

                    # Trigger V3 analysis after successful scraping
                    # This ensures articles get analyzed even if they had no content initially
                    if result.content and result.word_count > 50:  # Minimum 50 words
                        await self._publish_analysis_request(
                            item_id=item_id,
                            url=url,
                            content=result.content
                        )

                    logger.info(
                        f"Successfully scraped {item_id}: "
                        f"{result.word_count} words using {result.method_used}"
                    )
                else:
                    await failure_tracker.record_failure(feed_id)

                    # Publish scraping_failed event
                    await self._publish_scraping_failed_event(
                        feed_id=feed_id,
                        item_id=item_id,
                        url=url,
                        error=result.error_message,
                        status=result.status.value
                    )

                    logger.warning(
                        f"Scraping failed for {item_id}: "
                        f"status={result.status}, error={result.error_message}"
                    )

            except Exception as e:
                logger.error(f"Error processing scraping job: {e}", exc_info=True)

    async def _update_feed_item(
        self,
        feed_id: str,
        item_id: str,
        result
    ):
        """
        Update feed item with scraped content via Feed Service API.

        Args:
            feed_id: Feed UUID
            item_id: Item UUID
            result: ScrapeResult object
        """
        try:
            payload = {
                "scraped_at": None,  # Will be set by Feed Service
                "scrape_status": result.status.value,
                "scrape_word_count": result.word_count
            }

            # Only include content if scraping was successful
            if result.status == ScrapeStatus.SUCCESS and result.content:
                payload["content"] = result.content

                # Add author if extracted (join list to string, truncate at 200 chars)
                if result.extracted_authors:
                    authors_str = ", ".join(result.extracted_authors)[:200]
                    payload["author"] = authors_str

                # Add metadata if available (newspaper4k extras)
                if result.extracted_metadata:
                    payload["scraped_metadata"] = result.extracted_metadata

            # Update via API
            response = await self.http_client.patch(
                f"/api/v1/feeds/{feed_id}/items/{item_id}",
                json=payload
            )
            response.raise_for_status()

            logger.debug(f"Updated feed item {item_id} with scraping results")

        except httpx.HTTPError as e:
            logger.error(f"Failed to update feed item {item_id}: {e}")

    async def _publish_item_scraped_event(
        self,
        feed_id: str,
        item_id: str,
        url: str,
        word_count: int,
        method_used: str
    ):
        """
        Publish item_scraped event to RabbitMQ.

        This event triggers downstream processing like OSINT Event Analysis.
        Only published for successful scrapes with substantial content (≥500 words).

        Args:
            feed_id: Feed UUID
            item_id: Item UUID
            url: Scraped URL
            word_count: Number of words scraped
            method_used: Scraping method used (httpx/playwright)
        """
        try:
            # Publish for all successful scrapes (removed 500-word minimum)
            # Content analysis will decide what to analyze based on content length

            # Epic 0.3: Event type format: domain.event_name
            await self.event_publisher.publish_event(
                event_type="scraping.item_scraped",
                payload={
                    "feed_id": feed_id,
                    "item_id": item_id,
                    "url": url,
                    "word_count": word_count,
                    "scrape_method": method_used,
                    "status": "success",  # Add status field for content-analysis
                },
                correlation_id=item_id
            )

            logger.info(f"Published scraping.item_scraped event for {item_id} ({word_count} words)")

        except Exception as e:
            logger.error(f"Failed to publish item_scraped event for {item_id}: {e}")

    async def _publish_scraping_failed_event(
        self,
        feed_id: str,
        item_id: str,
        url: str,
        error: Optional[str],
        status: str
    ):
        """
        Publish scraping_failed event to RabbitMQ.

        This event can be used for monitoring and alerting.

        Args:
            feed_id: Feed UUID
            item_id: Item UUID
            url: URL that failed to scrape
            error: Error message
            status: Scrape status (timeout/blocked/error)
        """
        try:
            await self.event_publisher.publish_event(
                event_type="scraping.failed",
                payload={
                    "feed_id": feed_id,
                    "item_id": item_id,
                    "url": url,
                    "error_message": error,
                    "scrape_status": status,
                },
                correlation_id=item_id
            )

            logger.debug(f"Published scraping_failed event for {item_id}")

        except Exception as e:
            logger.error(f"Failed to publish scraping_failed event for {item_id}: {e}")

    async def _publish_analysis_request(
        self,
        item_id: str,
        url: str,
        content: str
    ):
        """
        Publish analysis.v3.request event to RabbitMQ after successful scraping.

        This ensures articles get analyzed even if they had no content when initially created.
        Fixes the timing issue where articles are created before scraping completes.

        Args:
            item_id: Article UUID
            url: Article URL
            content: Scraped content
        """
        try:
            # Get article title from feed service (we need it for the request)
            response = await self.http_client.get(f"/api/v1/feeds/items/{item_id}")
            if response.status_code != 200:
                logger.warning(f"Failed to get article {item_id} for analysis request: {response.status_code}")
                return

            article_data = response.json()

            # Epic 0.3: Event type format: domain.event_name
            await self.event_publisher.publish_event(
                event_type="analysis.v3.request",
                payload={
                    "article_id": item_id,
                    "title": article_data.get("title", ""),
                    "url": url,
                    "content": content,
                    "run_tier2": True,  # Enable all Tier2 specialists
                    "triggered_by": "scraping_service",  # Track source
                },
                correlation_id=item_id
            )

            logger.info(f"Published analysis.v3.request for {item_id} ({len(content)} chars)")

        except Exception as e:
            logger.error(f"Failed to publish analysis request for {item_id}: {e}")


# Global worker instance
scraping_worker = ScrapingWorker()
