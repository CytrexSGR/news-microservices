"""
RabbitMQ Consumer for verification.required events.

Listens for verification requests from content-analysis-service
and triggers DIA planning process.

Related: ADR-018 (DIA-Planner & Verifier)
"""

import json
import logging
import asyncio
from typing import Optional
import aio_pika
from aio_pika import IncomingMessage, Exchange, Queue
from aio_pika.abc import AbstractRobustConnection

# Import from project root models
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import VerificationRequiredEvent

from app.core.config import settings
from app.services.dia_planner import DIAPlanner
from app.services.dia_verifier import DIAVerifier

logger = logging.getLogger(__name__)


class VerificationConsumer:
    """
    RabbitMQ consumer for verification.required events.

    Responsibilities:
    1. Connect to RabbitMQ
    2. Declare exchange and queue
    3. Consume verification.required events
    4. Trigger DIA planning process
    5. Handle errors and retries
    """

    def __init__(self):
        """Initialize verification consumer."""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel = None
        self.exchange: Optional[Exchange] = None
        self.queue: Optional[Queue] = None
        self.planner = DIAPlanner()
        self.verifier = DIAVerifier()  # Phase 2: Add verifier

        logger.info("[VerificationConsumer] Initialized with Planner and Verifier")

    async def connect(self):
        """
        Connect to RabbitMQ and set up infrastructure.

        Creates:
        - Exchange: verification_exchange (topic)
        - Queue: verification_queue (durable)
        - Binding: verification.required.* -> verification_queue
        """
        try:
            logger.info(f"[VerificationConsumer] Connecting to RabbitMQ: {settings.RABBITMQ_URL}")

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=30
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)  # Process one message at a time

            logger.info("[VerificationConsumer] Connected to RabbitMQ")

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_VERIFICATION_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            logger.info(f"[VerificationConsumer] Declared exchange: {settings.RABBITMQ_VERIFICATION_EXCHANGE}")

            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.RABBITMQ_VERIFICATION_QUEUE,
                durable=True,
                arguments={
                    # Dead letter exchange for failed messages
                    "x-dead-letter-exchange": "verification_dlx",
                    # Message TTL: 24 hours
                    "x-message-ttl": 86400000
                }
            )
            logger.info(f"[VerificationConsumer] Declared queue: {settings.RABBITMQ_VERIFICATION_QUEUE}")

            # Bind queue to exchange
            await self.queue.bind(
                self.exchange,
                routing_key=settings.RABBITMQ_VERIFICATION_ROUTING_KEY
            )
            logger.info(
                f"[VerificationConsumer] Bound queue to exchange with "
                f"routing_key={settings.RABBITMQ_VERIFICATION_ROUTING_KEY}"
            )

        except Exception as e:
            logger.error(f"[VerificationConsumer] Failed to connect: {e}")
            raise

    async def start_consuming(self):
        """
        Start consuming messages from queue.

        This is a blocking call that processes messages until stopped.
        """
        if not self.queue:
            raise RuntimeError("Must call connect() before start_consuming()")

        logger.info("[VerificationConsumer] Starting to consume messages...")

        # Start consuming
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self._handle_message(message)

    async def _handle_message(self, message: IncomingMessage):
        """
        Handle incoming verification.required message.

        Args:
            message: RabbitMQ message

        Process:
        1. Parse message
        2. Validate event structure
        3. Trigger DIA planning
        4. ACK/NACK message based on result
        """
        async with message.process(requeue=False):  # Don't requeue on failure
            try:
                logger.info(
                    f"[VerificationConsumer] Received message: "
                    f"routing_key={message.routing_key}, "
                    f"delivery_tag={message.delivery_tag}"
                )

                # Parse message body
                event_data = json.loads(message.body.decode())

                # Validate and create VerificationRequiredEvent
                event = VerificationRequiredEvent(**event_data)

                logger.info(
                    f"[VerificationConsumer] Processing verification for "
                    f"article_id={event.article_id}, "
                    f"analysis_result_id={event.analysis_result_id}"
                )

                # =========================================================
                # Stage 1 & 2: DIA Planning (Root Cause + Plan Generation)
                # =========================================================
                problem_hypothesis, verification_plan = await self.planner.process_verification_request(event)

                logger.info(
                    f"[VerificationConsumer] Planning completed: "
                    f"hypothesis_type={problem_hypothesis.hypothesis_type}, "
                    f"plan_priority={verification_plan.priority}"
                )

                # =========================================================
                # Phase 2: DIA Verification (Tool Execution + Evidence)
                # =========================================================
                logger.info("[VerificationConsumer] Executing verification with tools...")

                evidence_package = await self.verifier.execute_verification(
                    plan=verification_plan,
                    hypothesis=problem_hypothesis,
                    event=event
                )

                logger.info(
                    f"[VerificationConsumer] Verification completed: "
                    f"hypothesis_confirmed={evidence_package.hypothesis_confirmed}, "
                    f"confidence_score={evidence_package.confidence_score:.2f}, "
                    f"key_findings={len(evidence_package.key_findings)}"
                )

                # Log evidence package as JSON for inspection
                logger.info(
                    f"[VerificationConsumer] Evidence Package:\n"
                    f"{evidence_package.model_dump_json(indent=2)}"
                )

                # TODO: Phase 3 - Pass to Corrector
                # For now, verification is complete. Next phase will:
                # 1. Use evidence to correct analysis
                # 2. Publish verification.completed event
                # 3. Update analysis results in database

                # Message will be ACKed automatically (async with message.process())

            except json.JSONDecodeError as e:
                logger.error(f"[VerificationConsumer] Invalid JSON in message: {e}")
                # Message will be NACKed (not requeued)

            except Exception as e:
                logger.error(
                    f"[VerificationConsumer] Error processing message: {e}",
                    exc_info=True
                )
                # Message will be NACKed (not requeued)
                # TODO: Publish to dead letter queue for manual inspection

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            logger.info("[VerificationConsumer] Connection closed")


# Singleton instance
_consumer: Optional[VerificationConsumer] = None


async def get_consumer() -> VerificationConsumer:
    """
    Get or create verification consumer singleton.

    Returns:
        VerificationConsumer instance
    """
    global _consumer
    if _consumer is None:
        _consumer = VerificationConsumer()
        await _consumer.connect()
    return _consumer


async def start_consumer():
    """
    Start the verification consumer (blocking).

    This function should be called from main.py on startup.
    """
    consumer = await get_consumer()
    await consumer.start_consuming()


# For testing/debugging
if __name__ == "__main__":
    import asyncio

    async def test_consumer():
        """Test the consumer by connecting and waiting for messages."""
        logging.basicConfig(level=logging.INFO)

        consumer = VerificationConsumer()
        await consumer.connect()

        logger.info("Consumer connected. Waiting for messages...")
        logger.info("Press Ctrl+C to stop")

        try:
            await consumer.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            await consumer.close()

    asyncio.run(test_consumer())
