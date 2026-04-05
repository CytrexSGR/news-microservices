#!/usr/bin/env python3
"""
Backfill Narrative Frames

Reads existing framing_analysis data from article_analysis table
and publishes narrative.frame.detected events to RabbitMQ.

No LLM API calls required - uses already analyzed data.

Usage:
    docker exec news-content-analysis-v3-api python /app/scripts/backfill_narrative_frames.py

Or run directly:
    python scripts/backfill_narrative_frames.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

import asyncpg
import aio_pika
from aio_pika import ExchangeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "news_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=")
POSTGRES_DB = os.getenv("POSTGRES_DB", "news_mcp")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "news.events")

# Batch settings
BATCH_SIZE = 100
PROGRESS_LOG_INTERVAL = 500


class NarrativeBackfill:
    """Backfill narrative frames from existing analysis data."""

    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.rmq_connection: Optional[aio_pika.RobustConnection] = None
        self.rmq_channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.processed = 0
        self.published = 0
        self.skipped = 0
        self.errors = 0

    async def connect(self):
        """Connect to PostgreSQL and RabbitMQ."""
        # PostgreSQL
        logger.info(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}...")
        self.pg_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            min_size=2,
            max_size=10
        )
        logger.info("✓ PostgreSQL connected")

        # RabbitMQ
        rabbitmq_url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
        logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}...")
        self.rmq_connection = await aio_pika.connect_robust(rabbitmq_url)
        self.rmq_channel = await self.rmq_connection.channel()
        self.exchange = await self.rmq_channel.declare_exchange(
            RABBITMQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True
        )
        logger.info("✓ RabbitMQ connected")

    async def disconnect(self):
        """Close connections."""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.rmq_connection:
            await self.rmq_connection.close()
        logger.info("Connections closed")

    async def get_total_count(self) -> int:
        """Get total number of articles with framing data."""
        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COUNT(*)
                FROM article_analysis
                WHERE tier2_results->'BIAS_DETECTOR'->'framing_analysis' IS NOT NULL
            """)
            return result

    async def fetch_articles_batch(self, offset: int) -> List[asyncpg.Record]:
        """Fetch a batch of articles with framing data."""
        async with self.pg_pool.acquire() as conn:
            return await conn.fetch("""
                SELECT
                    article_id,
                    tier2_results->'BIAS_DETECTOR'->'framing_analysis' as framing,
                    tier2_results->'BIAS_DETECTOR'->'perspective_balance' as perspectives,
                    tier2_results->'BIAS_DETECTOR'->'emotional_language' as emotional,
                    created_at
                FROM article_analysis
                WHERE tier2_results->'BIAS_DETECTOR'->'framing_analysis' IS NOT NULL
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, BATCH_SIZE, offset)

    def extract_entities_from_perspectives(self, perspectives: Dict) -> List[str]:
        """Extract entity names from perspective_balance viewpoint_details."""
        entities = []
        if not perspectives:
            return entities

        viewpoints = perspectives.get("viewpoint_details", [])
        for vp in viewpoints:
            viewpoint = vp.get("viewpoint", "")
            if viewpoint:
                # Clean up viewpoint names like "Mediator (China)" -> "China"
                if "(" in viewpoint and ")" in viewpoint:
                    # Extract the part in parentheses as the main entity
                    start = viewpoint.find("(") + 1
                    end = viewpoint.find(")")
                    entities.append(viewpoint[start:end])
                else:
                    entities.append(viewpoint)

        return entities

    def build_role_mapping(self, perspectives: Dict, frame_type: str) -> Dict[str, str]:
        """Build entity role mapping from perspectives."""
        role_mapping = {}
        if not perspectives:
            return role_mapping

        viewpoints = perspectives.get("viewpoint_details", [])
        for vp in viewpoints:
            viewpoint = vp.get("viewpoint", "")
            sentiment = vp.get("sentiment", "neutral")

            # Determine role based on sentiment and prominence
            if sentiment == "positive":
                role = "protagonist"
            elif sentiment == "negative":
                role = "antagonist"
            else:
                role = frame_type.replace("_frame", "")

            if viewpoint:
                if "(" in viewpoint and ")" in viewpoint:
                    entity_name = viewpoint[viewpoint.find("(")+1:viewpoint.find(")")]
                else:
                    entity_name = viewpoint
                role_mapping[entity_name] = role

        return role_mapping

    def transform_to_narrative_event(
        self,
        article_id: UUID,
        framing: Dict,
        perspectives: Dict,
        emotional: Dict
    ) -> Dict[str, Any]:
        """Transform analysis data to narrative.frame.detected event format."""
        frames = []

        # Primary frame
        primary_frame = framing.get("primary_frame", "")
        if primary_frame:
            frame_desc = framing.get("frame_descriptions", {}).get(primary_frame, {})
            entities = self.extract_entities_from_perspectives(perspectives)

            frames.append({
                "frame_type": primary_frame.replace("_frame", ""),
                "confidence": frame_desc.get("confidence", 0.7),
                "entities": entities,
                "text_excerpt": frame_desc.get("effect", "")[:500],
                "role_mapping": self.build_role_mapping(perspectives, primary_frame)
            })

        # Secondary frames
        for secondary in framing.get("secondary_frames", []):
            frame_desc = framing.get("frame_descriptions", {}).get(secondary, {})
            frames.append({
                "frame_type": secondary.replace("_frame", ""),
                "confidence": frame_desc.get("confidence", 0.6),
                "entities": [],  # Secondary frames don't get entity mapping
                "text_excerpt": frame_desc.get("effect", "")[:500],
                "role_mapping": {}
            })

        # Calculate narrative tension from emotional language
        narrative_tension = 0.0
        if emotional:
            narrative_tension = emotional.get("overall_emotional_intensity", 0.0)

        # Build entity portrayals from perspectives
        entity_portrayals = {}
        if perspectives:
            balance = perspectives.get("balance_assessment", {})
            dominant = perspectives.get("dominant_viewpoint", "")
            if dominant:
                entity_portrayals["dominant"] = [dominant]

        return {
            "event_type": "narrative.frame.detected",
            "service": "backfill-script",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "article_id": str(article_id),
                "frames": frames,
                "dominant_frame": primary_frame.replace("_frame", "") if primary_frame else None,
                "entity_portrayals": entity_portrayals,
                "narrative_tension": narrative_tension,
                "propaganda_indicators": [],
                "backfill": True  # Mark as backfilled data
            }
        }

    async def publish_event(self, event: Dict[str, Any]):
        """Publish narrative.frame.detected event to RabbitMQ."""
        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await self.exchange.publish(
            message,
            routing_key="narrative.frame.detected"
        )

    async def run(self, dry_run: bool = False):
        """Execute the backfill."""
        try:
            await self.connect()

            total = await self.get_total_count()
            logger.info(f"Found {total} articles with framing data to process")

            if dry_run:
                logger.info("DRY RUN - no events will be published")

            offset = 0
            while offset < total:
                batch = await self.fetch_articles_batch(offset)

                if not batch:
                    break

                for row in batch:
                    try:
                        article_id = row["article_id"]
                        framing = json.loads(row["framing"]) if row["framing"] else {}
                        perspectives = json.loads(row["perspectives"]) if row["perspectives"] else {}
                        emotional = json.loads(row["emotional"]) if row["emotional"] else {}

                        # Skip if no meaningful frame data
                        if not framing.get("primary_frame"):
                            self.skipped += 1
                            continue

                        event = self.transform_to_narrative_event(
                            article_id, framing, perspectives, emotional
                        )

                        if not dry_run:
                            await self.publish_event(event)

                        self.published += 1

                    except Exception as e:
                        logger.error(f"Error processing article {row['article_id']}: {e}")
                        self.errors += 1

                    self.processed += 1

                offset += BATCH_SIZE

                # Progress logging
                if self.processed % PROGRESS_LOG_INTERVAL == 0:
                    pct = (self.processed / total) * 100
                    logger.info(
                        f"Progress: {self.processed}/{total} ({pct:.1f}%) - "
                        f"Published: {self.published}, Skipped: {self.skipped}, Errors: {self.errors}"
                    )

            # Final summary
            logger.info("=" * 60)
            logger.info("BACKFILL COMPLETE")
            logger.info(f"  Total processed: {self.processed}")
            logger.info(f"  Events published: {self.published}")
            logger.info(f"  Skipped (no data): {self.skipped}")
            logger.info(f"  Errors: {self.errors}")
            logger.info("=" * 60)

        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Backfill narrative frames from existing analysis data")
    parser.add_argument("--dry-run", action="store_true", help="Don't publish events, just simulate")
    args = parser.parse_args()

    backfill = NarrativeBackfill()
    await backfill.run(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
