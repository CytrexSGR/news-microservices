"""
Analysis Request Consumer for Content-Analysis-V3

Consumes analysis.v3.request events from RabbitMQ and executes the V3 pipeline.

Event Flow:
1. Other services (e.g., feed-service) publish analysis.v3.request to news.events exchange
2. This worker consumes from analysis_v3_requests_queue (bound to analysis.v3.request)
3. Executes V3 pipeline (Tier0 → Tier1 → Tier2)
4. Publishes analysis.v3.completed or analysis.v3.failed event
5. ACKs message (or REJECTs to DLQ on failure)

Message Format:
    {
        "event_type": "analysis.v3.request",
        "service": "feed-service",
        "timestamp": "2025-11-19T09:00:00.000Z",
        "payload": {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Article Title",
            "url": "https://example.com/article",
            "content": "Article content...",
            "run_tier2": true
        }
    }
"""
import asyncio
import json
import logging
import signal
import sys
from typing import Optional
from uuid import UUID, uuid4

import aio_pika
from aio_pika import IncomingMessage, ExchangeType
from sqlalchemy.exc import DataError

from app.core.config import settings
from app.core.database import get_db_pool, init_db_pool, close_db_pool
from app.pipeline.tier0.triage import Tier0Triage
from app.pipeline.tier1.foundation import Tier1Foundation
from app.pipeline.tier2.orchestrator import Tier2Orchestrator
from app.messaging.event_publisher import get_event_publisher
from app.infrastructure.graph_client import V3GraphClient
from app.providers.base import ProviderError, ProviderRateLimitError, ProviderTimeoutError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AnalysisRequestConsumer:
    """Consumes analysis.v3.request events and executes V3 pipeline."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.graph_client: Optional[V3GraphClient] = None
        self.shutdown = False

    async def connect(self) -> None:
        """Connect to RabbitMQ and set up queue."""
        try:
            # Build RabbitMQ URL
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
                f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            )

            # Log without exposing password
            logger.info(
                f"Connecting to RabbitMQ: amqp://{settings.RABBITMQ_USER}:***@"
                f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            )

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={"service": "content-analysis-v3-consumer"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(
                prefetch_count=settings.V3_QUEUE_PREFETCH_COUNT
            )

            # Declare exchange (should already exist, created by other services)
            exchange = await self.channel.declare_exchange(
                "news.events",
                type=ExchangeType.TOPIC,
                durable=True,
            )

            # Declare DLQ (dead letter queue) for failed messages
            dlq = await self.channel.declare_queue(
                "analysis_v3_requests_queue_dlq",
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            # Declare main queue with DLQ binding
            self.queue = await self.channel.declare_queue(
                "analysis_v3_requests_queue",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",  # Default exchange
                    "x-dead-letter-routing-key": "analysis_v3_requests_queue_dlq",
                },
            )

            # Bind queue to exchange with routing key
            await self.queue.bind(
                exchange=exchange,
                routing_key="analysis.v3.request",  # Only consume V3 requests
            )

            logger.info("✓ Connected to RabbitMQ and bound to analysis.v3.request events")

            # Initialize Graph Client for Neo4j Knowledge Graph
            self.graph_client = V3GraphClient(
                uri=settings.NEO4J_URI,
                user=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD
            )
            try:
                await self.graph_client.connect()
                logger.info("✓ Graph client connected to Neo4j")
            except Exception as graph_error:
                logger.warning(
                    f"Failed to connect graph client to Neo4j: {graph_error}. "
                    "Graph publishing will be skipped."
                )
                self.graph_client = None

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ and Neo4j."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        if self.graph_client:
            await self.graph_client.disconnect()
        logger.info("Disconnected from RabbitMQ and Neo4j")

    async def handle_message(self, message: IncomingMessage) -> None:
        """
        Handle incoming analysis.v3.request event.

        Message format:
        {
          "event_type": "analysis.v3.request",
          "service": "feed-service",
          "timestamp": "2025-11-19T09:00:00.000Z",
          "payload": {
            "article_id": "uuid",
            "title": "Article Title",
            "url": "https://example.com/article",
            "content": "Article content...",
            "run_tier2": true
          }
        }
        """
        try:
            # Parse message
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})

            article_id = payload.get("article_id")
            title = payload.get("title")
            url = payload.get("url")
            content = payload.get("content")
            run_tier2 = payload.get("run_tier2", True)

            # Extract or generate correlation ID for distributed tracing
            correlation_id = (
                body.get("correlation_id") or
                payload.get("correlation_id") or
                str(uuid4())
            )

            if not article_id or not title or not content:
                logger.error("Invalid message: missing required fields")
                await message.reject(requeue=False)  # Send to DLQ
                return

            # Validate UUID format BEFORE processing
            try:
                UUID(article_id)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid UUID format for article_id '{article_id}': {e}. "
                    "Rejecting to DLQ."
                )
                await message.reject(requeue=False)
                return

            logger.info(
                f"[{correlation_id}] Received analysis.v3.request for article {article_id}: "
                f"title='{title[:50]}...', run_tier2={run_tier2}"
            )

            # Execute pipeline
            await self._run_pipeline(article_id, title, url, content, run_tier2, correlation_id)

            logger.info(f"[{correlation_id}] ✓ Completed V3 analysis for article {article_id}")

            # ACK message
            await message.ack()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            await message.reject(requeue=False)  # Malformed JSON -> DLQ

        except DataError as e:
            logger.error(f"Database data error (permanent): {e}")
            await message.reject(requeue=False)  # Don't retry, send to DLQ

        except ValueError as e:
            # Schema validation - permanent failure
            logger.error(f"Validation error (permanent): {e}")
            await message.reject(requeue=False)  # Send to DLQ

        except (ProviderRateLimitError, ProviderTimeoutError) as e:
            # Transient provider errors - requeue for retry
            logger.warning(f"Transient error, requeueing: {e}")
            await message.reject(requeue=True)  # Retry later

        except ProviderError as e:
            # Provider errors - permanent by default
            logger.error(f"Provider error (permanent): {e}")
            await message.reject(requeue=False)  # Send to DLQ

        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)
            # Unknown errors - requeue for safety
            await message.reject(requeue=True)

    async def _run_pipeline(
        self,
        article_id: str,
        title: str,
        url: Optional[str],
        content: str,
        run_tier2: bool,
        correlation_id: str,
    ) -> None:
        """
        Execute V3 analysis pipeline and publish completion event.

        Pipeline: Tier0 (Triage) → Tier1 (Foundation) → Tier2 (Specialists)

        Args:
            article_id: Article UUID
            title: Article title
            url: Article URL (optional)
            content: Article content
            run_tier2: Whether to run Tier2 specialists
            correlation_id: Correlation ID for distributed tracing
        """
        try:
            # Get database pool
            db_pool = await get_db_pool()

            # Get event publisher
            publisher = await get_event_publisher()

            # Tier0: Triage
            tier0 = Tier0Triage(db_pool)
            triage_decision = await tier0.execute(
                article_id=article_id,
                title=title,
                url=url,
                content=content,
            )

            logger.info(
                f"Tier0 complete for {article_id}: "
                f"keep={triage_decision.keep}, priority={triage_decision.PriorityScore}"
            )

            # Create Article node in Knowledge Graph with Tier0 data
            if self.graph_client and triage_decision.keep:
                try:
                    await self.graph_client.create_article_node(
                        article_id=article_id,
                        tier0_data={
                            "PriorityScore": triage_decision.PriorityScore,
                            "category": triage_decision.category,
                            "keep": triage_decision.keep,
                            "tokens_used": triage_decision.tokens_used,
                            "cost_usd": triage_decision.cost_usd,
                            "model": triage_decision.model
                        },
                        article_metadata={
                            "title": title,
                            "url": url
                        }
                    )
                    logger.info(f"✓ Created Article node in Knowledge Graph for {article_id}")
                except Exception as graph_error:
                    logger.warning(
                        f"Failed to create Article node for {article_id}: {graph_error}. "
                        "Continuing with pipeline execution."
                    )

            # If not kept, skip Tier1/Tier2
            if not triage_decision.keep:
                logger.info(f"Article {article_id} discarded by Tier0 triage")

                # Publish completion event (discarded)
                await publisher.publish_event(
                    event_type="analysis.v3.completed",
                    payload={
                        "article_id": article_id,
                        "correlation_id": correlation_id,
                        "success": True,
                        "discarded": True,
                        "pipeline_version": "3.0",
                        "tier0": {
                            "keep": False,
                            "priority_score": triage_decision.PriorityScore,
                            "category": triage_decision.category,
                            "tokens_used": triage_decision.tokens_used,
                            "cost_usd": triage_decision.cost_usd,
                            "model": triage_decision.model,
                        },
                    },
                )
                return

            # Tier1: Foundation Extraction
            tier1 = Tier1Foundation(db_pool)
            tier1_results = await tier1.execute(
                article_id=article_id,
                title=title,
                url=url,
                content=content,
            )

            logger.info(
                f"Tier1 complete for {article_id}: "
                f"{len(tier1_results.entities)} entities, "
                f"{len(tier1_results.relations)} relations"
            )

            # Publish Tier1 results to Knowledge Graph (Neo4j)
            if self.graph_client:
                try:
                    await self.graph_client.publish_tier1(
                        article_id=article_id,
                        tier1_data={
                            "entities": [
                                {
                                    "name": e.name,
                                    "type": e.type,
                                    "relevance": getattr(e, "confidence", 0.0)
                                }
                                for e in tier1_results.entities
                            ],
                            "relations": [
                                {
                                    "source": r.subject,
                                    "target": r.object,
                                    "type": r.predicate,
                                    "confidence": r.confidence
                                }
                                for r in tier1_results.relations
                            ],
                            "topics": [t.keyword for t in tier1_results.topics]
                        }
                    )
                    logger.info(f"✓ Published Tier1 to Knowledge Graph for {article_id}")
                except Exception as graph_error:
                    logger.warning(
                        f"Failed to publish Tier1 to Knowledge Graph for {article_id}: {graph_error}. "
                        "Continuing with pipeline execution."
                    )

            # Generate embedding for clustering (after Tier1, before Tier2)
            embedding = None
            try:
                from app.providers.openai.provider import OpenAIProvider

                embed_provider = OpenAIProvider(
                    model="text-embedding-3-small",
                    api_key=settings.OPENAI_API_KEY,
                    timeout=30,
                )

                # Combine title + first 500 chars of content for semantic representation
                embed_text = f"{title}. {content[:500]}"
                embedding = await embed_provider.generate_embedding(embed_text)

                logger.info(
                    f"[{correlation_id}] Generated embedding for {article_id} "
                    f"(dimensions={len(embedding)})"
                )
            except Exception as e:
                logger.warning(
                    f"[{correlation_id}] Failed to generate embedding for {article_id}: {e}. "
                    "Clustering will be skipped for this article."
                )
                # Continue without embedding - clustering will skip this article

            # Tier2: Specialist Analysis (optional)
            tier2_results = None
            if run_tier2:
                tier2 = Tier2Orchestrator(db_pool)
                tier2_results = await tier2.analyze_article(
                    article_id=article_id,
                    title=title,
                    content=content,
                    tier1_results=tier1_results,
                )

                logger.info(
                    f"Tier2 complete for {article_id}: "
                    f"{len(tier2_results.active_specialists)} specialists executed"
                )

                # Publish Tier2 results to Knowledge Graph (Neo4j)
                if self.graph_client:
                    try:
                        tier2_graph_data = {}

                        # Add FINANCIAL_ANALYST data if available
                        if tier2_results.financial_metrics and tier2_results.financial_metrics.financial_metrics:
                            fin_metrics = tier2_results.financial_metrics.financial_metrics.metrics
                            tier2_graph_data["FINANCIAL_ANALYST"] = {
                                "affected_sectors": fin_metrics.get("affected_sectors", {}),
                                "market_volatility": fin_metrics.get("market_volatility", "UNKNOWN")
                            }

                        # Add GEOPOLITICAL_ANALYST data if available
                        if tier2_results.geopolitical_metrics and tier2_results.geopolitical_metrics.geopolitical_metrics:
                            geo_metrics = tier2_results.geopolitical_metrics.geopolitical_metrics
                            tier2_graph_data["GEOPOLITICAL_ANALYST"] = {
                                "affected_regions": geo_metrics.countries_involved,
                                "stability_impact": "DEGRADING" if geo_metrics.metrics.get("conflict_severity", 0) > 5 else "STABLE",
                                "spillover_risk": geo_metrics.metrics.get("regional_stability_risk", 0) / 10.0
                            }

                        # Only publish if there's data to publish
                        if tier2_graph_data:
                            await self.graph_client.publish_tier2(
                                article_id=article_id,
                                tier2_data=tier2_graph_data
                            )
                            logger.info(f"✓ Published Tier2 to Knowledge Graph for {article_id}")
                    except Exception as graph_error:
                        logger.warning(
                            f"Failed to publish Tier2 to Knowledge Graph for {article_id}: {graph_error}. "
                            "Continuing with pipeline execution."
                        )

                # Publish narrative.frame.detected event if frames were detected
                if tier2_results.narrative_frame_metrics and tier2_results.narrative_frame_metrics.narrative_frame_metrics:
                    narrative_metrics = tier2_results.narrative_frame_metrics.narrative_frame_metrics
                    if narrative_metrics.frames:
                        await publisher.publish_event(
                            event_type="narrative.frame.detected",
                            payload={
                                "article_id": article_id,
                                "correlation_id": correlation_id,
                                "frames": [
                                    {
                                        "frame_type": f.frame_type,
                                        "confidence": f.confidence,
                                        "entities": f.entities,
                                        "text_excerpt": f.text_excerpt,
                                        "role_mapping": f.role_mapping,
                                    }
                                    for f in narrative_metrics.frames
                                ],
                                "dominant_frame": narrative_metrics.dominant_frame,
                                "entity_portrayals": narrative_metrics.entity_portrayals,
                                "narrative_tension": narrative_metrics.narrative_tension,
                                "propaganda_indicators": narrative_metrics.propaganda_indicators,
                            },
                        )
                        logger.info(
                            f"✓ Published narrative.frame.detected for {article_id}: "
                            f"{len(narrative_metrics.frames)} frames detected"
                        )

            # Publish completion event
            await publisher.publish_event(
                event_type="analysis.v3.completed",
                payload={
                    "article_id": article_id,
                    "correlation_id": correlation_id,
                    "title": title,                    # For clustering-service (cluster naming)
                    "embedding": embedding,            # For clustering-service (1536 floats or None)
                    "success": True,
                    "pipeline_version": "3.0",
                    "tier0": {
                        "keep": triage_decision.keep,
                        "priority_score": triage_decision.PriorityScore,
                        "category": triage_decision.category,
                        "tokens_used": triage_decision.tokens_used,
                        "cost_usd": triage_decision.cost_usd,
                        "model": triage_decision.model,
                    },
                    "tier1": {
                        # Full arrays for frontend display (not just counts!)
                        "entities": [e.model_dump() for e in tier1_results.entities],
                        "relations": [r.model_dump() for r in tier1_results.relations],
                        "topics": [t.model_dump() for t in tier1_results.topics],

                        # Scores (flattened for backend storage)
                        "impact_score": tier1_results.impact_score,
                        "credibility_score": tier1_results.credibility_score,
                        "urgency_score": tier1_results.urgency_score,

                        # Metadata
                        "tokens_used": tier1_results.tokens_used,
                        "cost_usd": tier1_results.cost_usd,
                        "model": tier1_results.model,
                    },
                    "tier2": {
                        # Full specialist findings for frontend display
                        "TOPIC_CLASSIFIER": tier2_results.topic_classification.model_dump() if tier2_results and tier2_results.topic_classification else None,
                        "ENTITY_EXTRACTOR": tier2_results.entity_enrichment.model_dump() if tier2_results and tier2_results.entity_enrichment else None,
                        "FINANCIAL_ANALYST": tier2_results.financial_metrics.model_dump() if tier2_results and tier2_results.financial_metrics else None,
                        "GEOPOLITICAL_ANALYST": tier2_results.geopolitical_metrics.model_dump() if tier2_results and tier2_results.geopolitical_metrics else None,
                        "SENTIMENT_ANALYZER": tier2_results.sentiment_metrics.model_dump() if tier2_results and tier2_results.sentiment_metrics else None,
                        "BIAS_SCORER": tier2_results.political_bias.model_dump() if tier2_results and tier2_results.political_bias else None,
                        "NARRATIVE_ANALYST": tier2_results.narrative_frame_metrics.model_dump() if tier2_results and tier2_results.narrative_frame_metrics else None,

                        # Aggregated metadata
                        "total_tokens": tier2_results.total_tokens_used if tier2_results else 0,
                        "total_cost_usd": tier2_results.total_cost_usd if tier2_results else 0.0,
                        "specialists_executed": len(tier2_results.active_specialists) if tier2_results else 0,
                    },
                    "metrics": {
                        "tier0_cost_usd": triage_decision.cost_usd,
                        "tier1_cost_usd": tier1_results.cost_usd,
                        "tier2_cost_usd": tier2_results.total_cost_usd if tier2_results else 0.0,
                    },
                },
            )

        except ValueError as e:
            # Schema validation error - permanent failure, don't retry
            logger.error(
                f"[{correlation_id}] [{article_id}] Schema validation failed: {e}",
                exc_info=True
            )
            publisher = await get_event_publisher()
            await publisher.publish_event(
                event_type="analysis.v3.failed",
                payload={
                    "article_id": article_id,
                    "correlation_id": correlation_id,
                    "success": False,
                    "pipeline_version": "3.0",
                    "error_type": "VALIDATION_ERROR",
                    "error_message": str(e),
                },
            )
            raise

        except ProviderRateLimitError as e:
            # Rate limit - transient, should be retried
            logger.warning(
                f"[{correlation_id}] [{article_id}] LLM provider rate limited: {e}. "
                "Message will be requeued for retry."
            )
            raise  # Requeue in handle_message

        except ProviderTimeoutError as e:
            # Timeout - transient, should be retried
            logger.warning(
                f"[{correlation_id}] [{article_id}] LLM provider timed out: {e}. "
                "Message will be requeued for retry."
            )
            raise  # Requeue in handle_message

        except ProviderError as e:
            # Other provider errors - may be permanent
            logger.error(
                f"[{correlation_id}] [{article_id}] LLM provider error: {e}",
                exc_info=True
            )
            publisher = await get_event_publisher()
            await publisher.publish_event(
                event_type="analysis.v3.failed",
                payload={
                    "article_id": article_id,
                    "correlation_id": correlation_id,
                    "success": False,
                    "pipeline_version": "3.0",
                    "error_type": "PROVIDER_ERROR",
                    "error_message": str(e),
                },
            )
            raise

        except Exception as e:
            # Unexpected error - log full traceback
            logger.error(
                f"[{correlation_id}] [{article_id}] Unexpected pipeline error: {e}",
                exc_info=True
            )
            publisher = await get_event_publisher()
            await publisher.publish_event(
                event_type="analysis.v3.failed",
                payload={
                    "article_id": article_id,
                    "correlation_id": correlation_id,
                    "success": False,
                    "pipeline_version": "3.0",
                    "error_type": "UNEXPECTED_ERROR",
                    "error_message": str(e),
                },
            )
            raise

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
    """Main entry point for consumer worker."""
    logger.info("=" * 80)
    logger.info("Content-Analysis-V3 Request Consumer")
    logger.info("=" * 80)
    logger.info("Service: content-analysis-v3")
    logger.info("Purpose: Consume analysis.v3.request events and execute V3 pipeline")
    logger.info("Queue: analysis_v3_requests_queue (routing_key: analysis.v3.request)")
    logger.info("=" * 80)

    # Initialize database pool BEFORE starting consumer
    logger.info("Initializing database connection pool...")
    try:
        await init_db_pool()
        logger.info("✓ Database pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        sys.exit(1)

    consumer = AnalysisRequestConsumer()

    # Register shutdown handlers
    signal.signal(signal.SIGINT, consumer.handle_shutdown)
    signal.signal(signal.SIGTERM, consumer.handle_shutdown)

    try:
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Clean up database pool
        logger.info("Closing database connection pool...")
        await close_db_pool()
        logger.info("✓ Database pool closed")

    logger.info("Consumer shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
