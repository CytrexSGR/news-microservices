#!/usr/bin/env python3
"""
Batch calculation script for Feed Quality V2 scores.

This script calculates comprehensive quality scores for all active feeds
and updates the database with the results.

Usage:
    python scripts/calculate_all_quality.py [--days 30] [--feed-id UUID] [--dry-run]

Examples:
    # Calculate for all active feeds
    python scripts/calculate_all_quality.py

    # Calculate for specific time window
    python scripts/calculate_all_quality.py --days 7

    # Calculate for single feed (testing)
    python scripts/calculate_all_quality.py --feed-id 330b60c7-1f19-4aab-a0d6-a3b3a207a07d

    # Dry run (no database updates)
    python scripts/calculate_all_quality.py --dry-run
"""
import asyncio
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.feed import Feed
from app.services.feed_quality_v2 import FeedQualityScorerV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_decimals_to_float(obj):
    """
    Recursively convert Decimal objects to float for JSON serialization.

    Args:
        obj: Object to convert (dict, list, Decimal, or other)

    Returns:
        Object with all Decimals converted to float
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    else:
        return obj


async def calculate_feed_quality(
    session: AsyncSession,
    feed: Feed,
    scorer: FeedQualityScorerV2,
    days: int = 30,
    dry_run: bool = False
) -> dict:
    """
    Calculate quality score for a single feed.

    Args:
        session: Database session
        feed: Feed model instance
        scorer: Quality scorer instance
        days: Number of days to analyze
        dry_run: If True, skip database updates

    Returns:
        Dict with calculation results and status
    """
    try:
        logger.info(f"Calculating quality for feed: {feed.name} ({feed.id})")

        # Calculate comprehensive quality
        quality_data = await scorer.calculate_comprehensive_quality(
            session=session,
            feed_id=feed.id,
            days=days
        )

        if not dry_run:
            # Update feed record with quality data
            feed.quality_score_v2 = int(quality_data['quality_score'])
            feed.quality_confidence = quality_data['confidence']
            feed.quality_trend = quality_data['trend']
            feed.quality_calculated_at = datetime.now(timezone.utc)
            # Convert Decimals to float for JSON serialization
            feed.article_quality_stats = convert_decimals_to_float({
                'component_scores': quality_data['component_scores'],
                'quality_distribution': quality_data['quality_distribution'],
                'red_flags': quality_data['red_flags'],
                'trends': {
                    'trend_label': quality_data['trends']['trend_label'],
                    'trend_value': quality_data['trends']['trend_value'],
                    'quality_7d_vs_30d': quality_data['trends']['quality_7d_vs_30d']
                },
                'data_stats': {
                    'articles_analyzed': quality_data['data_stats']['articles_analyzed'],
                    'total_articles': quality_data['data_stats']['total_articles'],
                    'coverage_percentage': quality_data['data_stats']['coverage_percentage']
                }
            })

            # Explicitly add feed to session and flush changes
            session.add(feed)
            await session.flush()
            await session.commit()
            logger.info(f"✅ Updated {feed.name}: Score={quality_data['quality_score']:.1f}, "
                       f"Code={quality_data['admiralty_code']['code']}, "
                       f"Confidence={quality_data['confidence']}")
        else:
            logger.info(f"🔍 DRY RUN - Would update {feed.name}: "
                       f"Score={quality_data['quality_score']:.1f}, "
                       f"Code={quality_data['admiralty_code']['code']}, "
                       f"Confidence={quality_data['confidence']}")

        return {
            'feed_id': str(feed.id),
            'feed_name': feed.name,
            'status': 'success',
            'quality_score': quality_data['quality_score'],
            'admiralty_code': quality_data['admiralty_code']['code'],
            'confidence': quality_data['confidence'],
            'trend': quality_data['trend'],
            'articles_analyzed': quality_data['data_stats']['articles_analyzed']
        }

    except Exception as e:
        logger.error(f"❌ Failed to calculate quality for {feed.name}: {e}", exc_info=True)
        return {
            'feed_id': str(feed.id),
            'feed_name': feed.name,
            'status': 'error',
            'error': str(e)
        }


async def calculate_all_feeds_quality(
    feed_id: UUID | None = None,
    days: int = 30,
    dry_run: bool = False
) -> dict:
    """
    Calculate quality scores for all active feeds (or single feed if specified).

    Args:
        feed_id: Optional specific feed ID to process
        days: Number of days to analyze
        dry_run: If True, skip database updates

    Returns:
        Dict with summary statistics
    """
    async with AsyncSessionLocal() as session:
        scorer = FeedQualityScorerV2()

        # Build query
        query = select(Feed).where(Feed.is_active == True)
        if feed_id:
            query = query.where(Feed.id == feed_id)

        result = await session.execute(query)
        feeds = result.scalars().all()

        if not feeds:
            if feed_id:
                logger.error(f"Feed {feed_id} not found or inactive")
                return {'error': 'Feed not found'}
            else:
                logger.warning("No active feeds found")
                return {'total': 0, 'successful': 0, 'failed': 0}

        logger.info(f"Processing {len(feeds)} feed(s) with {days}-day window")

        results = []
        for feed in feeds:
            result = await calculate_feed_quality(
                session=session,
                feed=feed,
                scorer=scorer,
                days=days,
                dry_run=dry_run
            )
            results.append(result)

        # Calculate summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')

        summary = {
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'dry_run': dry_run,
            'results': results
        }

        # Log summary
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH CALCULATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total feeds processed: {summary['total']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Dry run: {dry_run}")

        if successful > 0:
            # Quality distribution summary
            scores = [r['quality_score'] for r in results if r['status'] == 'success']
            avg_score = sum(scores) / len(scores)
            logger.info(f"\nAverage Quality Score: {avg_score:.1f}")

            # Admiralty Code distribution
            codes = {}
            for r in results:
                if r['status'] == 'success':
                    code = r.get('admiralty_code', 'Unknown')
                    codes[code] = codes.get(code, 0) + 1

            logger.info("\nAdmiralty Code Distribution:")
            for code in ['A', 'B', 'C', 'D', 'E', 'F']:
                count = codes.get(code, 0)
                if count > 0:
                    logger.info(f"  {code}: {count} feeds")

        logger.info(f"{'='*60}\n")

        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate Feed Quality V2 scores for all active feeds',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )
    parser.add_argument(
        '--feed-id',
        type=str,
        help='Calculate for specific feed only (UUID)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate but do not update database'
    )

    args = parser.parse_args()

    # Validate feed_id if provided
    feed_id = None
    if args.feed_id:
        try:
            feed_id = UUID(args.feed_id)
        except ValueError:
            logger.error(f"Invalid feed ID format: {args.feed_id}")
            sys.exit(1)

    # Run batch calculation
    try:
        summary = asyncio.run(calculate_all_feeds_quality(
            feed_id=feed_id,
            days=args.days,
            dry_run=args.dry_run
        ))

        if summary.get('error'):
            logger.error(f"Error: {summary['error']}")
            sys.exit(1)

        if summary['failed'] > 0:
            logger.warning(f"Completed with {summary['failed']} failures")
            sys.exit(1)

        logger.info("✅ Batch calculation completed successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
