#!/usr/bin/env python3
"""
Re-queue old articles for scraping.

Publishes scraping jobs to RabbitMQ for articles that were never scraped.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'feed-service'))

from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import FeedItem, Feed
from app.services.event_publisher import EventPublisher

async def requeue_old_articles(limit: int = 1000, dry_run: bool = False):
    """
    Re-queue old articles that were never scraped.

    Args:
        limit: Maximum number of articles to requeue
        dry_run: If True, only print what would be done
    """
    event_publisher = EventPublisher()

    async with AsyncSessionLocal() as session:
        # Find articles that need scraping
        result = await session.execute(
            select(FeedItem, Feed)
            .join(Feed, FeedItem.feed_id == Feed.id)
            .where(
                FeedItem.scrape_status.is_(None),  # Never scraped
                Feed.scrape_full_content == True,   # Feed has scraping enabled
                FeedItem.link.isnot(None)          # Has a valid link
            )
            .order_by(FeedItem.created_at.desc())  # Newest first
            .limit(limit)
        )

        items_to_queue = result.all()

        print(f"\n{'='*60}")
        print(f"Found {len(items_to_queue)} articles to re-queue for scraping")
        print(f"{'='*60}\n")

        if dry_run:
            print("🔍 DRY RUN MODE - No events will be published\n")
            for i, (item, feed) in enumerate(items_to_queue[:10], 1):
                print(f"{i}. {item.title[:60]}...")
                print(f"   Feed: {feed.name}")
                print(f"   URL: {item.link}")
                print(f"   Created: {item.created_at}")
                print()

            if len(items_to_queue) > 10:
                print(f"... and {len(items_to_queue) - 10} more articles\n")

            return

        # Publish events
        queued_count = 0
        failed_count = 0

        for item, feed in items_to_queue:
            try:
                await event_publisher.publish_event(
                    "feed.item.created",
                    {
                        "feed_id": str(feed.id),
                        "item_id": str(item.id),
                        "url": item.link,
                        "scrape_method": feed.scrape_method or "auto",
                    }
                )
                queued_count += 1

                if queued_count % 100 == 0:
                    print(f"✅ Queued {queued_count}/{len(items_to_queue)} articles...")

            except Exception as e:
                print(f"❌ Failed to queue {item.id}: {e}")
                failed_count += 1

        print(f"\n{'='*60}")
        print(f"✅ Successfully queued: {queued_count}")
        if failed_count > 0:
            print(f"❌ Failed to queue: {failed_count}")
        print(f"{'='*60}\n")

async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Re-queue old articles for scraping')
    parser.add_argument('--limit', type=int, default=1000, help='Maximum articles to requeue (default: 1000)')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without actually doing it')
    parser.add_argument('--all', action='store_true', help='Process all pending articles (no limit)')

    args = parser.parse_args()

    limit = None if args.all else args.limit

    await requeue_old_articles(limit=limit or 999999, dry_run=args.dry_run)

if __name__ == "__main__":
    asyncio.run(main())
