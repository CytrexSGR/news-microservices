"""
Feed fetching service - migrated and improved from monolith

Handles RSS/Atom feed fetching with circuit breaker pattern,
content deduplication, and error recovery.

Task 406 Improvements:
- Production-ready circuit breaker with Prometheus metrics
- Retry logic with exponential backoff
- Resilient HTTP client for feed fetching

Epic 1.2 Improvements:
- SimHash-based duplicate detection at ingestion
- Near-duplicate flagging for human review
- Prometheus metrics for duplicate rates
"""
import hashlib
import feedparser
import logging
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter

from app.db import AsyncSessionLocal
from app.models import Feed, FeedItem, FetchLog, FeedHealth, FeedStatus
from news_intelligence_common import SimHasher
from app.config import settings
from app.services.event_publisher import get_event_publisher
from app.resilience import (
    ResilientHttpClient,
    CircuitBreakerConfig,
    RetryConfig,
    CircuitBreakerOpenError,
)

# Epic 1.2: Deduplication metrics
DUPLICATE_REJECTED_TOTAL = Counter(
    "feed_duplicate_rejected_total",
    "Total articles rejected as duplicates (Hamming distance <= 3)",
    ["feed_id"]
)

NEAR_DUPLICATE_FLAGGED_TOTAL = Counter(
    "feed_near_duplicate_flagged_total",
    "Total articles flagged as near-duplicates for review (Hamming distance 4-7)",
    ["feed_id"]
)

logger = logging.getLogger(__name__)


class FeedFetcher:
    """Service for fetching and processing RSS/Atom feeds with resilience patterns."""

    def __init__(self):
        self._event_publisher = None
        self.http_clients = {}  # Per-feed HTTP clients with circuit breakers

    async def _get_publisher(self):
        """Get singleton event publisher (lazy init)."""
        if self._event_publisher is None:
            self._event_publisher = await get_event_publisher()
        return self._event_publisher

    def get_http_client(self, feed_id: int, feed_url: str) -> ResilientHttpClient:
        """
        Get or create resilient HTTP client for a feed.

        Each feed gets its own client with dedicated circuit breaker to prevent
        one bad feed from affecting others.
        """
        if feed_id not in self.http_clients:
            # Create circuit breaker config
            # Sanitize feed_id for Prometheus metric names (only alphanumeric and underscores)
            sanitized_feed_id = str(feed_id).replace("-", "_")
            cb_config = CircuitBreakerConfig(
                failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                success_threshold=settings.CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
                timeout_seconds=settings.CIRCUIT_BREAKER_TIMEOUT_SECONDS,
                enable_metrics=True,
                name=f"feed_{sanitized_feed_id}",  # Unique name for Prometheus metrics
            )

            # Create retry config
            retry_config = RetryConfig(
                max_retries=settings.MAX_FETCH_RETRIES,
                initial_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True,
            )

            # Create resilient HTTP client
            self.http_clients[feed_id] = ResilientHttpClient(
                circuit_breaker_config=cb_config,
                retry_config=retry_config,
                timeout=settings.FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={"User-Agent": settings.USER_AGENT},
            )

        return self.http_clients[feed_id]

    @asynccontextmanager
    async def get_db_session(self):
        """
        Get a database session.

        NOTE: Session may be committed manually during the transaction
        (e.g., before publishing events). Final commit here is safe/idempotent.
        """
        async with AsyncSessionLocal() as session:
            try:
                yield session
                # Commit if not already committed (idempotent - safe to call multiple times)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def fetch_feed(self, feed_id: int) -> Tuple[bool, int]:
        """
        Fetch a feed and return success status and new items count.

        Uses ResilientHttpClient with circuit breaker and retry logic.

        Args:
            feed_id: The ID of the feed to fetch

        Returns:
            Tuple of (success: bool, items_count: int)
        """
        try:
            async with self.get_db_session() as session:
                return await self._fetch_feed_internal(session, feed_id)
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker open for feed {feed_id}: {e}")
            return False, 0
        except Exception as e:
            logger.error(f"Error fetching feed {feed_id}: {e}", exc_info=True)
            return False, 0

    async def _fetch_feed_internal(
        self,
        session: AsyncSession,
        feed_id: int,
    ) -> Tuple[bool, int]:
        """Internal fetch logic with resilient HTTP client."""
        from sqlalchemy import text

        # Get feed from database
        result = await session.execute(select(Feed).where(Feed.id == feed_id))
        feed = result.scalar_one_or_none()

        if not feed:
            logger.error(f"Feed {feed_id} not found")
            return False, 0

        # Look up source_id from mapping table (created during feeds→sources migration)
        source_id = None
        try:
            mapping_result = await session.execute(
                text("SELECT source_id FROM _feed_to_source_mapping WHERE feed_id = :feed_id"),
                {"feed_id": feed_id}
            )
            row = mapping_result.first()
            if row:
                source_id = row[0]
        except Exception as e:
            # Mapping table might not exist yet (pre-migration) - that's fine
            logger.debug(f"Could not look up source_id for feed {feed_id}: {e}")

        logger.info(f"Starting fetch for feed {feed_id}: {feed.url}")

        # Create fetch log entry
        fetch_log = FetchLog(
            feed_id=feed_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(fetch_log)
        await session.flush()

        # Get resilient HTTP client for this feed
        http_client = self.get_http_client(feed_id, str(feed.url))

        try:
            # Fetch the feed with circuit breaker + retry
            async with http_client:
                # Build headers
                headers = {}

                # Add conditional headers if available
                if feed.etag:
                    headers["If-None-Match"] = feed.etag
                if feed.last_modified:
                    headers["If-Modified-Since"] = feed.last_modified

                start_time = datetime.now(timezone.utc)
                response = await http_client.get(str(feed.url), headers=headers)
                response_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

                # Handle 304 Not Modified
                if response.status_code == 304:
                    logger.info(f"Feed {feed_id} not modified since last fetch")

                    # ✅ FIX: Update last_fetched_at even for 304 responses
                    # The feed was checked (no new content), but we should record when we checked it
                    now = datetime.now(timezone.utc)
                    feed.last_fetched_at = now
                    feed.next_fetch_at = now + timedelta(minutes=feed.fetch_interval)

                    fetch_log.status = "success"
                    fetch_log.items_found = 0
                    fetch_log.items_new = 0
                    fetch_log.response_time_ms = response_time_ms
                    fetch_log.completed_at = datetime.now(timezone.utc)
                    await self._update_feed_health(session, feed_id, True, response_time_ms)
                    # Circuit breaker success already recorded by ResilientHttpClient
                    return True, 0

                # Response status already checked by ResilientHttpClient

                # Parse the feed
                parsed = feedparser.parse(response.content)

                if parsed.bozo:
                    raise Exception(f"Feed parse error: {parsed.get('bozo_exception', 'Unknown error')}")

                # Update feed metadata
                now = datetime.now(timezone.utc)
                feed.last_fetched_at = now

                # Update next_fetch_at for intelligent scheduling
                feed.next_fetch_at = now + timedelta(minutes=feed.fetch_interval)

                if "etag" in response.headers:
                    feed.etag = response.headers["etag"]
                if "last-modified" in response.headers:
                    feed.last_modified = response.headers["last-modified"]

                # Update feed title and description if not set
                if not feed.name and parsed.feed.get("title"):
                    feed.name = parsed.feed.title[:200]
                if not feed.description and parsed.feed.get("description"):
                    feed.description = parsed.feed.description

                # Process entries
                items_found = len(parsed.entries)
                items_new = 0
                new_item_data = []  # Collect item data for event publishing

                for entry in parsed.entries[:settings.MAX_ITEMS_PER_FETCH]:
                    try:
                        item_data = await self._process_feed_entry(session, feed, entry, source_id)
                        if item_data:
                            items_new += 1
                            new_item_data.append(item_data)
                    except Exception as e:
                        logger.warning(f"Error processing entry: {e}")
                        continue

                # Update feed statistics
                await self._update_feed_statistics(session, feed_id)

                # Update fetch log
                fetch_log.status = "success"
                fetch_log.items_found = items_found
                fetch_log.items_new = items_new
                fetch_log.response_time_ms = response_time_ms
                fetch_log.response_status_code = response.status_code
                fetch_log.completed_at = datetime.now(timezone.utc)
                fetch_log.duration = (fetch_log.completed_at - fetch_log.started_at).total_seconds()

                # Update feed health
                await self._update_feed_health(session, feed_id, True, response_time_ms)

                # Reset feed status if it was in error
                if feed.status == FeedStatus.ERROR.value:
                    feed.status = FeedStatus.ACTIVE.value
                    feed.last_error_message = None
                    feed.last_error_at = None
                    logger.info(f"Feed {feed_id} recovered from ERROR status")

                # Circuit breaker success already recorded by ResilientHttpClient

                # ⚡ OUTBOX PATTERN: Store events in outbox table (transactional)
                # Events will be published by separate outbox_processor
                # This GUARANTEES at-least-once delivery even if publish fails
                if items_new > 0:
                    from sqlalchemy import text
                    import json

                    # Extract item IDs for feed.fetch_completed event
                    new_item_ids = [item["item_id"] for item in new_item_data]

                    # 1. Insert feed.fetch_completed event to outbox
                    await session.execute(
                        text("""
                            INSERT INTO event_outbox (event_type, payload)
                            VALUES (:event_type, :payload)
                        """),
                        {
                            "event_type": "feed.fetch_completed",
                            "payload": json.dumps({
                                "feed_id": str(feed_id),
                                "items_found": items_found,
                                "items_new": items_new,
                                "item_ids": [str(item_id) for item_id in new_item_ids],
                            })
                        }
                    )

                    # 2. Insert individual article events to outbox
                    for item_data in new_item_data:
                        # Scraping event if enabled
                        if item_data["scrape_full_content"] and item_data["link"]:
                            await session.execute(
                                text("""
                                    INSERT INTO event_outbox (event_type, payload)
                                    VALUES (:event_type, :payload)
                                """),
                                {
                                    "event_type": "feed.item.created",
                                    "payload": json.dumps({
                                        "feed_id": str(item_data["feed_id"]),
                                        "item_id": str(item_data["item_id"]),
                                        "url": item_data["link"],
                                        "scrape_method": item_data["scrape_method"],
                                    })
                                }
                            )

                        # article.created event for analysis pipeline (V2 - legacy)
                        await session.execute(
                            text("""
                                INSERT INTO event_outbox (event_type, payload)
                                VALUES (:event_type, :payload)
                            """),
                            {
                                "event_type": "article.created",
                                "payload": json.dumps({
                                    "item_id": str(item_data["item_id"]),
                                    "feed_id": str(item_data["feed_id"]),
                                    "source_id": item_data.get("source_id"),  # Unified source reference
                                    "title": item_data["title"],
                                    "link": item_data["link"],
                                    "has_content": item_data["has_content"],
                                    "analysis_config": item_data["analysis_config"],
                                })
                            }
                        )

                        # analysis.v3.request event for V3 pipeline
                        # ONLY publish if article has content AND is NOT using scraping
                        # If scraping is enabled, scraping-service will publish analysis request after scraping completes
                        if item_data["content"] and not item_data["scrape_full_content"]:
                            await session.execute(
                                text("""
                                    INSERT INTO event_outbox (event_type, payload)
                                    VALUES (:event_type, :payload)
                                """),
                                {
                                    "event_type": "analysis.v3.request",
                                    "payload": json.dumps({
                                        "article_id": str(item_data["item_id"]),
                                        "title": item_data["title"],
                                        "url": item_data["link"],
                                        "content": item_data["content"],
                                        "run_tier2": True,  # Enable all Tier2 specialists
                                    })
                                }
                            )
                        elif item_data["scrape_full_content"]:
                            logger.info(
                                f"Skipping immediate V3 analysis for article {item_data['item_id']} "
                                f"(will be triggered after scraping): {item_data['title']}"
                            )
                        else:
                            logger.warning(
                                f"Skipping V3 analysis for article {item_data['item_id']} "
                                f"(empty content): {item_data['title']}"
                            )

                    logger.info(f"Stored {items_new} article events in outbox (transactional)")

                # ⚡ CRITICAL: Commit items + events in SINGLE transaction
                # Guarantees atomicity: either both saved or both rolled back
                await session.commit()
                logger.info(f"Committed {items_new} new items + events to database")

                logger.info(f"Feed {feed_id} fetch completed: {items_new}/{items_found} new items")
                return True, items_new

        except Exception as e:
            logger.error(f"Error fetching feed {feed_id}: {e}")

            # Update fetch log
            fetch_log.status = "error"
            fetch_log.error = str(e)[:500]
            fetch_log.completed_at = datetime.now(timezone.utc)
            fetch_log.duration = (fetch_log.completed_at - fetch_log.started_at).total_seconds()

            # Update feed status
            feed.status = FeedStatus.ERROR.value
            feed.last_error_message = str(e)[:500]
            feed.last_error_at = datetime.now(timezone.utc)
            feed.consecutive_failures += 1

            # Auto-deactivate feed after 10 consecutive failures
            if feed.consecutive_failures >= 10:
                feed.is_active = False
                feed.status = FeedStatus.INACTIVE.value
                logger.error(
                    f"Feed {feed_id} auto-deactivated after {feed.consecutive_failures} "
                    f"consecutive failures. Last error: {str(e)[:100]}"
                )

            # Update health
            await self._update_feed_health(session, feed_id, False)

            # Circuit breaker failure already recorded by ResilientHttpClient

            # Publish failure event
            publisher = await self._get_publisher()
            await publisher.publish_event(
                "feed.fetch_failed",
                {
                    "feed_id": feed_id,
                    "error": str(e),
                    "consecutive_failures": feed.consecutive_failures,
                }
            )

            return False, 0

    async def _process_feed_entry(
        self,
        session: AsyncSession,
        feed: Feed,
        entry: dict,
        source_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single feed entry and create an item if new.

        Args:
            session: Database session
            feed: Feed model instance
            entry: Parsed feed entry
            source_id: Source UUID from unified source management (optional)

        Returns:
            Item data dict if created (with id, feed_id, title, etc), None if duplicate

        ⚠️ IMPORTANT: Does NOT publish events - caller must publish AFTER commit!

        Epic 1.2 Deduplication:
        - SHA256 content_hash: Exact duplicate detection (existing)
        - SimHash fingerprint: Near-duplicate detection (new)
        - Hamming <= 3: Reject as duplicate
        - Hamming 4-7: Flag for human review
        """
        from app.services.deduplication import DeduplicationService
        from app.services.dedup_repository import DeduplicationRepository

        # Generate content hash for exact deduplication (SHA256)
        content_for_hash = f"{entry.get('title', '')}{entry.get('link', '')}{entry.get('summary', '')}"
        content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()

        # Check for exact duplicate (SHA256)
        result = await session.execute(
            select(FeedItem).where(FeedItem.content_hash == content_hash)
        )
        if result.scalar_one_or_none():
            return None

        # Extract content fields for SimHash
        title = entry.get("title", "Untitled")[:500]
        content = entry.get("content", [{}])[0].get("value") if entry.get("content") else None
        description = entry.get("summary")

        # Prepare text for SimHash (title + content or description)
        simhash_text = title
        if content:
            simhash_text = f"{simhash_text} {content}"
        elif description:
            simhash_text = f"{simhash_text} {description}"

        # Epic 1.2: SimHash deduplication check
        near_duplicate_info = None
        simhash_fp = None

        if simhash_text.strip():
            simhash_fp = SimHasher.compute_fingerprint(simhash_text)

            # Get recent fingerprints for comparison (72 hours lookback)
            dedup_repo = DeduplicationRepository(session)
            recent_fps = await dedup_repo.get_recent_fingerprints(hours=72)

            if recent_fps:
                dedup_service = DeduplicationService()
                dedup_result = dedup_service.check_duplicate(simhash_fp, recent_fps)

                if dedup_result.is_duplicate:
                    # Reject duplicate (Hamming <= 3)
                    logger.info(
                        f"Rejecting duplicate: '{title[:50]}...' "
                        f"(Hamming: {dedup_result.hamming_distance}, "
                        f"matches article: {dedup_result.matching_article_id})"
                    )
                    DUPLICATE_REJECTED_TOTAL.labels(feed_id=str(feed.id)).inc()
                    return None

                if dedup_result.is_near_duplicate:
                    # Store info for flagging after item is created
                    near_duplicate_info = {
                        "existing_article_id": dedup_result.matching_article_id,
                        "hamming_distance": dedup_result.hamming_distance,
                        "simhash_existing": dedup_result.matching_fingerprint,
                    }

        # Parse published date
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import time
            published_at = datetime.fromtimestamp(
                time.mktime(entry.published_parsed),
                tz=timezone.utc
            )
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            import time
            published_at = datetime.fromtimestamp(
                time.mktime(entry.updated_parsed),
                tz=timezone.utc
            )

        # Create new item with SimHash fingerprint
        item = FeedItem(
            feed_id=feed.id,
            source_id=source_id,  # Link to unified source management
            title=title,
            link=entry.get("link", ""),
            description=description,
            content=content,
            author=entry.get("author"),
            guid=entry.get("id", entry.get("guid")),
            published_at=published_at or datetime.now(timezone.utc),
            content_hash=content_hash,
            simhash_fingerprint=simhash_fp,  # Epic 1.2: Store SimHash fingerprint
            # Epic 0.4: NewsML-G2 fields
            version=1,
            version_created_at=datetime.now(timezone.utc),
            pub_status='usable',
        )

        session.add(item)
        await session.flush()

        # Epic 1.2: Flag near-duplicate after item has ID
        if near_duplicate_info:
            dedup_repo = DeduplicationRepository(session)
            await dedup_repo.flag_near_duplicate(
                new_article_id=item.id,
                existing_article_id=near_duplicate_info["existing_article_id"],
                hamming_distance=near_duplicate_info["hamming_distance"],
                simhash_new=simhash_fp,
                simhash_existing=near_duplicate_info["simhash_existing"],
            )
            NEAR_DUPLICATE_FLAGGED_TOTAL.labels(feed_id=str(feed.id)).inc()
            logger.info(
                f"Flagged near-duplicate: '{title[:50]}...' "
                f"(Hamming: {near_duplicate_info['hamming_distance']}, "
                f"similar to: {near_duplicate_info['existing_article_id']})"
            )

        # Return item data for event publishing (caller must publish AFTER commit)
        # ⚠️ CRITICAL FIX: Ensure content is properly evaluated for V3 analysis
        # Bug: item.content might be None even though RSS provided content (race condition)
        # Solution: Use explicit None check + strip whitespace to detect truly empty content
        content_value = item.content if item.content is not None else (item.description or "")
        has_real_content = bool(content_value and content_value.strip())

        return {
            "item_id": str(item.id),
            "feed_id": str(feed.id),
            "source_id": str(source_id) if source_id else None,  # Unified source reference
            "title": item.title,
            "link": item.link,
            "content": content_value,
            "has_content": has_real_content,
            "scrape_full_content": feed.scrape_full_content,
            "scrape_method": feed.scrape_method or "auto",
            # Epic 0.4: SimHash fingerprint for deduplication
            "simhash_fingerprint": item.simhash_fingerprint,
            # Epic 0.4: NewsML-G2 version metadata
            "version": item.version,
            "pub_status": item.pub_status,
            # ⚡ Event-Carried State Transfer: Include analysis config in item data
            # This eliminates content-analysis-service → feed-service DB query
            "analysis_config": {
                "enable_summary": feed.enable_summary,
                "enable_entity_extraction": feed.enable_entity_extraction,
                "enable_topic_classification": feed.enable_topic_classification,
                "enable_categorization": feed.enable_categorization,
                "enable_finance_sentiment": feed.enable_finance_sentiment,
                "enable_geopolitical_sentiment": feed.enable_geopolitical_sentiment,
                "enable_osint_analysis": feed.enable_osint_analysis,
            }
        }

    async def _update_feed_health(
        self,
        session: AsyncSession,
        feed_id: int,
        success: bool,
        response_time_ms: Optional[int] = None,
    ) -> None:
        """Update feed health metrics."""
        result = await session.execute(
            select(FeedHealth).where(FeedHealth.feed_id == feed_id)
        )
        health = result.scalar_one_or_none()

        if not health:
            health = FeedHealth(
                feed_id=feed_id,
                health_score=100 if success else 0,
                consecutive_failures=0 if success else 1,
                is_healthy=success,
                last_success_at=datetime.now(timezone.utc) if success else None,
                last_failure_at=None if success else datetime.now(timezone.utc),
            )
            session.add(health)
        else:
            if success:
                health.consecutive_failures = 0
                health.last_success_at = datetime.now(timezone.utc)
                health.is_healthy = True
            else:
                health.consecutive_failures += 1
                health.last_failure_at = datetime.now(timezone.utc)
                health.is_healthy = health.consecutive_failures < settings.CONSECUTIVE_FAILURES_FOR_ERROR

            # Update health score (simple calculation)
            if success:
                health.health_score = min(100, health.health_score + 10)
            else:
                health.health_score = max(0, health.health_score - 20)

            # Update response time average
            if response_time_ms is not None:
                if health.avg_response_time_ms:
                    # Simple moving average
                    health.avg_response_time_ms = (health.avg_response_time_ms * 0.9) + (response_time_ms * 0.1)
                else:
                    health.avg_response_time_ms = float(response_time_ms)

            health.updated_at = datetime.now(timezone.utc)

        # Update feed's health score
        result = await session.execute(select(Feed).where(Feed.id == feed_id))
        feed = result.scalar_one_or_none()
        if feed:
            feed.health_score = health.health_score
            feed.consecutive_failures = health.consecutive_failures

    async def _update_feed_statistics(self, session: AsyncSession, feed_id: int) -> None:
        """Update feed statistics (item counts)."""
        # Count total items
        result = await session.execute(
            select(FeedItem).where(FeedItem.feed_id == feed_id)
        )
        total_items = len(result.scalars().all())

        # Count items in last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await session.execute(
            select(FeedItem).where(
                FeedItem.feed_id == feed_id,
                FeedItem.created_at >= yesterday
            )
        )
        items_24h = len(result.scalars().all())

        # Update feed
        result = await session.execute(select(Feed).where(Feed.id == feed_id))
        feed = result.scalar_one_or_none()
        if feed:
            feed.total_items = total_items
            feed.items_last_24h = items_24h