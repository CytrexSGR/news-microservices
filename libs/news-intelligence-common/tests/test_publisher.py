"""Tests for EventPublisherWrapper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news_intelligence_common.publisher import EventPublisherWrapper, create_event
from news_intelligence_common.event_envelope import EventEnvelope


class TestCreateEvent:
    """Test event creation helper."""

    def test_create_event_minimal(self) -> None:
        """Should create event with minimal args."""
        event = create_event("article.created", {"article_id": "123"})
        assert event.event_type == "article.created"
        assert event.payload == {"article_id": "123"}
        assert event.event_id is not None
        assert len(event.event_id) == 36  # UUID format

    def test_create_event_with_correlation(self) -> None:
        """Should accept correlation_id."""
        event = create_event(
            "article.created",
            {"article_id": "123"},
            correlation_id="corr-456",
        )
        assert event.correlation_id == "corr-456"

    def test_create_event_with_causation(self) -> None:
        """Should accept causation_id."""
        event = create_event(
            "cluster.updated",
            {"cluster_id": "123"},
            correlation_id="corr-123",
            causation_id="cause-789",
        )
        assert event.causation_id == "cause-789"

    def test_create_event_with_metadata(self) -> None:
        """Should accept metadata."""
        event = create_event(
            "article.created",
            {"article_id": "123"},
            metadata={"trace_id": "abc123"},
        )
        assert event.metadata == {"trace_id": "abc123"}

    def test_create_event_returns_event_envelope(self) -> None:
        """Should return EventEnvelope instance."""
        event = create_event("article.created", {"article_id": "123"})
        assert isinstance(event, EventEnvelope)

    def test_create_event_invalid_type_raises(self) -> None:
        """Invalid event type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            create_event("InvalidType", {"data": "test"})


class TestEventPublisherWrapper:
    """Test EventPublisherWrapper class."""

    @pytest.fixture
    def mock_channel(self) -> AsyncMock:
        """Create mock aio_pika channel."""
        channel = AsyncMock()
        exchange = AsyncMock()
        exchange.publish = AsyncMock()
        channel.declare_exchange = AsyncMock(return_value=exchange)
        return channel

    @pytest.mark.asyncio
    async def test_publish_wraps_in_envelope(self, mock_channel: AsyncMock) -> None:
        """Should wrap payload in EventEnvelope."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish("article.created", {"article_id": "123"})

        # Verify publish was called
        mock_channel.declare_exchange.return_value.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_uses_routing_key(self, mock_channel: AsyncMock) -> None:
        """Should use event_type as routing key."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish("cluster.updated", {"cluster_id": "456"})

        call_args = mock_channel.declare_exchange.return_value.publish.call_args
        assert call_args.kwargs["routing_key"] == "cluster.updated"

    @pytest.mark.asyncio
    async def test_publish_returns_event_id(self, mock_channel: AsyncMock) -> None:
        """Should return event_id of published event."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        event_id = await publisher.publish("article.created", {"article_id": "123"})

        assert event_id is not None
        assert len(event_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_publish_validates_event(self, mock_channel: AsyncMock) -> None:
        """Should validate event before publishing when validation enabled."""
        publisher = EventPublisherWrapper(
            mock_channel, "test-service", validate=True
        )
        await publisher.initialize()

        # Invalid event_type should raise
        with pytest.raises(ValueError, match="Invalid event_type"):
            await publisher.publish("InvalidType", {"data": "test"})

    @pytest.mark.asyncio
    async def test_publish_without_validation(self, mock_channel: AsyncMock) -> None:
        """Should not validate when validate=False."""
        publisher = EventPublisherWrapper(
            mock_channel, "test-service", validate=False
        )
        await publisher.initialize()

        # Invalid event_type should raise from EventEnvelope itself
        with pytest.raises(ValueError, match="Invalid event_type"):
            await publisher.publish("InvalidType", {"data": "test"})

    @pytest.mark.asyncio
    async def test_publish_auto_initializes(self, mock_channel: AsyncMock) -> None:
        """Should auto-initialize on first publish if not initialized."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        # Don't call initialize()

        await publisher.publish("article.created", {"article_id": "123"})

        # Exchange should have been declared
        mock_channel.declare_exchange.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_with_correlation_id(self, mock_channel: AsyncMock) -> None:
        """Should pass correlation_id to envelope."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish(
            "article.created",
            {"article_id": "123"},
            correlation_id="my-correlation-id",
        )

        # Verify publish was called (correlation_id is in envelope)
        mock_channel.declare_exchange.return_value.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_with_causation_id(self, mock_channel: AsyncMock) -> None:
        """Should pass causation_id to envelope."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish(
            "article.created",
            {"article_id": "123"},
            correlation_id="corr-id",
            causation_id="cause-id",
        )

        mock_channel.declare_exchange.return_value.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_uses_default_exchange(self, mock_channel: AsyncMock) -> None:
        """Should use news.events exchange by default."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        mock_channel.declare_exchange.assert_called_once()
        call_args = mock_channel.declare_exchange.call_args
        assert call_args.args[0] == "news.events"

    @pytest.mark.asyncio
    async def test_publish_uses_custom_exchange(self, mock_channel: AsyncMock) -> None:
        """Should use custom exchange if provided."""
        publisher = EventPublisherWrapper(
            mock_channel, "test-service", exchange_name="custom.exchange"
        )
        await publisher.initialize()

        call_args = mock_channel.declare_exchange.call_args
        assert call_args.args[0] == "custom.exchange"

    @pytest.mark.asyncio
    async def test_publish_envelope_directly(self, mock_channel: AsyncMock) -> None:
        """Should publish pre-created EventEnvelope."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        envelope = create_event("article.created", {"article_id": "456"})
        event_id = await publisher.publish_envelope(envelope)

        assert event_id == envelope.event_id
        mock_channel.declare_exchange.return_value.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_has_correct_properties(self, mock_channel: AsyncMock) -> None:
        """Should set correct message properties."""
        import json

        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish("article.created", {"article_id": "123"})

        call_args = mock_channel.declare_exchange.return_value.publish.call_args
        message = call_args.args[0]

        # Check message body is JSON
        body = message.body
        data = json.loads(body)
        assert data["event_type"] == "article.created"
        assert data["payload"] == {"article_id": "123"}
        assert "event_id" in data


class TestEventPublisherWrapperEdgeCases:
    """Test edge cases for EventPublisherWrapper."""

    @pytest.fixture
    def mock_channel(self) -> AsyncMock:
        """Create mock aio_pika channel."""
        channel = AsyncMock()
        exchange = AsyncMock()
        exchange.publish = AsyncMock()
        channel.declare_exchange = AsyncMock(return_value=exchange)
        return channel

    @pytest.mark.asyncio
    async def test_multiple_publishes_reuse_exchange(
        self, mock_channel: AsyncMock
    ) -> None:
        """Should not redeclare exchange on multiple publishes."""
        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish("article.created", {"article_id": "1"})
        await publisher.publish("article.created", {"article_id": "2"})
        await publisher.publish("article.created", {"article_id": "3"})

        # Exchange should only be declared once
        assert mock_channel.declare_exchange.call_count == 1
        # But publish should be called 3 times
        assert mock_channel.declare_exchange.return_value.publish.call_count == 3

    @pytest.mark.asyncio
    async def test_publish_with_metadata(self, mock_channel: AsyncMock) -> None:
        """Should include metadata in envelope."""
        import json

        publisher = EventPublisherWrapper(mock_channel, "test-service")
        await publisher.initialize()

        await publisher.publish(
            "article.created",
            {"article_id": "123"},
            metadata={"custom_key": "custom_value"},
        )

        call_args = mock_channel.declare_exchange.return_value.publish.call_args
        message = call_args.args[0]
        data = json.loads(message.body)

        assert data["metadata"] == {"custom_key": "custom_value"}
