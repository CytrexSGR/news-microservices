"""
Relationships Consumer

Consumes `relationships.extracted` events from RabbitMQ and ingests triplets into Neo4j.

Post-Incident #18: Includes DLQ configuration and improved error handling
to prevent retry storms from non-retriable errors.
"""

import logging
import json
import asyncio
import time
from typing import Optional
from aio_pika import connect_robust, Message, IncomingMessage, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractQueue

from app.config import settings
from app.models.events import RelationshipsExtractedEvent, RelationshipTriplet
from app.models.graph import Entity, Relationship, Triplet
from app.services.ingestion_service import ingestion_service
from app.services.cypher_validator import CypherSyntaxError
from app.core.metrics import (
    kg_events_consumed_total,
    kg_consumer_processing_duration,
    kg_consumer_triplets_per_event,
    kg_consumer_queue_size
)

logger = logging.getLogger(__name__)


# Non-retriable errors - these should go to DLQ immediately
NON_RETRIABLE_ERRORS = (
    CypherSyntaxError,
    json.JSONDecodeError,
    KeyError,  # Missing required fields in event payload
    ValueError,  # Invalid data format
)


class RelationshipsConsumer:
    """RabbitMQ consumer for relationships.extracted events."""

    def __init__(self):
        """Initialize consumer (connection created on startup)."""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.queue: Optional[AbstractQueue] = None
        self._consumer_tag: Optional[str] = None

    async def connect(self):
        """
        Connect to RabbitMQ and setup queue/bindings.

        Post-Incident #18: Includes Dead Letter Queue (DLQ) configuration
        for non-retriable errors.

        Called during application startup.
        """
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url}...")

            # Connect to RabbitMQ
            self.connection = await connect_robust(
                settings.rabbitmq_url,
                timeout=30
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # Process max 10 messages concurrently

            # Declare main exchange (should already exist)
            exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare Dead Letter Exchange (DLX) for failed messages
            dlx_name = f"{settings.RABBITMQ_EXCHANGE}.dlx"
            await self.channel.declare_exchange(
                dlx_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare Dead Letter Queue (DLQ)
            dlq_name = f"{settings.RABBITMQ_QUEUE}.dlq"
            dlq = await self.channel.declare_queue(
                dlq_name,
                durable=True
            )
            await dlq.bind(dlx_name, routing_key="#")

            # Declare main queue with DLQ routing
            self.queue = await self.channel.declare_queue(
                settings.RABBITMQ_QUEUE,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': dlx_name,
                    'x-message-ttl': 86400000,  # 24 hours max retention
                }
            )

            # Bind queue to exchange with routing key
            await self.queue.bind(
                exchange,
                routing_key=settings.RABBITMQ_ROUTING_KEY
            )

            logger.info(
                f"✓ RabbitMQ connected. Queue: {settings.RABBITMQ_QUEUE}, "
                f"Routing: {settings.RABBITMQ_ROUTING_KEY}, "
                f"DLQ: {dlq_name}"
            )

        except Exception as e:
            logger.error(f"✗ Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise

    async def start_consuming(self):
        """
        Start consuming messages from queue.

        This runs continuously in the background.
        """
        if not self.queue:
            raise RuntimeError("Queue not initialized. Call connect() first.")

        try:
            logger.info("Starting message consumption...")

            # Start consuming messages
            await self.queue.consume(self._handle_message)

            logger.info("✓ Consumer started successfully")

        except Exception as e:
            logger.error(f"✗ Failed to start consumer: {e}", exc_info=True)
            raise

    async def _handle_message(self, message: IncomingMessage):
        """
        Handle a single relationships.extracted message.

        Post-Incident #18: Improved error handling with distinction between
        retriable and non-retriable errors.

        Args:
            message: Incoming RabbitMQ message
        """
        start_time = time.time()
        article_id = "unknown"

        try:
            # Parse message body
            body = json.loads(message.body.decode())
            event = RelationshipsExtractedEvent.parse_obj(body)
            article_id = event.payload.article_id

            triplet_count = len(event.payload.triplets)

            logger.info(
                f"Processing event: article_id={article_id}, "
                f"triplets={triplet_count}"
            )

            # Record triplets per event
            kg_consumer_triplets_per_event.observe(triplet_count)

            # Convert event triplets to graph triplets
            graph_triplets = []

            for event_triplet in event.payload.triplets:
                # Convert to graph model format
                # Include Wikidata Q-ID in properties if available
                subject_props = {}
                if event_triplet.subject.wikidata_id:
                    subject_props["wikidata_id"] = event_triplet.subject.wikidata_id

                subject = Entity(
                    name=event_triplet.subject.text,
                    type=event_triplet.subject.type,
                    properties=subject_props
                )

                object_props = {}
                if event_triplet.object.wikidata_id:
                    object_props["wikidata_id"] = event_triplet.object.wikidata_id

                obj = Entity(
                    name=event_triplet.object.text,
                    type=event_triplet.object.type,
                    properties=object_props
                )

                relationship = Relationship(
                    subject=event_triplet.subject.text,
                    subject_type=event_triplet.subject.type,
                    relationship_type=event_triplet.relationship.type,
                    object=event_triplet.object.text,
                    object_type=event_triplet.object.type,
                    confidence=event_triplet.relationship.confidence,
                    evidence=event_triplet.relationship.evidence,
                    source_url=event.payload.source_url,
                    article_id=event.payload.article_id
                )

                triplet = Triplet(
                    subject=subject,
                    relationship=relationship,
                    object=obj
                )

                graph_triplets.append(triplet)

            # Ingest all triplets
            summary = await ingestion_service.ingest_triplets_batch(
                triplets=graph_triplets,
                article_id=event.payload.article_id,
                source_url=event.payload.source_url or ""
            )

            # Record processing time
            duration = time.time() - start_time
            kg_consumer_processing_duration.observe(duration)

            # Increment success counter
            kg_events_consumed_total.labels(status='success').inc()

            logger.info(
                f"✓ Ingested {summary['triplets_processed']}/{len(graph_triplets)} triplets "
                f"in {duration:.2f}s. Nodes: +{summary['nodes_created']}, "
                f"Rels: +{summary['relationships_created']}"
            )

            # ACK the message on success
            await message.ack()

        except NON_RETRIABLE_ERRORS as e:
            # Non-retriable error - send to DLQ (reject without requeue)
            duration = time.time() - start_time
            kg_consumer_processing_duration.observe(duration)
            kg_events_consumed_total.labels(status='failed').inc()

            logger.error(
                f"✗ Non-retriable error for article_id={article_id} in {duration:.2f}s: "
                f"{type(e).__name__}: {e}",
                extra={
                    "article_id": article_id,
                    "error_type": type(e).__name__,
                    "retriable": False
                }
            )
            # Reject WITHOUT requeue → goes to DLQ
            await message.reject(requeue=False)

        except asyncio.TimeoutError as e:
            # Timeout - potentially retriable after backoff
            duration = time.time() - start_time
            kg_consumer_processing_duration.observe(duration)
            kg_events_consumed_total.labels(status='failed').inc()

            logger.warning(
                f"⚠ Timeout for article_id={article_id} after {duration:.2f}s",
                extra={"article_id": article_id, "retriable": True}
            )
            # Requeue for retry (will eventually go to DLQ after max retries)
            await message.reject(requeue=True)

        except Exception as e:
            # Unknown error - log details and requeue for retry
            duration = time.time() - start_time
            kg_consumer_processing_duration.observe(duration)
            kg_events_consumed_total.labels(status='failed').inc()

            logger.error(
                f"✗ Unexpected error for article_id={article_id} in {duration:.2f}s: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
                extra={
                    "article_id": article_id,
                    "error_type": type(e).__name__,
                    "retriable": True
                }
            )
            # Requeue for retry
            await message.reject(requeue=True)

    async def disconnect(self):
        """
        Disconnect from RabbitMQ.

        Called during application shutdown.
        """
        try:
            if self.connection:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")

        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}", exc_info=True)


# Global consumer instance
relationships_consumer = RelationshipsConsumer()
