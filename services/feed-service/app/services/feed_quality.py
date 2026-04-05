"""
Feed quality scoring service

Calculates quality scores based on various metrics.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedItem, FetchLog, FeedHealth

logger = logging.getLogger(__name__)


class FeedQualityScorer:
    """Service for calculating feed quality scores."""

    async def calculate_quality_score(
        self, session: AsyncSession, feed_id: int
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality score for a feed.

        Quality factors:
        1. Freshness - How recent are the articles
        2. Consistency - How regular is the publishing schedule
        3. Content Quality - Article length, completeness
        4. Reliability - Success rate, uptime

        Returns:
            Dictionary with quality scores and recommendations
        """
        # Get feed and related data
        result = await session.execute(select(Feed).where(Feed.id == feed_id))
        feed = result.scalar_one_or_none()

        if not feed:
            raise ValueError(f"Feed {feed_id} not found")

        # Calculate individual scores
        freshness_score = await self._calculate_freshness_score(session, feed_id)
        consistency_score = await self._calculate_consistency_score(session, feed_id)
        content_score = await self._calculate_content_score(session, feed_id)
        reliability_score = await self._calculate_reliability_score(session, feed_id)

        # Calculate overall quality score (weighted average)
        quality_score = (
            freshness_score * 0.3 +
            consistency_score * 0.2 +
            content_score * 0.2 +
            reliability_score * 0.3
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            freshness_score,
            consistency_score,
            content_score,
            reliability_score,
            feed
        )

        return {
            "feed_id": feed_id,
            "quality_score": round(quality_score, 2),
            "freshness_score": round(freshness_score, 2),
            "consistency_score": round(consistency_score, 2),
            "content_score": round(content_score, 2),
            "reliability_score": round(reliability_score, 2),
            "recommendations": recommendations,
            "calculated_at": datetime.now(timezone.utc),
        }

    async def _calculate_freshness_score(
        self, session: AsyncSession, feed_id: int
    ) -> float:
        """
        Calculate freshness score based on article recency.

        Score 0-100:
        - 100: Articles published within last hour
        - 80: Articles within last 24 hours
        - 60: Articles within last week
        - 40: Articles within last month
        - 20: Articles older than a month
        - 0: No articles or all very old
        """
        now = datetime.now(timezone.utc)

        # Get most recent article
        result = await session.execute(
            select(FeedItem.published_at)
            .where(FeedItem.feed_id == feed_id)
            .order_by(FeedItem.published_at.desc())
            .limit(1)
        )
        latest_article = result.scalar_one_or_none()

        if not latest_article:
            return 0.0

        # Ensure timezone-aware
        if latest_article.tzinfo is None:
            latest_article = latest_article.replace(tzinfo=timezone.utc)

        age = now - latest_article

        if age < timedelta(hours=1):
            return 100.0
        elif age < timedelta(days=1):
            return 80.0
        elif age < timedelta(days=7):
            return 60.0
        elif age < timedelta(days=30):
            return 40.0
        elif age < timedelta(days=90):
            return 20.0
        else:
            return 0.0

    async def _calculate_consistency_score(
        self, session: AsyncSession, feed_id: int
    ) -> float:
        """
        Calculate consistency score based on publishing regularity.

        Analyzes the standard deviation of time between articles.
        Lower deviation = more consistent = higher score.
        """
        # Get recent articles (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        result = await session.execute(
            select(FeedItem.published_at)
            .where(
                and_(
                    FeedItem.feed_id == feed_id,
                    FeedItem.published_at >= thirty_days_ago
                )
            )
            .order_by(FeedItem.published_at)
        )
        publish_times = [row[0] for row in result.all()]

        if len(publish_times) < 2:
            return 50.0  # Not enough data, return neutral score

        # Calculate time deltas between consecutive articles
        deltas = []
        for i in range(1, len(publish_times)):
            # Ensure timezone-aware
            time1 = publish_times[i-1]
            time2 = publish_times[i]
            if time1.tzinfo is None:
                time1 = time1.replace(tzinfo=timezone.utc)
            if time2.tzinfo is None:
                time2 = time2.replace(tzinfo=timezone.utc)

            delta_hours = (time2 - time1).total_seconds() / 3600
            deltas.append(delta_hours)

        if not deltas:
            return 50.0

        # Calculate mean and standard deviation
        import statistics
        mean_delta = statistics.mean(deltas)

        if len(deltas) > 1:
            std_dev = statistics.stdev(deltas)
            # Calculate coefficient of variation (CV)
            cv = (std_dev / mean_delta) * 100 if mean_delta > 0 else 100
        else:
            cv = 0

        # Convert CV to score (lower CV = higher score)
        if cv < 20:
            return 100.0
        elif cv < 40:
            return 80.0
        elif cv < 60:
            return 60.0
        elif cv < 80:
            return 40.0
        elif cv < 100:
            return 20.0
        else:
            return 10.0

    async def _calculate_content_score(
        self, session: AsyncSession, feed_id: int
    ) -> float:
        """
        Calculate content quality score.

        Based on:
        - Average article length
        - Presence of description/content
        - Successful content scraping (if enabled)
        """
        # Get recent articles
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        result = await session.execute(
            select(FeedItem)
            .where(
                and_(
                    FeedItem.feed_id == feed_id,
                    FeedItem.created_at >= seven_days_ago
                )
            )
            .limit(100)
        )
        items = result.scalars().all()

        if not items:
            return 50.0  # No recent data

        scores = []
        for item in items:
            item_score = 0

            # Title quality (max 30 points)
            if item.title:
                title_length = len(item.title)
                if title_length > 20:
                    item_score += 30
                elif title_length > 10:
                    item_score += 20
                else:
                    item_score += 10

            # Description quality (max 30 points)
            if item.description:
                desc_length = len(item.description)
                if desc_length > 100:
                    item_score += 30
                elif desc_length > 50:
                    item_score += 20
                else:
                    item_score += 10

            # Content quality (max 40 points)
            if item.content:
                content_length = len(item.content)
                if content_length > 500:
                    item_score += 40
                elif content_length > 200:
                    item_score += 25
                else:
                    item_score += 10
            elif item.scrape_status == "success" and item.scrape_word_count:
                # If content was scraped successfully
                if item.scrape_word_count > 300:
                    item_score += 40
                elif item.scrape_word_count > 100:
                    item_score += 25
                else:
                    item_score += 10

            scores.append(item_score)

        return sum(scores) / len(scores) if scores else 0.0

    async def _calculate_reliability_score(
        self, session: AsyncSession, feed_id: int
    ) -> float:
        """
        Calculate reliability score based on fetch success rate and uptime.
        """
        # Get health record
        result = await session.execute(
            select(FeedHealth).where(FeedHealth.feed_id == feed_id)
        )
        health = result.scalar_one_or_none()

        if not health:
            # No health data, check recent fetch logs
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            result = await session.execute(
                select(FetchLog.status)
                .where(
                    and_(
                        FetchLog.feed_id == feed_id,
                        FetchLog.started_at >= seven_days_ago
                    )
                )
            )
            fetch_logs = result.all()

            if not fetch_logs:
                return 50.0  # No data

            success_count = sum(1 for log in fetch_logs if log[0] == "success")
            success_rate = success_count / len(fetch_logs) if fetch_logs else 0

            return success_rate * 100

        # Use health metrics
        reliability = (
            health.success_rate * 0.4 +
            health.uptime_24h * 0.2 +
            health.uptime_7d * 0.2 +
            health.uptime_30d * 0.2
        )

        # Penalize for consecutive failures
        if health.consecutive_failures > 0:
            penalty = min(health.consecutive_failures * 5, 30)
            reliability = max(0, reliability * 100 - penalty)
        else:
            reliability = reliability * 100

        return reliability

    def _generate_recommendations(
        self,
        freshness_score: float,
        consistency_score: float,
        content_score: float,
        reliability_score: float,
        feed: Feed,
    ) -> List[str]:
        """Generate recommendations based on scores."""
        recommendations = []

        # Freshness recommendations
        if freshness_score < 40:
            recommendations.append(
                "Feed appears to be inactive or updating very slowly. "
                "Consider checking if the feed URL is still valid."
            )
        elif freshness_score < 60:
            recommendations.append(
                "Feed updates are infrequent. You might want to reduce the fetch interval."
            )

        # Consistency recommendations
        if consistency_score < 40:
            recommendations.append(
                "Feed has irregular publishing schedule. "
                "Consider adjusting fetch interval to match actual publishing pattern."
            )

        # Content recommendations
        if content_score < 40:
            if not feed.scrape_full_content:
                recommendations.append(
                    "Feed provides limited content. "
                    "Consider enabling full content scraping for better article quality."
                )
            else:
                recommendations.append(
                    "Content quality is low even with scraping enabled. "
                    "The source might have anti-scraping measures."
                )

        # Reliability recommendations
        if reliability_score < 60:
            if feed.consecutive_failures > 3:
                recommendations.append(
                    f"Feed has {feed.consecutive_failures} consecutive failures. "
                    "Check if the feed URL is correct or if the server is experiencing issues."
                )
            else:
                recommendations.append(
                    "Feed reliability is low. Consider implementing retry logic "
                    "or checking network connectivity."
                )

        # Fetch interval recommendations
        if feed.fetch_interval < 30 and freshness_score > 80:
            recommendations.append(
                "Feed is very active. Current fetch interval might be too aggressive."
            )
        elif feed.fetch_interval > 120 and freshness_score < 40:
            recommendations.append(
                "Feed is rarely updated. Consider increasing fetch interval to save resources."
            )

        if not recommendations:
            recommendations.append("Feed is performing well. No immediate actions needed.")

        return recommendations