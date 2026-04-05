"""Aggregate and update country statistics."""
import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def update_country_stats(db: AsyncSession, country_code: str) -> None:
    """Update statistics for a single country after new article."""
    try:
        # Use CAST() syntax - asyncpg doesn't handle :: next to named params
        await db.execute(
            text("""
                INSERT INTO country_stats (
                    country_code,
                    article_count_24h,
                    article_count_7d,
                    article_count_30d,
                    last_article_at,
                    last_updated
                )
                SELECT
                    CAST(:code_insert AS varchar(2)),
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days'),
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days'),
                    MAX(created_at),
                    NOW()
                FROM article_locations
                WHERE country_code = CAST(:code_filter AS varchar(2))
                ON CONFLICT (country_code) DO UPDATE SET
                    article_count_24h = EXCLUDED.article_count_24h,
                    article_count_7d = EXCLUDED.article_count_7d,
                    article_count_30d = EXCLUDED.article_count_30d,
                    last_article_at = EXCLUDED.last_article_at,
                    last_updated = NOW()
            """),
            {"code_insert": country_code, "code_filter": country_code},
        )
        logger.debug(f"Updated stats for country {country_code}")
    except Exception as e:
        logger.error(f"Failed to update stats for {country_code}: {e}")


async def refresh_all_stats(db: AsyncSession) -> int:
    """
    Refresh statistics for all countries.

    Returns count of countries updated.
    """
    try:
        result = await db.execute(
            text("""
                WITH stats AS (
                    SELECT
                        country_code,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as cnt_24h,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as cnt_7d,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as cnt_30d,
                        MAX(created_at) as last_at
                    FROM article_locations
                    GROUP BY country_code
                )
                UPDATE country_stats cs SET
                    article_count_24h = COALESCE(s.cnt_24h, 0),
                    article_count_7d = COALESCE(s.cnt_7d, 0),
                    article_count_30d = COALESCE(s.cnt_30d, 0),
                    last_article_at = s.last_at,
                    last_updated = NOW()
                FROM stats s
                WHERE cs.country_code = s.country_code
                RETURNING cs.country_code
            """)
        )
        updated = len(result.fetchall())
        logger.info(f"Refreshed stats for {updated} countries")
        return updated
    except Exception as e:
        logger.error(f"Failed to refresh all stats: {e}")
        return 0


async def get_country_centroid(db: AsyncSession, country_code: str) -> Optional[tuple]:
    """Get country centroid coordinates for broadcasting."""
    result = await db.execute(
        text("""
            SELECT centroid_lat as lat, centroid_lon as lon
            FROM countries
            WHERE iso_code = :country_code AND centroid_lon IS NOT NULL
        """),
        {"country_code": country_code}
    )
    row = result.fetchone()
    if row:
        return (row.lat, row.lon)
    return None
