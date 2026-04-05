#!/usr/bin/env python3
"""
Re-analyze articles that are missing analysis.

This script finds articles without analysis entries and creates
article.created events in the outbox. The outbox processor will
then publish them to RabbitMQ for analysis.

Usage:
    python scripts/reanalyze_missing_articles.py [--date YYYY-MM-DD] [--limit N] [--dry-run]
"""

import asyncio
import argparse
from datetime import datetime, date
from typing import List
import uuid

import asyncpg


async def get_missing_articles(
    conn: asyncpg.Connection,
    target_date: date = None,
    limit: int = None
) -> List[dict]:
    """
    Find articles without analysis entries.

    Args:
        conn: Database connection
        target_date: Filter articles by date (default: today)
        limit: Maximum number of articles to return

    Returns:
        List of article records (id, title, link, created_at)
    """
    if target_date is None:
        target_date = date.today()

    query = """
        SELECT
            fi.id,
            fi.title,
            fi.link,
            fi.feed_id,
            fi.created_at
        FROM feed_items fi
        LEFT JOIN article_analysis aa ON fi.id = aa.article_id
        LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id
        WHERE fi.created_at::date = $1
          AND aa.id IS NULL
          AND pe.id IS NULL
        ORDER BY fi.created_at
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = await conn.fetch(query, target_date)

    return [dict(row) for row in rows]


async def create_outbox_events(
    conn: asyncpg.Connection,
    articles: List[dict],
    dry_run: bool = False
) -> int:
    """
    Create article.created events in outbox for re-analysis.

    Args:
        conn: Database connection
        articles: List of article records
        dry_run: If True, don't actually insert events

    Returns:
        Number of events created
    """
    if dry_run:
        print(f"[DRY RUN] Would create {len(articles)} events")
        return len(articles)

    inserted = 0

    # Insert events in batches for better performance
    batch_size = 100

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]

        # Prepare batch insert
        values = []
        for article in batch:
            event_id = str(uuid.uuid4())
            correlation_id = str(uuid.uuid4())

            payload = {
                "article_id": str(article['id']),
                "feed_id": str(article['feed_id']),
                "title": article['title'],
                "link": article['link'],
                "timestamp": article['created_at'].isoformat(),
            }

            values.append((
                event_id,
                'article.created',
                payload,
                'pending',
                correlation_id,
            ))

        # Insert batch
        await conn.executemany(
            """
            INSERT INTO event_outbox
                (id, event_type, payload, status, correlation_id, created_at)
            VALUES
                ($1, $2, $3::jsonb, $4, $5, NOW())
            ON CONFLICT DO NOTHING
            """,
            values
        )

        inserted += len(batch)
        print(f"  ✓ Inserted batch {i//batch_size + 1}: {len(batch)} events")

    return inserted


async def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Re-analyze articles missing analysis"
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date (YYYY-MM-DD), default: today'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of articles to process'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    # Parse target date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()

    print("=" * 80)
    print("RE-ANALYZE MISSING ARTICLES")
    print("=" * 80)
    print(f"Target date: {target_date}")
    print(f"Limit: {args.limit or 'None (all articles)'}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='news_user',
        password='your_db_password',
        database='news_mcp'
    )

    try:
        # Find articles without analysis
        print("Step 1: Finding articles without analysis...")
        articles = await get_missing_articles(conn, target_date, args.limit)
        print(f"  ✓ Found {len(articles)} articles without analysis")

        if len(articles) == 0:
            print("\n✓ No articles need re-analysis. All done!")
            return

        # Show sample
        print("\nSample articles (first 3):")
        for article in articles[:3]:
            print(f"  - {article['title'][:60]}... (created: {article['created_at']})")

        if not args.dry_run:
            print("\nStep 2: Creating outbox events...")
            inserted = await create_outbox_events(conn, articles, args.dry_run)
            print(f"  ✓ Created {inserted} events in outbox")

            print("\nStep 3: Verification...")
            pending_count = await conn.fetchval(
                "SELECT COUNT(*) FROM event_outbox WHERE status = 'pending'"
            )
            print(f"  ✓ Total pending events in outbox: {pending_count}")

            print("\n" + "=" * 80)
            print("✅ RE-ANALYSIS QUEUED SUCCESSFULLY")
            print("=" * 80)
            print(f"\n{inserted} articles queued for analysis")
            print(f"The outbox processor will publish them within 5 seconds")
            print(f"Content-analysis workers will then process them")
            print(f"\nMonitor progress:")
            print(f"  - Outbox: docker exec postgres psql -U news_user -d news_mcp -c \"SELECT status, COUNT(*) FROM event_outbox GROUP BY status\"")
            print(f"  - Analysis: docker logs news-microservices-content-analysis-v2-1 --tail 100 -f")
        else:
            print("\n[DRY RUN] No changes made. Run without --dry-run to create events.")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
