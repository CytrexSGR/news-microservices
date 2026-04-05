"""
Narrative Frame Consumer

Consumes `narrative.frame.detected` events from RabbitMQ and creates
NarrativeFrame nodes with FRAMED_AS relationships to Entity nodes in Neo4j.

This enables graph-based narrative analysis:
- Which entities are framed as victims/heroes/threats?
- Which narratives dominate for specific entities?
- How do narrative patterns evolve over time?
"""

import logging
import json
import asyncio
import time
import uuid
from typing import Optional, Dict, Any, List
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractQueue

from app.config import settings
from app.services.neo4j_service import neo4j_service
from app.services.cypher_validator import CypherSyntaxError

logger = logging.getLogger(__name__)


# Non-retriable errors - these should go to DLQ immediately
NON_RETRIABLE_ERRORS = (
    CypherSyntaxError,
    json.JSONDecodeError,
    KeyError,
    ValueError,
)

# Narrative frame queue settings
NARRATIVE_QUEUE_NAME = "knowledge_graph_narrative_frames"
NARRATIVE_ROUTING_KEY = "narrative.frame.detected"


class NarrativeFrameConsumer:
    """RabbitMQ consumer for narrative.frame.detected events."""

    def __init__(self):
        """Initialize consumer (connection created on startup)."""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.queue: Optional[AbstractQueue] = None
        self._running = False

    async def connect(self):
        """
        Connect to RabbitMQ and setup queue/bindings.

        Includes Dead Letter Queue (DLQ) configuration for non-retriable errors.
        """
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url} for narrative frames...")

            self.connection = await connect_robust(
                settings.rabbitmq_url,
                timeout=30
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare main exchange (should already exist)
            exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare Dead Letter Exchange (DLX)
            dlx_name = f"{settings.RABBITMQ_EXCHANGE}.dlx"
            await self.channel.declare_exchange(
                dlx_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare Dead Letter Queue (DLQ)
            dlq_name = f"{NARRATIVE_QUEUE_NAME}.dlq"
            dlq = await self.channel.declare_queue(
                dlq_name,
                durable=True
            )
            await dlq.bind(dlx_name, routing_key="#")

            # Declare main queue with DLQ routing
            self.queue = await self.channel.declare_queue(
                NARRATIVE_QUEUE_NAME,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': dlx_name,
                    'x-message-ttl': 86400000,  # 24 hours max retention
                }
            )

            # Bind queue to routing key
            await self.queue.bind(exchange, routing_key=NARRATIVE_ROUTING_KEY)

            logger.info(
                f"Narrative consumer connected. Queue: {NARRATIVE_QUEUE_NAME}, "
                f"Routing: {NARRATIVE_ROUTING_KEY}, DLQ: {dlq_name}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ for narrative consumer: {e}", exc_info=True)
            raise

    async def start_consuming(self):
        """Start consuming messages from queue."""
        if not self.queue:
            raise RuntimeError("Queue not initialized. Call connect() first.")

        try:
            logger.info("Starting narrative frame consumption...")
            self._running = True
            await self.queue.consume(self._handle_message)
            logger.info("Narrative frame consumer started successfully")

        except Exception as e:
            logger.error(f"Failed to start narrative consumer: {e}", exc_info=True)
            raise

    async def _handle_message(self, message: IncomingMessage):
        """
        Handle a single narrative.frame.detected message.

        Expected payload format:
        {
            "event_type": "narrative.frame.detected",
            "service": "content-analysis-v3",
            "timestamp": "2025-12-26T20:00:00Z",
            "payload": {
                "article_id": "uuid-string",
                "frames": [
                    {
                        "frame_type": "victim|hero|threat|...",
                        "confidence": 0.85,
                        "entities": ["Entity1", "Entity2"],
                        "text_excerpt": "...",
                        "role_mapping": {"Entity1": "victim", ...}
                    }
                ],
                "dominant_frame": "conflict",
                "entity_portrayals": {"Entity1": ["victim"]},
                "narrative_tension": 0.75,
                "propaganda_indicators": []
            }
        }
        """
        start_time = time.time()
        article_id = "unknown"

        try:
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})
            article_id = payload.get("article_id", "unknown")

            frames = payload.get("frames", [])
            dominant_frame = payload.get("dominant_frame")
            entity_portrayals = payload.get("entity_portrayals", {})
            narrative_tension = payload.get("narrative_tension", 0.0)
            propaganda_indicators = payload.get("propaganda_indicators", [])

            if not frames:
                logger.debug(f"No frames in narrative event for article {article_id}")
                await message.ack()
                return

            logger.info(
                f"Processing narrative event: article_id={article_id}, "
                f"frames={len(frames)}, dominant={dominant_frame}"
            )

            # Process each frame - create NarrativeFrame nodes and relationships
            for frame_data in frames:
                await self._ingest_narrative_frame(
                    article_id=article_id,
                    frame_data=frame_data,
                    dominant_frame=dominant_frame,
                    narrative_tension=narrative_tension,
                    propaganda_indicators=propaganda_indicators
                )

            duration = time.time() - start_time
            logger.info(
                f"Ingested {len(frames)} narrative frames for article {article_id} "
                f"in {duration:.2f}s"
            )

            await message.ack()

        except NON_RETRIABLE_ERRORS as e:
            duration = time.time() - start_time
            logger.error(
                f"Non-retriable error for article_id={article_id} in {duration:.2f}s: "
                f"{type(e).__name__}: {e}",
                extra={"article_id": article_id, "retriable": False}
            )
            await message.reject(requeue=False)

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.warning(
                f"Timeout for article_id={article_id} after {duration:.2f}s",
                extra={"article_id": article_id, "retriable": True}
            )
            await message.reject(requeue=True)

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Unexpected error for article_id={article_id} in {duration:.2f}s: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
                extra={"article_id": article_id, "retriable": True}
            )
            await message.reject(requeue=True)

    async def _ingest_narrative_frame(
        self,
        article_id: str,
        frame_data: Dict[str, Any],
        dominant_frame: Optional[str],
        narrative_tension: float,
        propaganda_indicators: List[str]
    ):
        """
        Ingest a single narrative frame into Neo4j.

        Creates:
        1. NarrativeFrame node with frame properties
        2. FRAMED_AS relationships from entities to the NarrativeFrame

        Graph structure:
        (Entity)-[:FRAMED_AS {role: "victim", confidence: 0.85}]->(NarrativeFrame)

        Args:
            article_id: Article UUID string
            frame_data: Individual frame data from event
            dominant_frame: The dominant frame type for this article
            narrative_tension: Overall tension score (0-1)
            propaganda_indicators: List of detected propaganda techniques
        """
        frame_id = str(uuid.uuid4())
        frame_type = frame_data.get("frame_type", "unknown")
        confidence = float(frame_data.get("confidence", 0.5))
        entities = frame_data.get("entities", [])
        text_excerpt = frame_data.get("text_excerpt", "")[:500]
        role_mapping = frame_data.get("role_mapping", {})

        # Build Cypher to create NarrativeFrame and link to entities
        # First: Create the NarrativeFrame node
        cypher_create_frame = """
        MERGE (nf:NarrativeFrame {frame_id: $frame_id})
        ON CREATE SET
            nf.article_id = $article_id,
            nf.frame_type = $frame_type,
            nf.confidence = $confidence,
            nf.text_excerpt = $text_excerpt,
            nf.is_dominant = $is_dominant,
            nf.narrative_tension = $narrative_tension,
            nf.propaganda_indicators = $propaganda_indicators,
            nf.created_at = datetime()
        ON MATCH SET
            nf.last_seen = datetime()
        RETURN nf
        """

        await neo4j_service.execute_write(
            cypher_create_frame,
            parameters={
                "frame_id": frame_id,
                "article_id": article_id,
                "frame_type": frame_type,
                "confidence": confidence,
                "text_excerpt": text_excerpt,
                "is_dominant": frame_type == dominant_frame,
                "narrative_tension": narrative_tension,
                "propaganda_indicators": propaganda_indicators
            }
        )

        # Second: Link EXISTING entities to NarrativeFrame (no entity creation)
        # NOTE: Entity creation via MERGE with type='UNKNOWN' was removed (2025-12-27)
        # because it created garbage entities from LLM frame descriptions.
        # Entities should only be created by relationships_consumer with proper types.
        if entities:
            for entity_name in entities:
                role = role_mapping.get(entity_name, frame_type)

                # Only MATCH existing entities with proper types, don't create new ones
                cypher_link_entity = """
                MATCH (e:Entity {name: $entity_name})
                WHERE e.type IS NOT NULL AND e.type <> 'UNKNOWN'
                WITH e
                MATCH (nf:NarrativeFrame {frame_id: $frame_id})
                MERGE (e)-[r:FRAMED_AS]->(nf)
                ON CREATE SET
                    r.role = $role,
                    r.confidence = $confidence,
                    r.created_at = datetime()
                ON MATCH SET
                    r.last_seen = datetime()
                RETURN e, r, nf
                """

                await neo4j_service.execute_write(
                    cypher_link_entity,
                    parameters={
                        "entity_name": entity_name,
                        "frame_id": frame_id,
                        "role": role,
                        "confidence": confidence
                    }
                )

        logger.debug(
            f"Created NarrativeFrame {frame_id[:8]}... "
            f"(type={frame_type}, entities={len(entities)})"
        )

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        self._running = False
        try:
            if self.connection:
                await self.connection.close()
                logger.info("Narrative consumer RabbitMQ connection closed")

        except Exception as e:
            logger.error(f"Error closing narrative consumer: {e}", exc_info=True)


# Global consumer instance
narrative_consumer = NarrativeFrameConsumer()
