# services/clustering-service/app/workers/analysis_consumer.py
"""Consumer for analysis.v3.completed events.

Consumes analyzed articles from RabbitMQ and assigns them to clusters
using Single-Pass Clustering algorithm with cosine similarity matching.

Flow:
    1. Receive analysis.v3.completed event
    2. Extract embedding from payload
    3. Find matching cluster (similarity > threshold)
    4. If match: update cluster, publish cluster.updated
    5. If no match: create new cluster, publish cluster.created
    6. Detect bursts and publish cluster.burst_detected

Enhanced in Epic 1.3:
    - Time-windowed velocity tracking for burst detection
    - Multiple severity levels (low, medium, high, critical)
    - Webhook alerts to n8n for notifications
    - Cooldown period to prevent alert spam
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session
from app.schemas.events import AnalysisCompletedPayload
from app.services.burst_detection import BurstDetectionService, BurstResult
from app.services.burst_detection_v2 import EnhancedBurstDetectionService, EnhancedBurstResult
from app.services.burst_repository import BurstRepository
from app.services.alert_webhook import AlertWebhookService
from app.services.batch_cluster_repository import BatchClusterRepository
from app.services.cluster_repository import ClusterRepository
from app.services.clustering import ClusteringService
from app.services.event_publisher import get_event_publisher

logger = logging.getLogger(__name__)

# Configuration for incremental batch assignment
BATCH_ASSIGNMENT_DISTANCE_THRESHOLD = 0.5  # Max cosine distance to nearest centroid


class AnalysisConsumer:
    """
    Consumer for analysis.v3.completed events.

    Processes analyzed articles and assigns them to clusters using
    Single-Pass Clustering algorithm.

    Attributes:
        connection: RabbitMQ connection
        channel: RabbitMQ channel
        queue: Bound queue for analysis events
        clustering_service: Service for clustering logic
        event_publisher: Publisher for cluster events

    Example:
        >>> consumer = AnalysisConsumer()
        >>> await consumer.start()
        >>> # Consumer now processing messages
        >>> await consumer.stop()
    """

    def __init__(self):
        """Initialize consumer with required services."""
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.clustering_service = ClusteringService()
        self.event_publisher = None

        # Initialize burst detection service (Epic 1.3)
        self.burst_detection_service = BurstDetectionService(
            window_minutes=settings.BURST_WINDOW_MINUTES,
            velocity_thresholds={
                "low": settings.BURST_VELOCITY_LOW,
                "medium": settings.BURST_VELOCITY_MEDIUM,
                "high": settings.BURST_VELOCITY_HIGH,
                "critical": settings.BURST_VELOCITY_CRITICAL,
            },
            cooldown_minutes=settings.BURST_COOLDOWN_MINUTES,
        )

        # Initialize enhanced v2 burst detection (multi-signal analysis)
        self.enhanced_burst_service = EnhancedBurstDetectionService(
            window_minutes=settings.BURST_WINDOW_MINUTES,
            velocity_thresholds={
                "low": settings.BURST_VELOCITY_LOW,
                "medium": settings.BURST_VELOCITY_MEDIUM,
                "high": settings.BURST_VELOCITY_HIGH,
                "critical": settings.BURST_VELOCITY_CRITICAL,
            },
            cooldown_minutes=settings.BURST_COOLDOWN_MINUTES,
            growth_rate_threshold=settings.BURST_GROWTH_RATE_THRESHOLD,
            concentration_threshold=settings.BURST_CONCENTRATION_THRESHOLD,
            min_sources=settings.BURST_MIN_SOURCES,
            require_multi_signal=settings.BURST_REQUIRE_MULTI_SIGNAL,
        )
        self.use_enhanced_detection = settings.USE_ENHANCED_BURST_DETECTION

        # Initialize webhook service (if enabled)
        self.alert_service: Optional[AlertWebhookService] = None
        if settings.BURST_WEBHOOK_ENABLED:
            self.alert_service = AlertWebhookService(
                webhook_url=settings.BURST_WEBHOOK_URL,
            )

    async def start(self):
        """
        Start consumer and connect to RabbitMQ.

        Sets up:
            - Event publisher connection
            - RabbitMQ connection with QoS
            - Exchange and queue declarations
            - Binding to analysis.v3.completed events
            - Message consumption

        Raises:
            ConnectionError: If RabbitMQ connection fails
        """
        logger.info("Starting analysis consumer...")

        # Initialize event publisher
        self.event_publisher = await get_event_publisher()

        # Connect to RabbitMQ
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()

        # Set QoS (prefetch count)
        await self.channel.set_qos(prefetch_count=10)

        # Declare exchange (topic type for routing)
        exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declare queue for this consumer
        self.queue = await self.channel.declare_queue(
            "clustering.analysis",
            durable=True,
        )

        # Bind to analysis events
        await self.queue.bind(exchange, routing_key="analysis.v3.completed")
        logger.info("Bound to analysis.v3.completed events")

        # Start consuming messages
        await self.queue.consume(self._process_message)

        logger.info("Analysis consumer started")

    async def stop(self):
        """
        Stop consumer and close connections gracefully.

        Closes RabbitMQ connection which will also close channel and cancel
        any active consumers.
        """
        if self.connection:
            await self.connection.close()
        logger.info("Analysis consumer stopped")

    async def _process_message(self, message: aio_pika.IncomingMessage):
        """
        Process incoming analysis.v3.completed event.

        Parses the message, validates the payload, and delegates to
        _assign_to_cluster for clustering logic.

        Args:
            message: Incoming RabbitMQ message with EventEnvelope

        Note:
            Uses message.process() context manager for automatic ack/nack
        """
        async with message.process():
            try:
                # Parse message body
                raw_body = message.body.decode()
                message_data = json.loads(raw_body)

                # Extract payload from EventEnvelope
                # Support both wrapped and unwrapped formats
                payload_data = message_data.get("payload", message_data)
                correlation_id = message_data.get("correlation_id")
                event_id = message_data.get("event_id")

                # Validate payload with Pydantic schema
                try:
                    payload = AnalysisCompletedPayload(**payload_data)
                except Exception as e:
                    logger.warning(f"Invalid payload, skipping: {e}")
                    return

                # Skip if no embedding provided
                if not payload.embedding:
                    logger.debug(f"No embedding for {payload.article_id}, skipping")
                    return

                logger.info(f"Processing article {payload.article_id} for clustering")

                # Process article in database session
                async with async_session() as session:
                    repo = ClusterRepository(session)

                    # Idempotency check: skip if already processed
                    if await repo.is_article_processed(payload.article_id):
                        logger.debug(
                            f"Article {payload.article_id} already processed, skipping"
                        )
                        return

                    await self._assign_to_cluster(
                        session=session,
                        payload=payload,
                        correlation_id=correlation_id,
                        causation_id=event_id,
                    )

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    async def _assign_to_cluster(
        self,
        session: AsyncSession,
        payload: AnalysisCompletedPayload,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ):
        """
        Assign article to a cluster.

        Core clustering logic:
            1. Get active clusters from database
            2. Find best matching cluster using cosine similarity
            3. If match found (similarity >= threshold):
               - Update centroid with incremental mean
               - Increment article count
               - Check for burst detection
               - Publish cluster.updated event
            4. If no match:
               - Create new cluster with article as seed
               - Publish cluster.created event

        Args:
            session: Database session for repository operations
            payload: Validated analysis event payload
            correlation_id: Correlation ID for distributed tracing
            causation_id: ID of the causing event
        """
        repo = ClusterRepository(session)

        # Get active clusters for matching
        active_clusters = await repo.get_active_clusters(
            max_age_hours=settings.CLUSTER_MAX_AGE_HOURS
        )

        # Find matching cluster
        match = self.clustering_service.find_matching_cluster(
            embedding=payload.embedding,
            active_clusters=active_clusters,
        )

        # Prepare entities (top 5)
        entities = None
        if payload.entities:
            entities = payload.entities[:5]

        if match:
            # -----------------------------------------------------------------
            # Add to existing cluster
            # -----------------------------------------------------------------
            cluster_id = match["cluster_id"]
            similarity = match["similarity"]

            # Get current cluster data for article count
            cluster_data = next(
                (c for c in active_clusters if c["id"] == cluster_id),
                None
            )
            if cluster_data is None:
                logger.error(f"Cluster {cluster_id} not found in active list")
                return

            new_count = cluster_data["article_count"] + 1

            # Update centroid using incremental mean
            new_centroid = self.clustering_service.update_centroid(
                current_centroid=cluster_data["centroid"],
                new_vector=payload.embedding,
                article_count=new_count,
            )

            # Legacy burst detection (kept for backward compatibility)
            is_breaking = self._detect_burst(new_count)

            # Calculate tension from tier1 scores or use explicit value
            tension_score = payload.calculate_tension()

            # Update cluster in database
            updated_cluster = await repo.update_cluster(
                cluster_id=cluster_id,
                new_centroid=new_centroid,
                new_article_count=new_count,
                entities=entities,
                tension_score=tension_score,
                is_breaking=is_breaking,
            )

            # Record membership for idempotency
            await repo.add_article_to_cluster(
                cluster_id=cluster_id,
                article_id=payload.article_id,
                similarity_score=similarity,
            )
            await session.commit()

            logger.info(
                f"Added article {payload.article_id} to cluster {cluster_id} "
                f"(similarity: {similarity:.3f}, count: {new_count})"
            )

            # Publish cluster.updated event
            await self.event_publisher.publish_cluster_updated(
                cluster_id=str(cluster_id),
                article_id=str(payload.article_id),
                article_count=new_count,
                similarity_score=similarity,
                tension_score=tension_score,
                is_breaking=is_breaking,
                primary_entities=entities,
                correlation_id=correlation_id,
            )

            # Enhanced burst detection (Epic 1.3)
            # Uses time-windowed velocity tracking for more accurate detection
            cluster_title = cluster_data.get("title", "Unknown")
            top_entity_names = [e.get("name") for e in (entities or [])[:3]]

            # Extract category from tier0 triage results (if available)
            category = None
            if payload.tier0 and payload.tier0.category:
                category = payload.tier0.category.lower()  # Normalize to lowercase

            # Override to "crypto" if finance article contains crypto entities
            # Triage doesn't have a CRYPTO category, so we detect from entities
            if category == "finance" and payload.entities:
                crypto_keywords = {
                    "bitcoin", "btc", "ethereum", "eth", "xrp", "ripple",
                    "cryptocurrency", "crypto", "blockchain", "altcoin",
                    "solana", "sol", "cardano", "ada", "dogecoin", "doge",
                    "binance", "coinbase", "tether", "usdt", "stablecoin"
                }
                for entity in payload.entities:
                    entity_name = entity.get("name", "").lower()
                    if any(kw in entity_name for kw in crypto_keywords):
                        category = "crypto"
                        logger.debug(
                            f"Overriding category to 'crypto' due to entity: {entity_name}"
                        )
                        break

            burst_result = await self._check_burst_detection(
                session=session,
                cluster_id=cluster_id,
                cluster_title=cluster_title,
                top_entities=top_entity_names,
                tension_score=tension_score,
                correlation_id=correlation_id,
                category=category,
            )

            # If enhanced burst detection triggered, it already published events
            # Only publish legacy burst if no enhanced burst was detected
            if not burst_result and is_breaking and updated_cluster:
                await self.event_publisher.publish_burst_detected(
                    cluster_id=str(cluster_id),
                    title=updated_cluster.title,
                    article_count=new_count,
                    growth_rate=self._calculate_growth_rate(new_count),
                    tension_score=tension_score or 5.0,
                    top_entities=top_entity_names,
                    correlation_id=correlation_id,
                )

        else:
            # -----------------------------------------------------------------
            # Create new cluster
            # -----------------------------------------------------------------
            # Calculate tension for new cluster
            tension_score = payload.calculate_tension()

            cluster_id = await repo.create_cluster(
                title=payload.title,
                centroid_vector=payload.embedding,
                first_article_id=payload.article_id,
                entities=entities,
                tension_score=tension_score,
            )

            # Record membership for idempotency (first article in new cluster)
            await repo.add_article_to_cluster(
                cluster_id=cluster_id,
                article_id=payload.article_id,
                similarity_score=1.0,  # Perfect match to self
            )
            await session.commit()

            logger.info(
                f"Created new cluster {cluster_id} for article {payload.article_id}"
            )

            # Publish cluster.created event
            await self.event_publisher.publish_cluster_created(
                cluster_id=str(cluster_id),
                title=payload.title,
                article_id=str(payload.article_id),
                correlation_id=correlation_id,
            )

        # -----------------------------------------------------------------
        # Incremental Batch Cluster Assignment (Epic 2)
        # Assign article to nearest batch cluster for topic discovery
        # This runs in parallel with single-pass clustering
        # -----------------------------------------------------------------
        try:
            await self._assign_to_batch_cluster(
                session=session,
                article_id=payload.article_id,
                embedding=payload.embedding,
                title=payload.title,
                correlation_id=correlation_id,
            )
        except Exception as e:
            # Don't fail the main clustering if batch assignment fails
            logger.warning(f"Batch cluster assignment failed for {payload.article_id}: {e}")

    def _detect_burst(self, article_count: int) -> bool:
        """
        Simple burst detection based on article count.

        Legacy method kept for backward compatibility.
        See _check_burst_detection for enhanced time-windowed detection.

        Args:
            article_count: Current number of articles in cluster

        Returns:
            True if burst threshold reached
        """
        return article_count >= settings.BURST_ARTICLE_THRESHOLD

    def _calculate_growth_rate(self, article_count: int) -> float:
        """
        Calculate approximate growth rate.

        Simple ratio of article count to burst threshold.

        Args:
            article_count: Current number of articles

        Returns:
            Growth rate as float (1.0 = at threshold, 2.0 = double threshold)
        """
        return float(article_count) / settings.BURST_ARTICLE_THRESHOLD

    async def _check_burst_detection(
        self,
        session: AsyncSession,
        cluster_id: UUID,
        cluster_title: str,
        top_entities: Optional[List[str]] = None,
        tension_score: Optional[float] = None,
        correlation_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[BurstResult]:
        """
        Enhanced burst detection using multi-signal analysis.

        V2 enhancement:
        - Multi-signal analysis (velocity, growth rate, concentration)
        - Requires multiple signals to agree (reduces false positives)
        - Source diversity check (optional)
        - Fall back to v1 if enhanced detection disabled

        Args:
            session: Database session for repository operations
            cluster_id: UUID of the cluster to check
            cluster_title: Title of the cluster for alerts
            top_entities: Top entity names for alert context
            tension_score: Current tension score
            correlation_id: For distributed tracing
            category: Article category from triage (e.g., "conflict", "finance")

        Returns:
            BurstResult if burst detected, None otherwise
        """
        cluster_repo = ClusterRepository(session)
        burst_repo = BurstRepository(session)

        # Check database cooldown first (persistent across restarts)
        if await burst_repo.is_in_cooldown(cluster_id, settings.BURST_COOLDOWN_MINUTES):
            logger.debug(f"Cluster {cluster_id} in cooldown (DB), skipping burst detection")
            return None

        # Get article timestamps for velocity calculation
        timestamps = await cluster_repo.get_article_timestamps(
            cluster_id,
            hours=1  # Look back 1 hour
        )

        # Run burst detection algorithm
        result = None
        enhanced_result = None

        if self.use_enhanced_detection:
            # Use v2 multi-signal detection
            enhanced_result = self.enhanced_burst_service.detect_burst(
                cluster_id,
                timestamps,
                source_ids=None,  # TODO: Fetch source IDs for diversity check
            )
            if enhanced_result:
                # Convert to v1 BurstResult for compatibility
                result = BurstResult(
                    cluster_id=enhanced_result.cluster_id,
                    severity=enhanced_result.severity,
                    velocity=enhanced_result.velocity,
                    window_minutes=enhanced_result.window_minutes,
                    detected_at=enhanced_result.detected_at,
                )
                logger.info(
                    f"Enhanced v2 burst: cluster={cluster_id} "
                    f"severity={enhanced_result.severity.value} "
                    f"velocity={enhanced_result.velocity} "
                    f"growth_rate={enhanced_result.growth_rate:.1f}x "
                    f"concentration={enhanced_result.concentration:.0%} "
                    f"signals={enhanced_result.signals}"
                )
        else:
            # Use legacy v1 detection
            result = self.burst_detection_service.detect_burst(cluster_id, timestamps)

        if result is None:
            return None

        # Calculate growth_rate - use v2's calculated value if available
        if enhanced_result:
            growth_rate = enhanced_result.growth_rate
        else:
            growth_rate = result.velocity / settings.BURST_VELOCITY_LOW

        # Record alert in database with cluster metadata
        # Get the ACTUAL first and last article timestamps for the entire cluster
        # (not just the velocity window)
        first_article_at, last_article_at = await cluster_repo.get_cluster_article_range(
            cluster_id
        )

        alert_id = await burst_repo.record_burst_alert(
            cluster_id=cluster_id,
            severity=result.severity.value,
            velocity=result.velocity,
            window_minutes=result.window_minutes,
            alert_sent=False,
            title=cluster_title,
            tension_score=tension_score,
            growth_rate=growth_rate,
            top_entities=top_entities,
            first_article_at=first_article_at,
            last_article_at=last_article_at,
            category=category,
        )

        # Send webhook alert if service is enabled
        webhook_success = False
        if self.alert_service:
            webhook_success = await self.alert_service.send_alert(
                cluster_id=cluster_id,
                cluster_title=cluster_title,
                severity=result.severity,
                velocity=result.velocity,
                window_minutes=result.window_minutes,
                top_entities=top_entities,
            )

            if webhook_success:
                await burst_repo.mark_alert_sent(alert_id)
                # Mark in-memory cooldown as well
                if self.use_enhanced_detection:
                    self.enhanced_burst_service.mark_alerted(cluster_id)
                else:
                    self.burst_detection_service.mark_alerted(cluster_id)

        # Commit the burst alert record
        await session.commit()

        # Publish burst_detected event
        await self.event_publisher.publish_burst_detected(
            cluster_id=str(cluster_id),
            title=cluster_title,
            article_count=result.velocity,
            growth_rate=growth_rate,
            tension_score=tension_score or 5.0,
            top_entities=top_entities,
            correlation_id=correlation_id,
        )

        return result

    async def _assign_to_batch_cluster(
        self,
        session: AsyncSession,
        article_id: UUID,
        embedding: List[float],
        title: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Assign article to nearest batch cluster (incremental assignment).

        This provides real-time topic assignment for new articles even between
        batch clustering runs. The article is assigned to the nearest cluster
        centroid if within the distance threshold.

        Args:
            session: Database session
            article_id: UUID of the article
            embedding: Article embedding vector (1536D)
            title: Article title for logging
            correlation_id: For distributed tracing

        Returns:
            Dict with cluster info if assigned, None if no suitable cluster found

        Note:
            This is complementary to single-pass clustering. Articles may be in:
            - Single-pass cluster (real-time burst detection)
            - Batch cluster (topic discovery)
            - Both or neither
        """
        batch_repo = BatchClusterRepository(session)

        # Check if there's a completed batch
        batch_id = await batch_repo.get_latest_batch_id()
        if batch_id is None:
            logger.debug("No completed batch available for incremental assignment")
            return None

        # Find nearest cluster using pgvector similarity search
        similar = await batch_repo.find_similar_clusters(
            embedding=embedding,
            batch_id=batch_id,
            limit=1,
        )

        if not similar:
            logger.debug(f"No batch clusters found for article {article_id}")
            return None

        nearest = similar[0]
        similarity = nearest["similarity"]
        distance = 1.0 - similarity  # Convert similarity to distance

        # Check distance threshold
        if distance > BATCH_ASSIGNMENT_DISTANCE_THRESHOLD:
            logger.debug(
                f"Article {article_id} too far from nearest batch cluster "
                f"(distance={distance:.3f} > threshold={BATCH_ASSIGNMENT_DISTANCE_THRESHOLD})"
            )
            return None

        cluster_id = nearest["cluster_id"]
        cluster_label = nearest["label"]

        # Insert into batch_article_clusters
        # Note: Using raw SQL since we need to handle potential duplicates
        from sqlalchemy import text

        insert_sql = text("""
            INSERT INTO batch_article_clusters (article_id, cluster_id, batch_id, distance_to_centroid, assigned_at)
            VALUES (:article_id, :cluster_id, :batch_id, :distance, NOW())
            ON CONFLICT (article_id) DO UPDATE SET
                cluster_id = EXCLUDED.cluster_id,
                batch_id = EXCLUDED.batch_id,
                distance_to_centroid = EXCLUDED.distance_to_centroid,
                assigned_at = NOW()
        """)

        await session.execute(insert_sql, {
            "article_id": str(article_id),
            "cluster_id": cluster_id,
            "batch_id": str(batch_id),
            "distance": distance,
        })

        logger.info(
            f"Incrementally assigned article {article_id} to batch cluster {cluster_id} "
            f"'{cluster_label}' (similarity={similarity:.3f})"
        )

        # Publish event for sitrep-service and other consumers
        await self.event_publisher.publish_event(
            event_type="batch.article.assigned",
            payload={
                "article_id": str(article_id),
                "cluster_id": cluster_id,
                "cluster_label": cluster_label,
                "batch_id": str(batch_id),
                "similarity": similarity,
                "title": title[:100],  # Truncate for event
            },
            correlation_id=correlation_id,
        )

        return {
            "cluster_id": cluster_id,
            "label": cluster_label,
            "similarity": similarity,
            "batch_id": str(batch_id),
        }


# Global consumer instance
analysis_consumer = AnalysisConsumer()
