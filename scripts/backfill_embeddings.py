#!/usr/bin/env python3
"""
Backfill embeddings for existing articles.

Generates embeddings for articles that don't have them yet and:
1. STORES them in article_analysis.embedding column (pgvector)
2. Optionally publishes to clustering-service via analysis.v3.completed events

Cost: ~$0.02 per 1M tokens (text-embedding-3-small)
      ~4000 articles × 500 tokens = 2M tokens = ~$0.04

Usage:
    python scripts/backfill_embeddings.py --days 4 --batch-size 50 --dry-run
    python scripts/backfill_embeddings.py --days 4 --batch-size 50
    python scripts/backfill_embeddings.py --days 4 --batch-size 50 --no-publish  # DB only, no events
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from uuid import UUID

import asyncpg
import aio_pika
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
_db_url = os.getenv("DATABASE_URL", "postgresql://news_user:news_password@localhost:5432/news_mcp")
DATABASE_URL = _db_url.replace("postgresql+asyncpg://", "postgresql://")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXCHANGE_NAME = "news.events"


class EmbeddingBackfiller:
    def __init__(self, dry_run: bool = False, publish_events: bool = True):
        self.dry_run = dry_run
        self.publish_events = publish_events
        self.db_pool = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.exchange = None
        self.openai_client = None

        # Stats
        self.processed = 0
        self.errors = 0
        self.skipped = 0
        self.stored_in_db = 0
        self.total_tokens = 0
        self.cost_per_million = 0.02  # text-embedding-3-small pricing

    async def connect(self):
        """Connect to database, RabbitMQ (if publishing), and OpenAI."""
        # Database
        logger.info("Connecting to PostgreSQL...")
        self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

        if not self.dry_run:
            # RabbitMQ (only if publishing events)
            if self.publish_events:
                logger.info("Connecting to RabbitMQ...")
                self.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
                self.rabbitmq_channel = await self.rabbitmq_connection.channel()
                self.exchange = await self.rabbitmq_channel.declare_exchange(
                    EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True
                )

            # OpenAI
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable required")
            logger.info("Initializing OpenAI client...")
            self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        logger.info("All connections established")

    async def disconnect(self):
        """Close all connections."""
        if self.db_pool:
            await self.db_pool.close()
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

    async def get_articles_without_embeddings(self, days: int = None, limit: int = None) -> list:
        """Fetch articles that need embeddings (embedding IS NULL).

        Args:
            days: If provided, only fetch from last N days. If None, fetch ALL articles.
            limit: Maximum number of articles to fetch.

        Note: Works with ANY article that has a feed_items entry, regardless of
        whether tier1_results exists. Uses title + content from feed_items directly.
        """
        if days:
            date_filter = f"AND aa.created_at >= NOW() - INTERVAL '{days} days'"
        else:
            date_filter = ""  # No date restriction - get ALL articles

        query = f"""
            SELECT
                aa.article_id,
                fi.title,
                LEFT(COALESCE(fi.content, fi.description, ''), 2000) as content_preview,
                aa.tier1_results->'entities' as entities,
                aa.tier1_results->'sentiment' as sentiment,
                aa.tier1_results->'topics' as topics,
                (aa.tier1_results->>'tension_level')::float as tension_level,
                aa.created_at
            FROM article_analysis aa
            JOIN feed_items fi ON aa.article_id = fi.id
            WHERE aa.embedding IS NULL
              AND fi.title IS NOT NULL
              {date_filter}
            ORDER BY aa.created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)

        return rows

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using OpenAI."""
        # Truncate to ~8000 chars
        truncated = text[:8000]

        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=truncated
        )

        # Track actual token usage
        self.total_tokens += response.usage.prompt_tokens

        return response.data[0].embedding

    def _parse_json(self, value):
        """Parse JSON string if needed, otherwise return as-is."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def _extract_topic_keywords(self, topics_value) -> list[str] | None:
        """Extract topic keywords from topics data."""
        topics = self._parse_json(topics_value)
        if topics is None:
            return None
        if isinstance(topics, list):
            # Extract 'keyword' from each dict, or use string directly
            return [t.get("keyword", str(t)) if isinstance(t, dict) else str(t) for t in topics]
        return None

    async def store_embedding_in_db(self, article_id: str, embedding: list[float]):
        """Store embedding directly in article_analysis table."""
        # Format embedding for pgvector: '[0.1, 0.2, ...]'
        embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"

        query = """
            UPDATE article_analysis
            SET embedding = CAST($1 AS vector),
                updated_at = NOW()
            WHERE article_id = $2
        """

        async with self.db_pool.acquire() as conn:
            await conn.execute(query, embedding_str, article_id)

        self.stored_in_db += 1

    async def publish_event(self, article: dict, embedding: list[float]):
        """Publish analysis.v3.completed event with embedding."""
        event = {
            "event_type": "analysis.v3.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "article_id": str(article["article_id"]),
                "correlation_id": f"backfill-{article['article_id']}",
                "title": article["title"],
                "embedding": embedding,
                "success": True,
                "pipeline_version": "3.0-backfill",
                "entities": self._parse_json(article.get("entities")),
                "sentiment": self._parse_json(article.get("sentiment")),
                "topics": self._extract_topic_keywords(article.get("topics")),
                "tension_level": float(article["tension_level"]) if article.get("tension_level") else None,
            }
        }

        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await self.exchange.publish(message, routing_key="analysis.v3.completed")

    async def process_single_article(self, article: dict) -> bool:
        """Process a single article. Returns True on success."""
        try:
            title = article["title"] or ""
            content = article["content_preview"] or ""
            embed_text = f"{title}. {content}"

            if self.dry_run:
                self.processed += 1
                return True

            # Generate embedding
            embedding = await self.generate_embedding(embed_text)

            # Store embedding in database (PRIMARY action)
            article_id = str(article["article_id"])
            await self.store_embedding_in_db(article_id, embedding)

            # Optionally publish event for clustering
            if self.publish_events:
                await self.publish_event(article, embedding)

            self.processed += 1
            return True

        except Exception as e:
            logger.error(f"Error processing {article['article_id']}: {e}")
            self.errors += 1
            return False

    async def process_batch(self, articles: list, concurrency: int = 10):
        """Process a batch of articles with parallel requests."""
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(article):
            async with semaphore:
                return await self.process_single_article(article)

        # Process all articles in batch concurrently (limited by semaphore)
        tasks = [process_with_semaphore(article) for article in articles]
        await asyncio.gather(*tasks)

        # Log progress
        if self.processed % 100 < len(articles):
            running_cost = (self.total_tokens / 1_000_000) * self.cost_per_million
            logger.info(
                f"Progress: {self.processed} articles | "
                f"{self.total_tokens:,} tokens | ${running_cost:.4f}"
            )

    async def run(self, days: int = None, batch_size: int = 50, limit: int = None):
        """Run the backfill process.

        Args:
            days: If provided, only process articles from last N days. If None, process ALL.
            batch_size: Number of articles per batch.
            limit: Maximum total articles to process.
        """
        await self.connect()

        try:
            # Get articles
            if days:
                logger.info(f"Fetching articles from last {days} days...")
            else:
                logger.info("Fetching ALL articles without embeddings...")
            articles = await self.get_articles_without_embeddings(days, limit)
            total = len(articles)
            logger.info(f"Found {total} articles to process")

            if total == 0:
                logger.info("No articles to process")
                return

            # Estimate cost
            estimated_tokens = total * 500  # ~500 tokens per article
            estimated_cost = (estimated_tokens / 1_000_000) * 0.02
            logger.info(f"Estimated cost: ${estimated_cost:.4f} ({estimated_tokens:,} tokens)")

            if self.dry_run:
                logger.info("[DRY-RUN] Would process articles without making API calls")

            # Process in batches
            for i in range(0, total, batch_size):
                batch = articles[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
                await self.process_batch(batch)

                # Small delay between batches to avoid rate limits
                if not self.dry_run and i + batch_size < total:
                    await asyncio.sleep(0.5)

            # Summary
            actual_cost = (self.total_tokens / 1_000_000) * self.cost_per_million
            logger.info("=" * 50)
            logger.info("Backfill complete!")
            logger.info(f"  Processed: {self.processed}")
            logger.info(f"  Stored in DB: {self.stored_in_db}")
            logger.info(f"  Events published: {self.processed if self.publish_events else 0}")
            logger.info(f"  Errors: {self.errors}")
            logger.info(f"  Skipped: {self.skipped}")
            logger.info(f"  Total tokens: {self.total_tokens:,}")
            logger.info(f"  Actual cost: ${actual_cost:.4f}")

        finally:
            await self.disconnect()


async def main():
    parser = argparse.ArgumentParser(description="Backfill embeddings for existing articles")
    parser.add_argument("--days", type=int, help="Number of days to backfill (default: 4, ignored if --all)")
    parser.add_argument("--all", action="store_true", help="Process ALL articles without date restriction")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size (default: 50)")
    parser.add_argument("--limit", type=int, help="Limit total articles (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Don't make API calls, just show what would be done")
    parser.add_argument("--no-publish", action="store_true", help="Store in DB only, don't publish events to RabbitMQ")

    args = parser.parse_args()

    # Determine days parameter
    if args.all:
        days = None  # No date restriction
    elif args.days:
        days = args.days
    else:
        days = 4  # Default

    backfiller = EmbeddingBackfiller(dry_run=args.dry_run, publish_events=not args.no_publish)
    await backfiller.run(days=days, batch_size=args.batch_size, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
