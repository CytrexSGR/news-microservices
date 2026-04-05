"""
RabbitMQ event consumer for Narrative Service

Listens for narrative.frame.detected events from content-analysis-v3
and persists frames to the narrative_frames table.
"""
import aio_pika
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.narrative_frame import NarrativeFrame
from app.services.narrative_clustering import narrative_clustering_service

logger = logging.getLogger(__name__)


class NarrativeFrameConsumer:
    """Consumer for narrative.frame.detected events from content-analysis-v3"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._running = False

    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ URL from settings"""
        return (
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
            f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
        )

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                client_properties={"service": "narrative-service"}
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange for events (same as other services)
            self.exchange = await self.channel.declare_exchange(
                "news.events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            logger.info("Connected to RabbitMQ exchange: news.events")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def start_consuming(self):
        """Start consuming narrative.frame.detected events"""
        if not self.channel or not self.exchange:
            await self.connect()

        # Declare queue for narrative frame events
        queue = await self.channel.declare_queue(
            "narrative_frame_events",
            durable=True,
            arguments={
                "x-message-ttl": 3600000,  # 1 hour TTL
                "x-max-length": 10000,  # Max 10k messages
            }
        )

        # Bind to narrative event topics
        routing_keys = [
            "narrative.frame.detected",  # From content-analysis-v3
            "analysis.v3.completed",      # Backup: full V3 analysis with NARRATIVE_ANALYST
        ]

        for routing_key in routing_keys:
            await queue.bind(self.exchange, routing_key=routing_key)
            logger.info(f"Bound to routing key: {routing_key}")

        self._running = True
        # Start consuming messages
        await queue.consume(self.process_message)
        logger.info("Started consuming RabbitMQ events for narrative frames")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """
        Process incoming RabbitMQ message

        Expected message format for narrative.frame.detected:
        {
            "event_type": "narrative.frame.detected",
            "service": "content-analysis-v3",
            "timestamp": "2025-12-26T20:00:00Z",
            "payload": {
                "article_id": "uuid-string",
                "frames": [...],
                "dominant_frame": "conflict",
                "entity_portrayals": {...},
                "narrative_tension": 0.75,
                "propaganda_indicators": [...]
            }
        }
        """
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                event_type = payload.get("event_type")
                event_payload = payload.get("payload", {})
                service = payload.get("service", "unknown")

                logger.info(f"Processing event: {event_type} from {service}")

                # Route to appropriate handler
                if event_type == "narrative.frame.detected":
                    await self.handle_frame_detected(event_payload)
                elif event_type == "analysis.v3.completed":
                    await self.handle_analysis_completed(event_payload)
                else:
                    logger.debug(f"Ignoring event type: {event_type}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON in RabbitMQ message")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)

    async def handle_frame_detected(self, payload: Dict[str, Any]):
        """
        Handle narrative.frame.detected event

        Persists frames to narrative_frames table and triggers clustering update.

        Payload format:
        {
            "article_id": "uuid-string",
            "frames": [
                {
                    "frame_type": "conflict",
                    "confidence": 0.85,
                    "entities": ["Entity1", "Entity2"],
                    "text_excerpt": "...",
                    "role_mapping": {"Entity1": "victim", "Entity2": "threat"}
                }
            ],
            "dominant_frame": "conflict",
            "entity_portrayals": {"Entity1": ["victim"]},
            "narrative_tension": 0.75,
            "propaganda_indicators": []
        }
        """
        article_id = payload.get("article_id")
        frames_data = payload.get("frames", [])

        if not article_id:
            logger.warning("narrative.frame.detected event missing article_id")
            return

        if not frames_data:
            logger.debug(f"No frames in narrative.frame.detected for article {article_id}")
            return

        logger.info(f"Processing {len(frames_data)} narrative frames for article {article_id}")

        try:
            async with AsyncSessionLocal() as db:
                frames_created = 0

                for frame_data in frames_data:
                    frame = self._create_frame_from_payload(
                        event_id=uuid.UUID(article_id),
                        frame_data=frame_data,
                        metadata={
                            "dominant_frame": payload.get("dominant_frame"),
                            "narrative_tension": payload.get("narrative_tension"),
                            "propaganda_indicators": payload.get("propaganda_indicators", []),
                        }
                    )
                    db.add(frame)
                    frames_created += 1

                await db.commit()
                logger.info(f"Created {frames_created} narrative frames for article {article_id}")

                # Trigger cluster update (async - don't wait)
                # This runs in background to update narrative clusters
                try:
                    result = await narrative_clustering_service.update_narrative_clusters(db)
                    logger.info(f"Cluster update result: {result}")
                except Exception as cluster_error:
                    logger.warning(f"Cluster update failed (non-critical): {cluster_error}")

        except Exception as e:
            logger.error(f"Error persisting frames for article {article_id}: {e}", exc_info=True)

    async def handle_analysis_completed(self, payload: Dict[str, Any]):
        """
        Handle analysis.v3.completed event (backup for narrative data)

        Extracts NARRATIVE_ANALYST data from tier2 payload.

        Payload format:
        {
            "article_id": "uuid-string",
            "tier2": {
                "NARRATIVE_ANALYST": {
                    "frames": [...],
                    "dominant_frame": "...",
                    ...
                }
            }
        }
        """
        article_id = payload.get("article_id")
        tier2_data = payload.get("tier2", {})
        narrative_data = tier2_data.get("NARRATIVE_ANALYST")

        if not article_id or not narrative_data:
            # Not every V3 analysis has narrative data - that's fine
            return

        # Convert to frame.detected format and process
        frames_payload = {
            "article_id": article_id,
            "frames": narrative_data.get("frames", []),
            "dominant_frame": narrative_data.get("dominant_frame"),
            "entity_portrayals": narrative_data.get("entity_portrayals", {}),
            "narrative_tension": narrative_data.get("narrative_tension", 0.0),
            "propaganda_indicators": narrative_data.get("propaganda_indicators", []),
        }

        await self.handle_frame_detected(frames_payload)

    def _create_frame_from_payload(
        self,
        event_id: uuid.UUID,
        frame_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> NarrativeFrame:
        """
        Create NarrativeFrame model from event payload

        Args:
            event_id: Article UUID
            frame_data: Individual frame data from event
            metadata: Additional context (dominant_frame, tension, etc.)

        Returns:
            NarrativeFrame model instance
        """
        # Parse entities - convert list to structured format
        entities_list = frame_data.get("entities", [])
        entities_structured = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "raw": entities_list  # Keep original for reference
        }

        # Role mapping provides additional context
        role_mapping = frame_data.get("role_mapping", {})

        return NarrativeFrame(
            id=uuid.uuid4(),
            event_id=event_id,
            frame_type=frame_data.get("frame_type", "unknown"),
            confidence=max(0.0, min(1.0, float(frame_data.get("confidence", 0.5)))),
            text_excerpt=frame_data.get("text_excerpt", "")[:500],  # Limit length
            entities=entities_structured,
            frame_metadata={
                "role_mapping": role_mapping,
                "dominant_frame": metadata.get("dominant_frame"),
                "narrative_tension": metadata.get("narrative_tension"),
                "propaganda_indicators": metadata.get("propaganda_indicators", []),
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def close(self):
        """Close RabbitMQ connection"""
        self._running = False
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("RabbitMQ connection closed")


# Singleton instance
_consumer_instance: Optional[NarrativeFrameConsumer] = None


def get_consumer() -> NarrativeFrameConsumer:
    """Get or create global consumer instance"""
    global _consumer_instance

    if _consumer_instance is None:
        _consumer_instance = NarrativeFrameConsumer()

    return _consumer_instance


async def close_consumer():
    """Close global consumer"""
    global _consumer_instance

    if _consumer_instance:
        await _consumer_instance.close()
        _consumer_instance = None
