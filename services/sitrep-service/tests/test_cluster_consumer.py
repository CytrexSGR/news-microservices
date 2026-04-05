# services/sitrep-service/tests/test_cluster_consumer.py
"""Tests for cluster event consumer."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.events import (
    ClusterCreatedEvent,
    ClusterUpdatedEvent,
    BurstDetectedEvent,
    parse_cluster_event,
)


class TestEventParsing:
    """Test event parsing from RabbitMQ messages."""

    def test_parse_cluster_created_event(self):
        """Test parsing cluster.created event."""
        payload = {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "Breaking News: Market Rally",
                "article_id": str(uuid4()),
                "article_count": 1,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = parse_cluster_event(payload)

        assert isinstance(event, ClusterCreatedEvent)
        assert event.title == "Breaking News: Market Rally"
        assert event.article_count == 1

    def test_parse_cluster_updated_event(self):
        """Test parsing cluster.updated event."""
        payload = {
            "event_type": "cluster.updated",
            "payload": {
                "cluster_id": str(uuid4()),
                "article_id": str(uuid4()),
                "article_count": 5,
                "similarity_score": 0.85,
                "tension_score": 7.5,
                "is_breaking": True,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = parse_cluster_event(payload)

        assert isinstance(event, ClusterUpdatedEvent)
        assert event.article_count == 5
        assert event.is_breaking is True

    def test_parse_burst_detected_event(self):
        """Test parsing cluster.burst_detected event."""
        payload = {
            "event_type": "cluster.burst_detected",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "URGENT: Major Event",
                "article_count": 15,
                "growth_rate": 3.5,
                "tension_score": 9.0,
                "top_entities": ["Entity1", "Entity2"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = parse_cluster_event(payload)

        assert isinstance(event, BurstDetectedEvent)
        assert event.growth_rate == 3.5
        assert "Entity1" in event.top_entities

    def test_parse_unknown_event_returns_none(self):
        """Test that unknown event types return None."""
        payload = {
            "event_type": "unknown.event",
            "payload": {},
        }

        event = parse_cluster_event(payload)

        assert event is None

    def test_parse_event_with_missing_optional_fields(self):
        """Test parsing event with missing optional fields."""
        payload = {
            "event_type": "cluster.updated",
            "payload": {
                "cluster_id": str(uuid4()),
                "article_id": str(uuid4()),
                "article_count": 3,
                "similarity_score": 0.75,
                # Missing: tension_score, is_breaking, primary_entities
            },
        }

        event = parse_cluster_event(payload)

        assert isinstance(event, ClusterUpdatedEvent)
        assert event.tension_score is None
        assert event.is_breaking is False

    def test_parse_event_preserves_uuid(self):
        """Test that UUIDs are properly parsed."""
        cluster_id = str(uuid4())
        article_id = str(uuid4())

        payload = {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": cluster_id,
                "title": "Test Title",
                "article_id": article_id,
                "article_count": 1,
            },
        }

        event = parse_cluster_event(payload)

        assert str(event.cluster_id) == cluster_id
        assert str(event.article_id) == article_id


class TestClusterCreatedEvent:
    """Tests for ClusterCreatedEvent schema."""

    def test_create_valid_event(self):
        """Test creating a valid ClusterCreatedEvent."""
        event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Test Story",
            article_id=uuid4(),
            article_count=1,
        )

        assert event.title == "Test Story"
        assert event.article_count == 1

    def test_default_article_count(self):
        """Test default article_count is 1."""
        event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Test",
            article_id=uuid4(),
        )

        assert event.article_count == 1


class TestClusterUpdatedEvent:
    """Tests for ClusterUpdatedEvent schema."""

    def test_create_valid_event(self):
        """Test creating a valid ClusterUpdatedEvent."""
        event = ClusterUpdatedEvent(
            cluster_id=uuid4(),
            article_id=uuid4(),
            article_count=5,
            similarity_score=0.85,
            tension_score=7.0,
            is_breaking=True,
        )

        assert event.article_count == 5
        assert event.similarity_score == 0.85
        assert event.is_breaking is True

    def test_default_is_breaking(self):
        """Test default is_breaking is False."""
        event = ClusterUpdatedEvent(
            cluster_id=uuid4(),
            article_id=uuid4(),
            article_count=2,
            similarity_score=0.9,
        )

        assert event.is_breaking is False


class TestBurstDetectedEvent:
    """Tests for BurstDetectedEvent schema."""

    def test_create_valid_event(self):
        """Test creating a valid BurstDetectedEvent."""
        event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking: Major Development",
            article_count=20,
            growth_rate=4.5,
            tension_score=9.5,
            top_entities=["Entity1", "Entity2"],
        )

        assert event.growth_rate == 4.5
        assert event.tension_score == 9.5
        assert len(event.top_entities) == 2

    def test_default_detection_method(self):
        """Test default detection_method."""
        event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking",
            article_count=10,
            growth_rate=3.0,
            tension_score=8.0,
        )

        assert event.detection_method == "frequency_spike"

    def test_default_recommended_action(self):
        """Test default recommended_action."""
        event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking",
            article_count=10,
            growth_rate=3.0,
            tension_score=8.0,
        )

        assert event.recommended_action == "immediate_alert"
