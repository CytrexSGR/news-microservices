"""Background job to match new articles against watchlist items.

Runs periodically to check for new security events that match watchlist criteria.
Creates alerts for matches that meet threshold requirements.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertMatcher:
    """Matches new security events against watchlist items."""

    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)
        self.last_check = datetime.utcnow() - timedelta(minutes=5)

    async def run_matching_cycle(self):
        """Run one matching cycle."""
        async with AsyncSession(self.engine) as db:
            # Get active watchlist items
            watchlist_query = text("""
                SELECT id, item_type, item_value, notify_threshold
                FROM security_watchlist
                WHERE notify_on_new = true
            """)
            watchlist_result = await db.execute(watchlist_query)
            watchlist_items = watchlist_result.fetchall()

            if not watchlist_items:
                return 0

            total_alerts = 0
            current_time = datetime.utcnow()

            for item in watchlist_items:
                alerts = await self._match_item(db, item, self.last_check)
                total_alerts += len(alerts)

            self.last_check = current_time
            return total_alerts

    async def _match_item(
        self,
        db: AsyncSession,
        item: Any,
        since: datetime,
    ) -> List[Dict]:
        """Match a single watchlist item against recent articles."""
        item_type = item.item_type
        item_value = item.item_value
        threshold = item.notify_threshold

        # Build match query based on type
        if item_type == "country":
            match_query = text("""
                INSERT INTO security_alerts (watchlist_id, article_id, title, priority_score, threat_level, country_code, matched_value)
                SELECT
                    :watchlist_id,
                    aa.article_id,
                    fi.title,
                    (aa.triage_results->>'priority_score')::int,
                    CASE
                        WHEN (aa.triage_results->>'priority_score')::int >= 9 THEN 'critical'
                        WHEN (aa.triage_results->>'priority_score')::int >= 7 THEN 'high'
                        WHEN (aa.triage_results->>'priority_score')::int >= 5 THEN 'medium'
                        ELSE 'low'
                    END,
                    al.country_code,
                    :matched_value
                FROM article_analysis aa
                JOIN article_locations al ON aa.article_id = al.article_id
                JOIN feed_items fi ON aa.article_id = fi.id
                WHERE al.country_code = :item_value
                  AND (aa.triage_results->>'priority_score')::int >= :threshold
                  AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND aa.created_at > :since
                  AND NOT EXISTS (
                      SELECT 1 FROM security_alerts sa
                      WHERE sa.watchlist_id = :watchlist_id AND sa.article_id = aa.article_id
                  )
                RETURNING id
            """)
        elif item_type == "keyword":
            match_query = text("""
                INSERT INTO security_alerts (watchlist_id, article_id, title, priority_score, threat_level, country_code, matched_value)
                SELECT
                    :watchlist_id,
                    aa.article_id,
                    fi.title,
                    (aa.triage_results->>'priority_score')::int,
                    CASE
                        WHEN (aa.triage_results->>'priority_score')::int >= 9 THEN 'critical'
                        WHEN (aa.triage_results->>'priority_score')::int >= 7 THEN 'high'
                        WHEN (aa.triage_results->>'priority_score')::int >= 5 THEN 'medium'
                        ELSE 'low'
                    END,
                    (SELECT country_code FROM article_locations WHERE article_id = aa.article_id LIMIT 1),
                    :matched_value
                FROM article_analysis aa
                JOIN feed_items fi ON aa.article_id = fi.id
                WHERE (fi.title ILIKE '%' || :item_value || '%' OR fi.content ILIKE '%' || :item_value || '%')
                  AND (aa.triage_results->>'priority_score')::int >= :threshold
                  AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND aa.created_at > :since
                  AND NOT EXISTS (
                      SELECT 1 FROM security_alerts sa
                      WHERE sa.watchlist_id = :watchlist_id AND sa.article_id = aa.article_id
                  )
                RETURNING id
            """)
        elif item_type == "entity":
            match_query = text("""
                INSERT INTO security_alerts (watchlist_id, article_id, title, priority_score, threat_level, country_code, matched_value)
                SELECT
                    :watchlist_id,
                    aa.article_id,
                    fi.title,
                    (aa.triage_results->>'priority_score')::int,
                    CASE
                        WHEN (aa.triage_results->>'priority_score')::int >= 9 THEN 'critical'
                        WHEN (aa.triage_results->>'priority_score')::int >= 7 THEN 'high'
                        WHEN (aa.triage_results->>'priority_score')::int >= 5 THEN 'medium'
                        ELSE 'low'
                    END,
                    (SELECT country_code FROM article_locations WHERE article_id = aa.article_id LIMIT 1),
                    :matched_value
                FROM article_analysis aa
                JOIN feed_items fi ON aa.article_id = fi.id
                WHERE aa.tier1_results->'entities' @> :entity_json::jsonb
                  AND (aa.triage_results->>'priority_score')::int >= :threshold
                  AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND aa.created_at > :since
                  AND NOT EXISTS (
                      SELECT 1 FROM security_alerts sa
                      WHERE sa.watchlist_id = :watchlist_id AND sa.article_id = aa.article_id
                  )
                RETURNING id
            """)
        elif item_type == "region":
            match_query = text("""
                INSERT INTO security_alerts (watchlist_id, article_id, title, priority_score, threat_level, country_code, matched_value)
                SELECT
                    :watchlist_id,
                    aa.article_id,
                    fi.title,
                    (aa.triage_results->>'priority_score')::int,
                    CASE
                        WHEN (aa.triage_results->>'priority_score')::int >= 9 THEN 'critical'
                        WHEN (aa.triage_results->>'priority_score')::int >= 7 THEN 'high'
                        WHEN (aa.triage_results->>'priority_score')::int >= 5 THEN 'medium'
                        ELSE 'low'
                    END,
                    al.country_code,
                    :matched_value
                FROM article_analysis aa
                JOIN article_locations al ON aa.article_id = al.article_id
                JOIN countries c ON al.country_code = c.iso_code
                JOIN feed_items fi ON aa.article_id = fi.id
                WHERE c.region = :item_value
                  AND (aa.triage_results->>'priority_score')::int >= :threshold
                  AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND aa.created_at > :since
                  AND NOT EXISTS (
                      SELECT 1 FROM security_alerts sa
                      WHERE sa.watchlist_id = :watchlist_id AND sa.article_id = aa.article_id
                  )
                RETURNING id
            """)
        else:
            return []

        params = {
            "watchlist_id": str(item.id),
            "item_value": item_value,
            "matched_value": item_value,
            "threshold": threshold,
            "since": since,
        }

        if item_type == "entity":
            params["entity_json"] = f'[{{"name": "{item_value}"}}]'

        try:
            result = await db.execute(match_query, params)
            await db.commit()
            return result.fetchall()
        except Exception as e:
            logger.error(f"Error matching {item_type}={item_value}: {e}")
            await db.rollback()
            return []


async def run_alert_matcher():
    """Main entry point for alert matching job."""
    db_url = settings.DATABASE_URL
    matcher = AlertMatcher(db_url)

    while True:
        try:
            count = await matcher.run_matching_cycle()
            if count > 0:
                logger.info(f"Created {count} new alerts")
        except Exception as e:
            logger.error(f"Alert matching error: {e}")

        await asyncio.sleep(60)  # Run every minute
