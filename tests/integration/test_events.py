"""
Integration tests for RabbitMQ event system
Tests event publishing, consumption, and end-to-end flows
"""

import asyncio
import json
import os
import pytest
from datetime import datetime
from uuid import uuid4

# Add shared directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from event_publisher import EventPublisher, get_event_publisher
from event_consumer import MultiEventConsumer, create_consumer
from event_integration import (
    EventTypes,
    QueueNames,
    FeedServiceEvents,
    ContentAnalysisServiceEvents,
    ResearchServiceEvents,
    OSINTServiceEvents,
    NotificationServiceEvents,
)


# Test configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:rabbit_secret_2024@localhost:5672/news_mcp")
TEST_TIMEOUT = 10  # seconds


@pytest.fixture
async def event_publisher():
    """Create event publisher for tests"""
    publisher = EventPublisher(
        rabbitmq_url=RABBITMQ_URL,
        exchange_name="news.events",
        service_name="test-service",
    )
    await publisher.initialize()
    yield publisher
    await publisher.close()


@pytest.fixture
async def test_queue_consumer():
    """Create test consumer"""
    consumer = MultiEventConsumer(
        rabbitmq_url=RABBITMQ_URL,
        queue_name="test.queue",
        routing_keys=["#"],  # Subscribe to all events
        exchange_name="news.events",
        service_name="test-consumer",
    )
    await consumer.initialize()
    yield consumer
    await consumer.close()


class TestEventPublishing:
    """Test event publishing functionality"""

    @pytest.mark.asyncio
    async def test_publish_article_created(self, event_publisher):
        """Test publishing article.created event"""
        result = await event_publisher.publish(
            event_type=EventTypes.ARTICLE_CREATED,
            data={
                "article_id": str(uuid4()),
                "feed_id": str(uuid4()),
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "Test content",
                "published_at": datetime.utcnow().isoformat(),
            },
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_analysis_completed(self, event_publisher):
        """Test publishing analysis.completed event"""
        result = await event_publisher.publish(
            event_type=EventTypes.ANALYSIS_COMPLETED,
            data={
                "article_id": str(uuid4()),
                "analysis_id": str(uuid4()),
                "sentiment": {"score": 0.8, "label": "positive"},
                "entities": [{"text": "OpenAI", "type": "ORG"}],
                "topics": ["AI", "Technology"],
                "keywords": ["artificial intelligence", "machine learning"],
                "summary": "Test summary",
                "language": "en",
                "processing_time_ms": 1234,
            },
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_batch(self, event_publisher):
        """Test batch publishing"""
        events = [
            (EventTypes.ARTICLE_CREATED, {
                "article_id": str(uuid4()),
                "feed_id": str(uuid4()),
                "title": f"Article {i}",
                "url": f"https://example.com/article-{i}",
                "content": f"Content {i}",
            })
            for i in range(5)
        ]

        success_count = await event_publisher.publish_batch(events)
        assert success_count == 5

    @pytest.mark.asyncio
    async def test_publish_with_correlation_id(self, event_publisher):
        """Test publishing with correlation ID"""
        correlation_id = str(uuid4())
        result = await event_publisher.publish(
            event_type=EventTypes.ARTICLE_CREATED,
            data={
                "article_id": str(uuid4()),
                "feed_id": str(uuid4()),
                "title": "Test",
                "url": "https://example.com",
                "content": "Test",
            },
            correlation_id=correlation_id,
        )
        assert result is True


class TestEventConsumption:
    """Test event consumption functionality"""

    @pytest.mark.asyncio
    async def test_consume_article_created(self, event_publisher):
        """Test consuming article.created event"""
        received_events = []

        async def handle_article_created(event):
            received_events.append(event)

        # Create consumer
        consumer = await create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            queue_name="test.content-analysis.articles",
            routing_keys=["article.created"],
            handlers={
                EventTypes.ARTICLE_CREATED: handle_article_created,
            },
            service_name="test-content-analysis",
        )

        # Start consuming
        await consumer.start_consuming()

        # Publish event
        article_id = str(uuid4())
        await event_publisher.publish(
            event_type=EventTypes.ARTICLE_CREATED,
            data={
                "article_id": article_id,
                "feed_id": str(uuid4()),
                "title": "Test Article",
                "url": "https://example.com/article",
                "content": "Test content",
            },
        )

        # Wait for event to be consumed
        await asyncio.sleep(2)

        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]["event_type"] == EventTypes.ARTICLE_CREATED
        assert received_events[0]["data"]["article_id"] == article_id

        await consumer.close()

    @pytest.mark.asyncio
    async def test_multiple_event_types(self, event_publisher):
        """Test consuming multiple event types"""
        received_events = {}

        async def handle_article_created(event):
            received_events["article"] = event

        async def handle_article_updated(event):
            received_events["update"] = event

        # Create consumer
        consumer = await create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            queue_name="test.search.articles",
            routing_keys=["article.created", "article.updated"],
            handlers={
                EventTypes.ARTICLE_CREATED: handle_article_created,
                EventTypes.ARTICLE_UPDATED: handle_article_updated,
            },
            service_name="test-search",
        )

        await consumer.start_consuming()

        # Publish events
        article_id = str(uuid4())
        await event_publisher.publish(
            EventTypes.ARTICLE_CREATED,
            {"article_id": article_id, "feed_id": str(uuid4()), "title": "Test", "url": "https://example.com", "content": "Test"},
        )
        await event_publisher.publish(
            EventTypes.ARTICLE_UPDATED,
            {"article_id": article_id, "feed_id": str(uuid4()), "changes": {"title": "Updated"}, "updated_at": datetime.utcnow().isoformat()},
        )

        await asyncio.sleep(2)

        assert "article" in received_events
        assert "update" in received_events

        await consumer.close()


class TestServiceIntegration:
    """Test service-specific integration helpers"""

    @pytest.mark.asyncio
    async def test_feed_service_publish(self):
        """Test Feed Service event publishing"""
        publisher = FeedServiceEvents.get_publisher(RABBITMQ_URL)
        await publisher.initialize()

        result = await FeedServiceEvents.publish_article_created(
            publisher=publisher,
            article_id=str(uuid4()),
            feed_id=str(uuid4()),
            title="Test Article",
            url="https://example.com/article",
            content="Test content",
            author="Test Author",
            published_at=datetime.utcnow().isoformat(),
        )

        assert result is True
        await publisher.close()

    @pytest.mark.asyncio
    async def test_content_analysis_integration(self):
        """Test Content Analysis Service integration"""
        # Publisher
        publisher = ContentAnalysisServiceEvents.get_publisher(RABBITMQ_URL)
        await publisher.initialize()

        result = await ContentAnalysisServiceEvents.publish_analysis_completed(
            publisher=publisher,
            article_id=str(uuid4()),
            analysis_id=str(uuid4()),
            sentiment={"score": 0.8, "label": "positive"},
            entities=[],
            topics=["AI"],
            keywords=["test"],
            summary="Test summary",
            language="en",
            processing_time_ms=1000,
        )

        assert result is True
        await publisher.close()


class TestEndToEndFlow:
    """Test complete event flow through multiple services"""

    @pytest.mark.asyncio
    async def test_article_to_notification_flow(self):
        """
        Test complete flow:
        1. Feed Service publishes article.created
        2. Content Analysis consumes and publishes analysis.completed
        3. OSINT consumes and publishes alert.triggered
        4. Notification consumes and publishes notification.sent
        """
        flow_events = {}

        # Simulate Content Analysis Service
        async def handle_article_created(event):
            flow_events["article_created"] = event
            # Simulate analysis
            publisher = ContentAnalysisServiceEvents.get_publisher(RABBITMQ_URL)
            await publisher.initialize()
            await ContentAnalysisServiceEvents.publish_analysis_completed(
                publisher=publisher,
                article_id=event["data"]["article_id"],
                analysis_id=str(uuid4()),
                sentiment={"score": 0.9, "label": "positive"},
                entities=[],
                topics=["Test"],
                keywords=["test"],
                summary="Test",
                language="en",
                processing_time_ms=500,
            )
            await publisher.close()

        # Simulate OSINT Service
        async def handle_analysis_completed(event):
            flow_events["analysis_completed"] = event
            # Simulate alert detection
            publisher = OSINTServiceEvents.get_publisher(RABBITMQ_URL)
            await publisher.initialize()
            await OSINTServiceEvents.publish_alert_triggered(
                publisher=publisher,
                alert_id=str(uuid4()),
                alert_type="anomaly",
                severity="high",
                title="Test Alert",
                description="Test alert description",
                indicators=["test"],
                confidence_score=0.85,
                recommended_actions=["investigate"],
            )
            await publisher.close()

        # Simulate Notification Service
        async def handle_alert_triggered(event):
            flow_events["alert_triggered"] = event

        # Set up consumers
        content_consumer = await ContentAnalysisServiceEvents.create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            handlers={EventTypes.ARTICLE_CREATED: handle_article_created},
        )
        await content_consumer.start_consuming()

        osint_consumer = await OSINTServiceEvents.create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            handlers={EventTypes.ANALYSIS_COMPLETED: handle_analysis_completed},
        )
        await osint_consumer.start_consuming()

        notification_consumer = await NotificationServiceEvents.create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            handlers={EventTypes.ALERT_TRIGGERED: handle_alert_triggered},
        )
        await notification_consumer.start_consuming()

        # Publish initial event
        publisher = FeedServiceEvents.get_publisher(RABBITMQ_URL)
        await publisher.initialize()
        await FeedServiceEvents.publish_article_created(
            publisher=publisher,
            article_id=str(uuid4()),
            feed_id=str(uuid4()),
            title="Breaking News",
            url="https://example.com/news",
            content="Important news content",
            published_at=datetime.utcnow().isoformat(),
        )
        await publisher.close()

        # Wait for flow to complete
        await asyncio.sleep(5)

        # Verify all events were triggered
        assert "article_created" in flow_events
        assert "analysis_completed" in flow_events
        assert "alert_triggered" in flow_events

        # Cleanup
        await content_consumer.close()
        await osint_consumer.close()
        await notification_consumer.close()


class TestErrorHandling:
    """Test error handling and dead-letter queue"""

    @pytest.mark.asyncio
    async def test_invalid_event_structure(self, event_publisher):
        """Test publishing event with invalid structure"""
        # This should fail validation
        result = await event_publisher.publish(
            event_type="invalid.event",
            data="not a dict",  # Invalid: should be dict
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_handler_exception(self, event_publisher):
        """Test consumer handling exceptions gracefully"""
        async def failing_handler(event):
            raise Exception("Simulated handler error")

        consumer = await create_consumer(
            rabbitmq_url=RABBITMQ_URL,
            queue_name="test.failing.queue",
            routing_keys=["article.created"],
            handlers={EventTypes.ARTICLE_CREATED: failing_handler},
            service_name="test-failing",
        )

        await consumer.start_consuming()

        # Publish event (should not crash consumer)
        await event_publisher.publish(
            EventTypes.ARTICLE_CREATED,
            {"article_id": str(uuid4()), "feed_id": str(uuid4()), "title": "Test", "url": "https://example.com", "content": "Test"},
        )

        await asyncio.sleep(2)
        await consumer.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
