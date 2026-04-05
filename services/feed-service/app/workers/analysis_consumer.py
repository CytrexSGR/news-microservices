"""
Analysis Results Consumer Worker

Consumes analysis events from RabbitMQ and stores results in article_analysis table.

Supported Events:
- analysis.completed (V2): Published by content-analysis-v2
- analysis.v3.completed (V3): Published by content-analysis-v3 (success or discarded)
- analysis.v3.failed (V3): Published by content-analysis-v3 (pipeline errors)

This worker runs as a separate process alongside the Feed Service API and Celery workers.

⚠️ DUAL-TABLE ARCHITECTURE WARNING ⚠️
=====================================
This worker writes to the UNIFIED table:
    public.article_analysis (3364 rows)

However, this table is NEVER READ by any service! The frontend gets data from the LEGACY table:
    content_analysis_v2.pipeline_executions (7097 rows, read via analysis_loader.py proxy)

WHY: Incomplete schema migration. This worker was implemented but not deployed for several months
(missing from docker-compose.yml until 2025-10-31), causing data fragmentation.

IMPACT:
- This worker writes to unified table (since 2025-10-31)
- Frontend still reads from legacy table (via content-analysis-v2 API)
- Result: Orphaned data in unified table, never displayed to users

HISTORICAL ISSUE (RESOLVED 2025-10-31):
- Worker existed in code but NOT in docker-compose.yml
- Unified table received no data until worker was deployed
- Now deployed, but table still not used by frontend

DECISION REQUIRED: Choose migration path (see POSTMORTEMS.md - Incident #8)
- Option A: Complete migration to unified table (update feed-service to read from here)
- Option B: Rollback to legacy table only (remove this worker, drop unified table)
- Option C: Dual-table with clear boundaries (document, monitor drift)

Related Files:
- services/feed-service/app/services/analysis_loader.py (reads from legacy table via proxy)
- services/content-analysis-v2/app/api/v2/endpoints/pipeline_executions.py (legacy table API)

Last Updated: 2025-10-31
See: POSTMORTEMS.md - Incident #8 for full analysis

Event Flow:
1. V2 or V3 service publishes analysis event to news.events exchange:
   - V2: analysis.completed
   - V3: analysis.v3.completed, analysis.v3.failed
2. This worker consumes from analysis_results_queue (bound to all 3 routing keys)
3. Extracts results from event payload (supports both V2 and V3 formats)
4. Stores in article_analysis table ⚠️ BUT THIS TABLE IS NEVER READ ⚠️
5. ACKs message (or REJECTs to DLQ on failure)
"""
import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from uuid import UUID

import aio_pika
from aio_pika import IncomingMessage, ExchangeType
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DataError

from app.db import AsyncSessionLocal
from app.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AnalysisConsumer:
    """Consumes analysis.completed events and stores results."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.shutdown = False

    async def connect(self) -> None:
        """Connect to RabbitMQ and set up queue."""
        try:
            logger.info(f"Connecting to RabbitMQ: {settings.RABBITMQ_URL}")

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                client_properties={"service": "feed-service-analysis-consumer"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # Process 10 messages concurrently

            # Declare exchange (should already exist, created by content-analysis-v2)
            exchange = await self.channel.declare_exchange(
                "news.events",
                type=ExchangeType.TOPIC,
                durable=True,
            )

            # Declare DLQ (dead letter queue) for failed messages
            dlq = await self.channel.declare_queue(
                "analysis_results_queue_dlq",
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            # Declare main queue with DLQ binding
            self.queue = await self.channel.declare_queue(
                "analysis_results_queue",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",  # Default exchange
                    "x-dead-letter-routing-key": "analysis_results_queue_dlq",
                },
            )

            # Bind queue to exchange with routing keys (V2 and V3 events)
            await self.queue.bind(
                exchange=exchange,
                routing_key="analysis.completed",  # V2 events
            )
            await self.queue.bind(
                exchange=exchange,
                routing_key="analysis.v3.completed",  # V3 success events
            )
            await self.queue.bind(
                exchange=exchange,
                routing_key="analysis.v3.failed",  # V3 failure events
            )

            logger.info("✓ Connected to RabbitMQ and bound to V2 + V3 analysis events")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")

    async def handle_message(self, message: IncomingMessage) -> None:
        """
        Handle incoming analysis events (V2 and V3).

        V2 Message format (analysis.completed):
        {
          "event_type": "analysis.completed",
          "service": "content-analysis-v2",
          "timestamp": "2025-10-29T19:00:00.000Z",
          "payload": {
            "article_id": "uuid",
            "success": true,
            "pipeline_version": "2.0",
            "triage": {...},
            "tier1": {...},
            "tier2": {...},
            "tier3": {...},
            "relevance": {...},
            "metrics": {...}
          }
        }

        V3 Message format (analysis.v3.completed / analysis.v3.failed):
        {
          "event_type": "analysis.v3.completed",
          "service": "content-analysis-v3",
          "timestamp": "2025-11-19T10:30:00.000Z",
          "payload": {
            "article_id": "uuid",
            "success": true,
            "pipeline_version": "3.0",
            "discarded": false,
            "tier0": {...},
            "tier1": {...},
            "tier2": {...},
            "metrics": {...}
          }
        }
        """
        try:
            # Parse message
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})

            article_id = payload.get("article_id")
            success = payload.get("success", False)
            event_type = body.get("event_type", "unknown")
            pipeline_version = payload.get("pipeline_version", "unknown")

            if not article_id:
                logger.error("Invalid message: missing article_id")
                await message.reject(requeue=False)  # Send to DLQ
                return

            # Validate UUID format BEFORE database operation
            # This prevents test articles with invalid UUIDs from blocking the queue
            try:
                UUID(article_id)  # Raises ValueError if invalid
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid UUID format for article_id '{article_id}': {e}. "
                    "Rejecting to DLQ (likely a test article)."
                )
                await message.reject(requeue=False)  # Invalid UUID -> DLQ, don't retry
                return

            logger.info(
                f"Received {event_type} for article {article_id}: "
                f"success={success}, pipeline={pipeline_version}"
            )

            # Store results in database
            async with AsyncSessionLocal() as db:
                await self._store_analysis_results(db, payload)
                await db.commit()

            logger.info(f"✓ Stored analysis results for article {article_id}")

            # ACK message
            await message.ack()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            await message.reject(requeue=False)  # Malformed JSON -> DLQ
        except DataError as e:
            # Database data errors (e.g., invalid data types) are permanent
            logger.error(f"Database data error (permanent): {e}")
            await message.reject(requeue=False)  # Don't retry, send to DLQ
        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)
            # Reject with requeue ONLY for transient errors (DB connection, etc.)
            # For permanent errors, use requeue=False to avoid infinite loops
            await message.reject(requeue=True)

    async def _store_analysis_results(
        self,
        db: AsyncSession,
        payload: Dict[str, Any],
    ) -> None:
        """
        Store analysis results in article_analysis table.

        Supports both V2 and V3 payload formats:
        - V2: triage, tier1, tier2, tier3, relevance fields
        - V3: tier0, tier1, tier2 fields (no tier3, no relevance)

        ⚠️ WARNING: This writes to public.article_analysis (UNIFIED table)
        which is NEVER READ by any service!

        Frontend reads from content_analysis_v2.pipeline_executions (LEGACY table)
        via analysis_loader.py proxy to content-analysis-v2 API.

        Result: This data is orphaned and never displayed to users.

        See file header and POSTMORTEMS.md - Incident #8 for details.

        Uses UPSERT (INSERT ... ON CONFLICT) to handle duplicate messages
        (at-least-once delivery from RabbitMQ).
        """
        article_id = payload["article_id"]
        success = payload["success"]
        pipeline_version = payload.get("pipeline_version", "2.0")

        # Extract results based on pipeline version
        if pipeline_version == "3.0":
            # V3 payload format
            triage = payload.get("tier0")  # V3: tier0 = triage decision
            tier1 = payload.get("tier1")
            tier2 = payload.get("tier2")
            tier3 = None  # V3 has no tier3
            relevance = None  # V3 has no relevance scoring
        else:
            # V2 payload format (default)
            triage = payload.get("triage")
            tier1 = payload.get("tier1")
            tier2 = payload.get("tier2")
            tier3 = payload.get("tier3")
            relevance = payload.get("relevance")

        metrics = payload.get("metrics")
        error_message = payload.get("error_message") or payload.get("error")  # V3 uses "error"
        failed_agents = payload.get("failed_agents", [])

        # Extract embedding (V3 only - 1536 floats from text-embedding-3-small)
        embedding = payload.get("embedding")  # List of 1536 floats or None

        # Extract relevance score
        relevance_score = None
        score_breakdown = None
        if relevance:
            relevance_score = relevance.get("overall_score")
            score_breakdown = relevance.get("score_breakdown")

        # UPSERT query (idempotent - safe for duplicate messages)
        query = text("""
            INSERT INTO article_analysis (
                article_id,
                pipeline_version,
                success,
                triage_results,
                tier1_results,
                tier2_results,
                tier3_results,
                relevance_score,
                score_breakdown,
                metrics,
                error_message,
                failed_agents,
                embedding,
                created_at,
                updated_at
            ) VALUES (
                :article_id,
                :pipeline_version,
                :success,
                CAST(:triage_results AS jsonb),
                CAST(:tier1_results AS jsonb),
                CAST(:tier2_results AS jsonb),
                CAST(:tier3_results AS jsonb),
                :relevance_score,
                CAST(:score_breakdown AS jsonb),
                CAST(:metrics AS jsonb),
                :error_message,
                :failed_agents,
                CAST(:embedding AS vector),
                NOW(),
                NOW()
            )
            ON CONFLICT (article_id)
            DO UPDATE SET
                pipeline_version = EXCLUDED.pipeline_version,
                success = EXCLUDED.success,
                triage_results = EXCLUDED.triage_results,
                tier1_results = EXCLUDED.tier1_results,
                tier2_results = EXCLUDED.tier2_results,
                tier3_results = EXCLUDED.tier3_results,
                relevance_score = EXCLUDED.relevance_score,
                score_breakdown = EXCLUDED.score_breakdown,
                metrics = EXCLUDED.metrics,
                error_message = EXCLUDED.error_message,
                failed_agents = EXCLUDED.failed_agents,
                embedding = COALESCE(EXCLUDED.embedding, article_analysis.embedding),
                updated_at = NOW()
        """)

        # Format embedding for pgvector: '[0.1, 0.2, ...]' or None
        embedding_str = None
        if embedding and isinstance(embedding, list) and len(embedding) == 1536:
            embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"

        await db.execute(query, {
            "article_id": article_id,
            "pipeline_version": pipeline_version,
            "success": success,
            "triage_results": json.dumps(triage) if triage else None,
            "tier1_results": json.dumps(tier1) if tier1 else None,
            "tier2_results": json.dumps(tier2) if tier2 else None,
            "tier3_results": json.dumps(tier3) if tier3 else None,
            "relevance_score": relevance_score,
            "score_breakdown": json.dumps(score_breakdown) if score_breakdown else None,
            "metrics": json.dumps(metrics) if metrics else None,
            "error_message": error_message,
            "failed_agents": failed_agents,
            "embedding": embedding_str,
        })

    async def start_consuming(self) -> None:
        """Start consuming messages from queue."""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ")

        logger.info("Starting message consumption...")

        # Start consuming
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                if self.shutdown:
                    logger.info("Shutdown signal received, stopping...")
                    break

                await self.handle_message(message)

    async def run(self) -> None:
        """Main entry point for worker."""
        try:
            await self.connect()
            await self.start_consuming()
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal (SIGINT, SIGTERM)."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown = True


async def main():
    """Main entry point."""
    logger.info("================================================================================")
    logger.info("Analysis Results Consumer Worker")
    logger.info("================================================================================")
    logger.info("Service: feed-service")
    logger.info("Purpose: Consume analysis events from V2 and V3 pipelines")
    logger.info("Queue: analysis_results_queue")
    logger.info("Routing Keys:")
    logger.info("  - analysis.completed (V2)")
    logger.info("  - analysis.v3.completed (V3)")
    logger.info("  - analysis.v3.failed (V3)")
    logger.info("================================================================================")

    consumer = AnalysisConsumer()

    # Register shutdown handlers
    signal.signal(signal.SIGINT, consumer.handle_shutdown)
    signal.signal(signal.SIGTERM, consumer.handle_shutdown)

    try:
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
