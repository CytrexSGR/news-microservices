#!/usr/bin/env python3
"""
Backfill script for geo-processing historical articles.

Reads all analyzed articles from article_analysis table,
extracts LOCATION entities, and creates article_locations mappings.
"""
import asyncio
import logging
import sys
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from app.services.article_locator import process_article_locations
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database connection - use DATABASE_URL from settings
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_unprocessed_articles(db: AsyncSession, batch_size: int = 500, offset: int = 0):
    """Get articles that haven't been geo-processed yet."""
    query = text("""
        SELECT
            aa.article_id,
            aa.tier1_results->'entities' as entities,
            aa.created_at
        FROM article_analysis aa
        LEFT JOIN article_locations al ON aa.article_id = al.article_id
        WHERE aa.success = true
        AND aa.tier1_results IS NOT NULL
        AND al.article_id IS NULL
        ORDER BY aa.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(query, {"limit": batch_size, "offset": offset})
    return result.fetchall()


async def get_total_unprocessed(db: AsyncSession) -> int:
    """Get count of unprocessed articles."""
    query = text("""
        SELECT COUNT(*)
        FROM article_analysis aa
        LEFT JOIN article_locations al ON aa.article_id = al.article_id
        WHERE aa.success = true
        AND aa.tier1_results IS NOT NULL
        AND al.article_id IS NULL
    """)
    result = await db.execute(query)
    return result.scalar() or 0


async def backfill_batch(batch: list, stats: dict) -> None:
    """Process a batch of articles."""
    async with AsyncSessionLocal() as db:
        for row in batch:
            article_id = row.article_id
            entities = row.entities or []

            if not entities:
                stats['skipped_no_entities'] += 1
                continue

            try:
                # Process locations
                mapped_countries = await process_article_locations(db, article_id, entities)

                if mapped_countries:
                    stats['articles_mapped'] += 1
                    stats['locations_created'] += len(mapped_countries)
                else:
                    stats['skipped_no_locations'] += 1

            except Exception as e:
                stats['errors'] += 1
                if stats['errors'] <= 10:  # Only log first 10 errors
                    logger.error(f"Error processing {article_id}: {e}")

        # Commit batch
        await db.commit()


async def main():
    """Main backfill function."""
    logger.info("=" * 60)
    logger.info("Geolocation Backfill Script")
    logger.info("=" * 60)

    stats = {
        'total_processed': 0,
        'articles_mapped': 0,
        'locations_created': 0,
        'skipped_no_entities': 0,
        'skipped_no_locations': 0,
        'errors': 0,
    }

    batch_size = 500
    offset = 0

    async with AsyncSessionLocal() as db:
        total = await get_total_unprocessed(db)

    logger.info(f"Found {total:,} unprocessed articles")

    if total == 0:
        logger.info("Nothing to backfill!")
        return

    start_time = datetime.now()

    while True:
        async with AsyncSessionLocal() as db:
            batch = await get_unprocessed_articles(db, batch_size, 0)  # Always offset 0 since we process and remove

        if not batch:
            break

        await backfill_batch(batch, stats)
        stats['total_processed'] += len(batch)

        # Progress update
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = stats['total_processed'] / elapsed if elapsed > 0 else 0
        remaining = (total - stats['total_processed']) / rate if rate > 0 else 0

        logger.info(
            f"Progress: {stats['total_processed']:,}/{total:,} "
            f"({stats['total_processed']/total*100:.1f}%) | "
            f"Mapped: {stats['articles_mapped']:,} | "
            f"Locations: {stats['locations_created']:,} | "
            f"Rate: {rate:.0f}/s | "
            f"ETA: {remaining/60:.1f}min"
        )

        # Small delay to not overwhelm DB
        await asyncio.sleep(0.1)

    # Final stats
    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info("=" * 60)
    logger.info("Backfill Complete!")
    logger.info("=" * 60)
    logger.info(f"Total processed:      {stats['total_processed']:,}")
    logger.info(f"Articles mapped:      {stats['articles_mapped']:,}")
    logger.info(f"Locations created:    {stats['locations_created']:,}")
    logger.info(f"Skipped (no entities):{stats['skipped_no_entities']:,}")
    logger.info(f"Skipped (no locations):{stats['skipped_no_locations']:,}")
    logger.info(f"Errors:               {stats['errors']:,}")
    logger.info(f"Duration:             {elapsed/60:.1f} minutes")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
