# services/sitrep-service/app/schemas/events.py
"""Event schemas for cluster events.

Defines Pydantic models for parsing incoming cluster events from RabbitMQ.
These events are published by the clustering-service and consumed by sitrep-service
to aggregate top stories for intelligence briefings.

Events:
    - cluster.created: New cluster created from first article
    - cluster.updated: Article added to existing cluster
    - cluster.burst_detected: Breaking news detected (rapid growth)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class ClusterCreatedEvent(BaseModel):
    """
    Event emitted when a new cluster is created.

    Published when the clustering-service creates a new cluster from
    the first article that doesn't match any existing cluster.

    Attributes:
        cluster_id: UUID of the new cluster
        title: Cluster title (from first article's headline)
        article_id: UUID of the first article in the cluster
        article_count: Always 1 for new clusters
        category: Content category for decay rate selection
            Valid categories: breaking_news, geopolitics, analysis,
            markets, technology. Defaults to "default".
        timestamp: Event timestamp (optional, from envelope)
    """

    cluster_id: UUID
    title: str
    article_id: UUID
    article_count: int = 1
    category: str = "default"
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClusterUpdatedEvent(BaseModel):
    """
    Event emitted when an article is added to an existing cluster.

    Published when a new article matches an existing cluster based
    on semantic similarity scoring.

    Attributes:
        cluster_id: UUID of the updated cluster
        article_id: UUID of the newly added article
        article_count: Total articles in cluster after update
        similarity_score: Cosine similarity score for the match (0-1)
        tension_score: Story tension/importance score (0-10)
        is_breaking: Whether cluster is now classified as breaking news
        category: Content category for decay rate selection
            Valid categories: breaking_news, geopolitics, analysis,
            markets, technology. Defaults to "default".
        primary_entities: Top entities extracted from cluster articles
        timestamp: Event timestamp (optional, from envelope)
    """

    cluster_id: UUID
    article_id: UUID
    article_count: int
    similarity_score: float
    tension_score: Optional[float] = None
    is_breaking: bool = False
    category: str = "default"
    primary_entities: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BurstDetectedEvent(BaseModel):
    """
    Event emitted when breaking news is detected.

    Published when a cluster shows rapid article growth (frequency spike)
    indicating breaking news that may require immediate attention.

    Attributes:
        cluster_id: UUID of the cluster
        title: Cluster headline/title
        article_count: Current number of articles in cluster
        growth_rate: Growth rate multiplier (articles / threshold)
        tension_score: Story tension/importance score (0-10)
        top_entities: List of top entity names in the cluster
        category: Original content category (before burst detection).
            Note: Burst events automatically use "breaking_news" decay rate.
        detection_method: How the burst was detected (default: frequency_spike)
        recommended_action: Suggested downstream action
        timestamp: Event timestamp (optional, from envelope)
    """

    cluster_id: UUID
    title: str
    article_count: int
    growth_rate: float
    tension_score: float
    top_entities: Optional[List[str]] = None
    category: str = "breaking_news"  # Burst events default to breaking_news
    detection_method: str = "frequency_spike"
    recommended_action: str = "immediate_alert"
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Union type for all cluster events
ClusterEvent = Union[ClusterCreatedEvent, ClusterUpdatedEvent, BurstDetectedEvent]


def parse_cluster_event(message: Dict[str, Any]) -> Optional[ClusterEvent]:
    """
    Parse a RabbitMQ message into a typed cluster event.

    Parses the event envelope format used by clustering-service:
    {
        "event_type": "cluster.created",
        "payload": {...},
        "timestamp": "2026-01-05T10:00:00Z",
        ...
    }

    Args:
        message: Raw message dict from RabbitMQ

    Returns:
        Typed event object (ClusterCreatedEvent, ClusterUpdatedEvent,
        or BurstDetectedEvent), or None if unknown event type

    Example:
        >>> msg = {"event_type": "cluster.created", "payload": {...}}
        >>> event = parse_cluster_event(msg)
        >>> if isinstance(event, ClusterCreatedEvent):
        ...     print(f"New cluster: {event.title}")
    """
    event_type = message.get("event_type", "")
    payload = message.get("payload", {})
    timestamp = message.get("timestamp")

    # Add timestamp to payload if present in envelope
    if timestamp:
        payload["timestamp"] = timestamp

    # Map event types to parser classes
    parsers = {
        "cluster.created": ClusterCreatedEvent,
        "cluster.updated": ClusterUpdatedEvent,
        "cluster.burst_detected": BurstDetectedEvent,
    }

    parser = parsers.get(event_type)
    if parser is None:
        return None

    return parser(**payload)
