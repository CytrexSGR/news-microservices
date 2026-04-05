#!/usr/bin/env python3
"""
Backfill Script for Unprocessed Articles

Finds articles that haven't been analyzed by content-analysis-v2 pipeline
and creates article.created events in the event_outbox for reprocessing.

Usage:
    python backfill_unprocessed_articles.py --days 7 --batch-size 100 --dry-run
    python backfill_unprocessed_articles.py --days 7 --batch-size 100 --execute
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "news_user",
    "password": "your_db_password",
    "database": "news_mcp",
}


async def get_unprocessed_articles(
    conn: asyncpg.Connection,
    days: int,
    batch_size: int
) -> List[Dict[str, Any]]:
    """
    Get articles that haven't been processed by content-analysis-v2.

    Args:
        conn: Database connection
        days: Number of days to look back
        batch_size: Maximum number of articles to return

    Returns:
        List of unprocessed articles
    """
    query = """
        SELECT
            fi.id,
            fi.feed_id,
            fi.title,
            fi.link,
            fi.created_at,
            LENGTH(fi.content) as content_length
        FROM feed_items fi
        LEFT JOIN content_analysis_v2.pipeline_executions pe
            ON fi.id = pe.article_id AND pe.success = true
        WHERE fi.created_at >= NOW() - INTERVAL '$1 days'
          AND pe.id IS NULL
          AND fi.content IS NOT NULL
          AND LENGTH(fi.content) >= 10
        ORDER BY fi.created_at ASC
        LIMIT $2
    """

    rows = await conn.fetch(query, days, batch_size)

    articles = []
    for row in rows:
        articles.append({
            "id": str(row["id"]),
            "feed_id": str(row["feed_id"]),
            "title": row["title"],
            "link": row["link"],
            "created_at": row["created_at"].isoformat(),
            "content_length": row["content_length"],
        })

    return articles


async def create_outbox_events(
    conn: asyncpg.Connection,
    articles: List[Dict[str, Any]],
    dry_run: bool = True
) -> int:
    """
    Create article.created events in event_outbox for unprocessed articles.

    Args:
        conn: Database connection
        articles: List of articles to create events for
        dry_run: If True, don't actually insert events

    Returns:
        Number of events created
    """
    if dry_run:
        logger.info(f"DRY RUN: Would create {len(articles)} events")
        return 0

    insert_query = """
        INSERT INTO event_outbox (event_type, payload, status, created_at)
        VALUES ($1, $2, 'pending', NOW())
    """

    events_created = 0

    async with conn.transaction():
        for article in articles:
            payload = {
                "item_id": article["id"],
                "feed_id": article["feed_id"],
                "title": article["title"],
                "link": article["link"],
                "has_content": True,
                "backfill": True,  # Mark as backfill for tracking
            }

            await conn.execute(
                insert_query,
                "article.created",
                json.dumps(payload)
            )
            events_created += 1

    logger.info(f"✓ Created {events_created} events in outbox")
    return events_created


async def get_statistics(conn: asyncpg.Connection, days: int) -> Dict[str, int]:
    """
    Get statistics about processed vs unprocessed articles.

    Args:
        conn: Database connection
        days: Number of days to look back

    Returns:
        Dictionary with statistics
    """
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(pe.id) as processed,
            COUNT(*) - COUNT(pe.id) as unprocessed
        FROM feed_items fi
        LEFT JOIN content_analysis_v2.pipeline_executions pe
            ON fi.id = pe.article_id AND pe.success = true
        WHERE fi.created_at >= NOW() - INTERVAL '$1 days'
          AND fi.content IS NOT NULL
          AND LENGTH(fi.content) >= 10
    """

    row = await conn.fetchrow(query, days)

    return {
        "total": row["total"],
        "processed": row["processed"],
        "unprocessed": row["unprocessed"],
    }


async def main():
    """Main backfill execution."""
    parser = argparse.ArgumentParser(
        description="Backfill unprocessed articles for content-analysis-v2"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Maximum number of articles to process (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the backfill (required if not --dry-run)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")

    if args.dry_run and args.execute:
        parser.error("Cannot specify both --dry-run and --execute")

    # Connect to database
    logger.info(f"Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Get statistics
        logger.info(f"Analyzing last {args.days} days...")
        stats = await get_statistics(conn, args.days)

        logger.info(f"Statistics for last {args.days} days:")
        logger.info(f"  Total articles:       {stats['total']}")
        logger.info(f"  Processed:            {stats['processed']}")
        logger.info(f"  Unprocessed:          {stats['unprocessed']}")
        logger.info(f"  Coverage:             {(stats['processed']/stats['total']*100):.1f}%")

        if stats['unprocessed'] == 0:
            logger.info("✓ No unprocessed articles found. Nothing to do.")
            return

        # Get unprocessed articles
        logger.info(f"\nFetching up to {args.batch_size} unprocessed articles...")
        articles = await get_unprocessed_articles(conn, args.days, args.batch_size)

        if not articles:
            logger.info("✓ No unprocessed articles found in this batch.")
            return

        logger.info(f"Found {len(articles)} unprocessed articles")

        # Show sample
        logger.info("\nSample articles:")
        for i, article in enumerate(articles[:5], 1):
            logger.info(
                f"  {i}. [{article['created_at'][:10]}] {article['title'][:60]}... "
                f"({article['content_length']} chars)"
            )

        # Create events
        if args.dry_run:
            logger.info(f"\n{'='*60}")
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info(f"{'='*60}")
            logger.info(f"Would create {len(articles)} article.created events")
        else:
            logger.info(f"\n{'='*60}")
            logger.info("EXECUTING BACKFILL")
            logger.info(f"{'='*60}")

            confirmation = input(f"Create {len(articles)} events in outbox? (yes/no): ")
            if confirmation.lower() != "yes":
                logger.info("Backfill cancelled by user")
                return

            events_created = await create_outbox_events(conn, articles, dry_run=False)

            logger.info(f"\n✓ Backfill complete!")
            logger.info(f"  Events created:     {events_created}")
            logger.info(f"  Processing will begin within ~5 seconds (next outbox run)")

    finally:
        await conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
