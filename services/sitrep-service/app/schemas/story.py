# services/sitrep-service/app/schemas/story.py
"""Schemas for aggregated stories.

Defines Pydantic models for stories aggregated from cluster events.
Stories are the primary unit of intelligence for SITREP reports.

Models:
    - TopStory: Individual story aggregated from cluster data
    - StorySummary: Collection of stories for SITREP generation
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TopStory(BaseModel):
    """
    Represents an aggregated top story from cluster data.

    A TopStory is created from cluster events and maintains metrics
    for time-decay relevance ranking. Stories are keyed by cluster_id
    to enable updates from multiple events.

    Attributes:
        cluster_id: UUID of the source cluster
        title: Story headline from cluster title
        summary: Optional AI-generated summary
        article_count: Number of articles in cluster
        first_seen_at: When the story was first detected
        last_updated_at: Most recent update timestamp
        tension_score: Story importance/urgency score (0-10)
        relevance_score: Time-decay weighted relevance (0-1)
        is_breaking: Whether this is breaking news
        category: Content category for decay rate selection.
            Valid categories: breaking_news, geopolitics, analysis,
            markets, technology. Defaults to "default".
        top_entities: Key entities mentioned in the story
        growth_rate: Article growth rate (for burst detection)

    Example:
        >>> story = TopStory(
        ...     cluster_id=uuid4(),
        ...     title="Market Rally Continues",
        ...     article_count=15,
        ...     first_seen_at=datetime.now(timezone.utc),
        ...     last_updated_at=datetime.now(timezone.utc),
        ...     tension_score=7.5,
        ...     relevance_score=0.85,
        ...     category="markets",
        ... )
    """

    cluster_id: UUID
    title: str
    summary: Optional[str] = None
    article_count: int = 1
    first_seen_at: datetime
    last_updated_at: datetime
    tension_score: float = 0.0
    relevance_score: float = 0.0
    is_breaking: bool = False
    category: str = "default"
    top_entities: List[str] = Field(default_factory=list)
    growth_rate: Optional[float] = None

    model_config = {"from_attributes": True}


class StorySummary(BaseModel):
    """
    Summary of top stories for SITREP generation.

    Provides a snapshot of aggregated stories with metadata
    for LLM prompt generation.

    Attributes:
        stories: Ranked list of TopStory objects
        total_clusters: Total number of clusters tracked
        breaking_count: Number of breaking news stories
        time_range_hours: Lookback period for stories
        generated_at: When this summary was created

    Example:
        >>> summary = StorySummary(
        ...     stories=[story1, story2],
        ...     total_clusters=50,
        ...     breaking_count=2,
        ... )
    """

    stories: List[TopStory]
    total_clusters: int
    breaking_count: int
    time_range_hours: int = 24
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"from_attributes": True}
