#!/usr/bin/env python3
"""
Backfill V3 Analysis Results to Neo4j Knowledge Graph

Migrates existing V3 analysis results (Tier0, Tier1, Tier2) from PostgreSQL
to Neo4j knowledge graph.

Usage:
    python scripts/backfill_graph.py [--dry-run] [--limit N] [--start-from ID]

Options:
    --dry-run: Preview changes without writing to Neo4j
    --limit N: Process only first N articles
    --start-from ID: Start from specific article ID (for resuming)

Example:
    # Preview first 10 articles
    python scripts/backfill_graph.py --dry-run --limit 10

    # Backfill all articles
    python scripts/backfill_graph.py

    # Resume from specific article
    python scripts/backfill_graph.py --start-from abc-123
"""

import asyncio
import asyncpg
import sys
import argparse
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.graph_client import V3GraphClient
from app.core.config import settings


async def fetch_articles_for_backfill(
    pool: asyncpg.Pool,
    limit: Optional[int] = None,
    start_from: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch articles that have V3 analysis but not in graph.

    Args:
        pool: Database connection pool
        limit: Maximum number of articles to process
        start_from: Start from this article ID (for resuming)

    Returns:
        List of article IDs with V3 analysis
    """
    query = """
    SELECT DISTINCT t0.article_id
    FROM triage_decisions t0
    ORDER BY t0.created_at ASC
    """

    if limit:
        query += f" LIMIT {limit}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)

    return [{"article_id": str(row["article_id"])} for row in rows]


async def fetch_tier0_data(
    pool: asyncpg.Pool,
    article_id: str
) -> Optional[Dict[str, Any]]:
    """Fetch Tier0 triage decision for article."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM triage_decisions WHERE article_id = $1",
            UUID(article_id)
        )

    if not row:
        return None

    return {
        "PriorityScore": row["priority_score"],
        "category": row["category"],
        "keep": row["keep"],
        "tokens_used": row["tokens_used"],
        "cost_usd": row["cost_usd"]
    }


async def fetch_tier1_data(
    pool: asyncpg.Pool,
    article_id: str
) -> Optional[Dict[str, Any]]:
    """Fetch Tier1 foundation extraction for article."""
    async with pool.acquire() as conn:
        # Check if Tier1 exists
        scores = await conn.fetchrow(
            "SELECT * FROM tier1_scores WHERE article_id = $1",
            UUID(article_id)
        )

        if not scores:
            return None

        # Fetch entities
        entities = await conn.fetch(
            "SELECT * FROM tier1_entities WHERE article_id = $1",
            UUID(article_id)
        )

        # Fetch relations
        relations = await conn.fetch(
            "SELECT * FROM tier1_relations WHERE article_id = $1",
            UUID(article_id)
        )

        # Fetch topics
        topics = await conn.fetch(
            "SELECT * FROM tier1_topics WHERE article_id = $1",
            UUID(article_id)
        )

    return {
        "entities": [
            {
                "name": e["entity_name"],
                "type": e["entity_type"],
                "relevance": e.get("relevance", 0.0)
            }
            for e in entities
        ],
        "relations": [
            {
                "source": r["source_entity"],
                "target": r["target_entity"],
                "type": r["relation_type"],
                "confidence": r.get("confidence", 0.0)
            }
            for r in relations
        ],
        "topics": [t["topic"] for t in topics]
    }


async def backfill_article(
    pool: asyncpg.Pool,
    graph_client: V3GraphClient,
    article_id: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Backfill single article to graph.

    Args:
        pool: Database connection pool
        graph_client: Neo4j graph client
        article_id: Article UUID
        dry_run: If True, don't write to Neo4j

    Returns:
        Dict with backfill results
    """
    result = {
        "article_id": article_id,
        "tier0_published": False,
        "tier1_published": False,
        "tier2_published": False,
        "errors": []
    }

    try:
        # Fetch Tier0 data
        tier0_data = await fetch_tier0_data(pool, article_id)
        if not tier0_data:
            result["errors"].append("No Tier0 data found")
            return result

        # Publish Tier0 to graph
        if not dry_run:
            try:
                await graph_client.create_article_node(
                    article_id=article_id,
                    tier0_data=tier0_data,
                    article_metadata={}
                )
                result["tier0_published"] = True
            except Exception as e:
                result["errors"].append(f"Tier0 publish failed: {e}")
                return result  # Stop if Tier0 fails
        else:
            result["tier0_published"] = True  # Dry run success

        # Fetch Tier1 data (if article kept)
        if tier0_data.get("keep"):
            tier1_data = await fetch_tier1_data(pool, article_id)
            if tier1_data:
                # Publish Tier1 to graph
                if not dry_run:
                    try:
                        await graph_client.publish_tier1(
                            article_id=article_id,
                            tier1_data=tier1_data
                        )
                        result["tier1_published"] = True
                    except Exception as e:
                        result["errors"].append(f"Tier1 publish failed: {e}")
                else:
                    result["tier1_published"] = True  # Dry run success

        # TODO: Tier2 backfill (when specialist data extraction is implemented)

    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")

    return result


async def main():
    """Main backfill execution."""
    parser = argparse.ArgumentParser(description="Backfill V3 analyses to Neo4j")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--limit", type=int, help="Process only first N articles")
    parser.add_argument("--start-from", type=str, help="Start from article ID")
    args = parser.parse_args()

    print("=" * 80)
    print("V3 → Neo4j Backfill Script")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Limit: {args.limit or 'None (all articles)'}")
    print(f"Start from: {args.start_from or 'Beginning'}")
    print("=" * 80)

    # Initialize database pool
    print("\n[1/5] Connecting to PostgreSQL...")
    pool = await asyncpg.create_pool(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    print("✓ PostgreSQL connected")

    # Initialize graph client
    print("\n[2/5] Connecting to Neo4j...")
    graph_client = V3GraphClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )

    try:
        await graph_client.connect()
        print("✓ Neo4j connected")
    except Exception as e:
        print(f"✗ Neo4j connection failed: {e}")
        await pool.close()
        return

    # Fetch articles to backfill
    print("\n[3/5] Fetching articles for backfill...")
    articles = await fetch_articles_for_backfill(
        pool,
        limit=args.limit,
        start_from=args.start_from
    )
    print(f"✓ Found {len(articles)} articles to backfill")

    # Backfill articles
    print(f"\n[4/5] {'Previewing' if args.dry_run else 'Backfilling'} articles...")
    success_count = 0
    error_count = 0

    for i, article in enumerate(articles, 1):
        article_id = article["article_id"]
        print(f"\n[{i}/{len(articles)}] Processing {article_id}...")

        result = await backfill_article(
            pool,
            graph_client,
            article_id,
            dry_run=args.dry_run
        )

        if result["errors"]:
            print(f"  ✗ Errors: {', '.join(result['errors'])}")
            error_count += 1
        else:
            print(f"  ✓ Success:")
            print(f"    - Tier0: {'✓' if result['tier0_published'] else '✗'}")
            print(f"    - Tier1: {'✓' if result['tier1_published'] else '✗'}")
            print(f"    - Tier2: {'✓' if result['tier2_published'] else '✗'}")
            success_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("Backfill Summary")
    print("=" * 80)
    print(f"Total articles: {len(articles)}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No data was written to Neo4j")
        print("Run without --dry-run to perform actual backfill")

    # Cleanup
    print("\n[5/5] Cleaning up...")
    await graph_client.disconnect()
    await pool.close()
    print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
