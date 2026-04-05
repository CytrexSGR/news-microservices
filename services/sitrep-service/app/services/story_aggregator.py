# services/sitrep-service/app/services/story_aggregator.py
"""Story aggregation service for SITREP generation.

Aggregates cluster events into ranked top stories with category-aware
time-decay relevance scoring. Maintains in-memory cache of active stories
for real-time intelligence briefing generation.

Features:
    - Handles cluster.created, cluster.updated, cluster.burst_detected events
    - Applies category-aware time-decay scoring via RelevanceScorer
    - Category decay rates: breaking_news=0.15, geopolitics=0.03, analysis=0.01
    - Boosts breaking news relevance
    - Provides get_stories() and get_top_stories() for SITREP generation
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from app.constants import CATEGORY_ALIASES
from app.schemas.events import (
    ClusterEvent,
    ClusterCreatedEvent,
    ClusterUpdatedEvent,
    BurstDetectedEvent,
)
from app.schemas.story import TopStory
from app.services.relevance_scorer import RelevanceScorer

logger = logging.getLogger(__name__)


class StoryAggregator:
    """
    Aggregates cluster events into ranked top stories.

    Maintains an in-memory cache of active stories keyed by cluster_id
    and applies category-aware time-decay scoring for relevance ranking.

    Category Decay Rates:
        - breaking_news: 0.15 (~5h half-life) - Very fast decay
        - geopolitics: 0.03 (~24h half-life) - Slow decay
        - analysis: 0.01 (~70h half-life) - Very slow decay
        - markets: 0.08 (~9h half-life) - Medium decay
        - technology: 0.05 (~14h half-life) - Standard decay
        - default: 0.05 (~14h half-life) - Fallback

    Attributes:
        _stories: Dict mapping cluster_id (UUID) to TopStory
        _scorer: RelevanceScorer instance for category-aware relevance calculation

    Example:
        >>> aggregator = StoryAggregator()
        >>> await aggregator.handle_event(cluster_created_event)
        >>> stories = await aggregator.get_top_stories(limit=10)
    """

    # Breaking news boost multiplier (applied after composite score)
    BREAKING_BOOST = 1.5

    def __init__(self):
        """
        Initialize the story aggregator.

        Creates a RelevanceScorer with category-aware decay rates.
        """
        self._stories: Dict[UUID, TopStory] = {}
        self._scorer = RelevanceScorer()
        self._events_received: int = 0

    async def handle_event(self, event: ClusterEvent) -> None:
        """
        Handle incoming cluster event.

        Dispatches to appropriate handler based on event type.
        Maintains state between calls for story aggregation.

        Args:
            event: Parsed cluster event (ClusterCreatedEvent,
                   ClusterUpdatedEvent, or BurstDetectedEvent)
        """
        self._events_received += 1

        if isinstance(event, ClusterCreatedEvent):
            await self._handle_created(event)
        elif isinstance(event, ClusterUpdatedEvent):
            await self._handle_updated(event)
        elif isinstance(event, BurstDetectedEvent):
            await self._handle_burst(event)
        else:
            logger.warning(f"Unknown event type: {type(event)}")

    async def _handle_created(self, event: ClusterCreatedEvent) -> None:
        """
        Handle cluster.created event - add new story.

        Creates a new TopStory from the cluster creation event.

        Args:
            event: ClusterCreatedEvent with cluster details
        """
        now = event.timestamp or datetime.now(timezone.utc)

        story = TopStory(
            cluster_id=event.cluster_id,
            title=event.title,
            article_count=event.article_count,
            first_seen_at=now,
            last_updated_at=now,
            tension_score=0.0,
            relevance_score=1.0,  # New stories start with high relevance
            is_breaking=False,
            category=event.category,
            top_entities=[],
        )

        self._stories[event.cluster_id] = story
        logger.debug(
            f"Added story: {event.title} (cluster_id={event.cluster_id}, "
            f"category={event.category})"
        )

    async def _handle_updated(self, event: ClusterUpdatedEvent) -> None:
        """
        Handle cluster.updated event - update existing story.

        Updates story metrics. Creates story if not exists (late join scenario).

        Args:
            event: ClusterUpdatedEvent with updated metrics
        """
        story = self._stories.get(event.cluster_id)
        now = datetime.now(timezone.utc)

        if story is None:
            # Create story if not exists (late join)
            story = TopStory(
                cluster_id=event.cluster_id,
                title=f"Cluster {event.cluster_id}",  # Placeholder title
                article_count=event.article_count,
                first_seen_at=now,
                last_updated_at=now,
                tension_score=event.tension_score or 0.0,
                is_breaking=event.is_breaking,
                category=event.category,
            )
            self._stories[event.cluster_id] = story
            logger.debug(
                f"Created story from update (late join): {event.cluster_id}, "
                f"category={event.category}"
            )
        else:
            # Update existing story
            story.article_count = event.article_count
            story.last_updated_at = now
            story.is_breaking = event.is_breaking

            # Update category if provided and different
            if event.category != "default" and event.category != story.category:
                story.category = event.category

            if event.tension_score is not None:
                story.tension_score = event.tension_score

            if event.primary_entities:
                # Extract entity names from entity dicts
                story.top_entities = [
                    e.get("name", str(e)) for e in event.primary_entities[:5]
                ]

        logger.debug(
            f"Updated story: cluster_id={event.cluster_id}, "
            f"articles={story.article_count}, category={story.category}"
        )

    async def _handle_burst(self, event: BurstDetectedEvent) -> None:
        """
        Handle cluster.burst_detected event - mark as breaking.

        Creates or updates story with breaking news status and metrics.
        Breaking news uses "breaking_news" category for fast decay.

        Args:
            event: BurstDetectedEvent with burst detection details
        """
        story = self._stories.get(event.cluster_id)
        now = event.timestamp or datetime.now(timezone.utc)

        if story is None:
            # Create breaking story
            story = TopStory(
                cluster_id=event.cluster_id,
                title=event.title,
                article_count=event.article_count,
                first_seen_at=now,
                last_updated_at=now,
                tension_score=event.tension_score,
                is_breaking=True,
                category=event.category,  # Usually "breaking_news"
                growth_rate=event.growth_rate,
                top_entities=event.top_entities or [],
            )
            self._stories[event.cluster_id] = story
            logger.info(
                f"Breaking news story created: {event.title} "
                f"(category={event.category})"
            )
        else:
            # Update existing story as breaking
            story.title = event.title
            story.article_count = event.article_count
            story.tension_score = event.tension_score
            story.is_breaking = True
            story.category = event.category  # Override to breaking_news
            story.growth_rate = event.growth_rate
            story.last_updated_at = now

            if event.top_entities:
                story.top_entities = event.top_entities

            logger.info(
                f"Story upgraded to breaking: {event.title} "
                f"(category={story.category})"
            )

    async def get_stories(self) -> List[TopStory]:
        """
        Get all tracked stories.

        Returns:
            List of all TopStory objects (unranked)
        """
        return list(self._stories.values())

    async def get_top_stories(
        self,
        limit: int = 10,
        min_article_count: int = 1,
        max_age_hours: Optional[int] = None,
        category: Optional[str] = None,
        is_breaking_only: bool = False,
    ) -> List[TopStory]:
        """
        Get top stories sorted by category-aware time-decayed relevance.

        Calculates composite relevance score for each story using:
        - Category-aware time-decayed base score (40%)
        - Tension score component (30%)
        - Article count component (20%)
        - Breaking news boost (10%)

        Breaking news stories get an additional 1.5x multiplier.

        Args:
            limit: Maximum number of stories to return
            min_article_count: Minimum articles required in cluster
            max_age_hours: Maximum age in hours (None = no limit)
            category: Filter by category (None = all categories)
            is_breaking_only: If True, only return breaking news stories

        Returns:
            List of TopStory sorted by relevance_score descending
        """
        now = datetime.now(timezone.utc)
        stories = []

        for story in self._stories.values():
            # Filter by minimum article count
            if story.article_count < min_article_count:
                continue

            # Filter by max age
            if max_age_hours is not None:
                age_hours = (now - story.first_seen_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    continue

            # Filter by category (map cluster category to SITREP category)
            if category is not None:
                mapped_category = CATEGORY_ALIASES.get(story.category, story.category)
                if mapped_category != category:
                    continue

            # Filter breaking only
            if is_breaking_only and not story.is_breaking:
                continue

            # Calculate category-aware composite relevance score
            story.relevance_score = self._calculate_relevance(story, now)
            stories.append(story)

        # Sort by relevance descending
        stories.sort(key=lambda s: s.relevance_score, reverse=True)

        return stories[:limit]

    def _calculate_relevance(self, story: TopStory, now: datetime) -> float:
        """
        Calculate category-aware composite relevance score for a story.

        Uses RelevanceScorer to apply category-specific decay rates:
        - breaking_news: 0.15 (fast decay, ~5h half-life)
        - geopolitics: 0.03 (slow decay, ~24h half-life)
        - analysis: 0.01 (very slow decay, ~70h half-life)
        - default: 0.05 (standard news decay, ~14h half-life)

        Args:
            story: TopStory to calculate relevance for
            now: Current timestamp for time decay

        Returns:
            Relevance score between 0 and 1
        """
        # Use RelevanceScorer for category-aware composite scoring
        composite = self._scorer.calculate_composite_score(
            base_score=1.0,
            published_at=story.first_seen_at,
            tension_score=story.tension_score,
            article_count=story.article_count,
            is_breaking=story.is_breaking,
            category=story.category,
            now=now,
        )

        # Apply additional breaking news multiplier
        if story.is_breaking:
            composite = min(1.0, composite * self.BREAKING_BOOST)

        return min(1.0, composite)

    async def clear(self) -> None:
        """Clear all tracked stories."""
        self._stories.clear()
        logger.info("Story aggregator cache cleared")

    @property
    def story_count(self) -> int:
        """Get number of tracked stories."""
        return len(self._stories)

    @property
    def events_received(self) -> int:
        """Get count of events received."""
        return self._events_received
