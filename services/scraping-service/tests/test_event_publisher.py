"""
Unit tests for EventPublisher service.

Tests connection recovery logic (P1-7).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aio_pika.exceptions import AMQPConnectionError, ChannelClosed

from app.services.event_publisher import EventPublisher


@pytest.fixture
def event_publisher(mock_rabbitmq_connection):
    """Create an EventPublisher instance with mocked dependencies."""
    publisher = EventPublisher()
    publisher.connection = mock_rabbitmq_connection["connection"]
    publisher.channel = mock_rabbitmq_connection["channel"]
    publisher.exchange = mock_rabbitmq_connection["exchange"]
    return publisher


class TestIsConnected:
    """Tests for _is_connected method."""

    def test_is_connected_returns_true_when_all_components_healthy(self, event_publisher):
        """Test that _is_connected returns True when connection is healthy."""
        assert event_publisher._is_connected() is True

    def test_is_connected_returns_false_when_connection_none(self, event_publisher):
        """Test that _is_connected returns False when connection is None."""
        event_publisher.connection = None
        assert event_publisher._is_connected() is False

    def test_is_connected_returns_false_when_connection_closed(self, event_publisher):
        """Test that _is_connected returns False when connection is closed."""
        event_publisher.connection.is_closed = True
        assert event_publisher._is_connected() is False

    def test_is_connected_returns_false_when_channel_closed(self, event_publisher):
        """Test that _is_connected returns False when channel is closed."""
        event_publisher.channel.is_closed = True
        assert event_publisher._is_connected() is False

    def test_is_connected_returns_false_when_exchange_none(self, event_publisher):
        """Test that _is_connected returns False when exchange is None."""
        event_publisher.exchange = None
        assert event_publisher._is_connected() is False


class TestEnsureConnected:
    """Tests for _ensure_connected method."""

    @pytest.mark.asyncio
    async def test_ensure_connected_returns_true_when_already_connected(self, event_publisher):
        """Test that _ensure_connected returns True immediately when connected."""
        result = await event_publisher._ensure_connected()
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_connected_reconnects_when_disconnected(self, event_publisher):
        """Test that _ensure_connected attempts reconnection when disconnected."""
        # Mark as disconnected
        event_publisher.connection = None
        event_publisher.channel = None
        event_publisher.exchange = None

        with patch.object(event_publisher, 'connect', new_callable=AsyncMock) as mock_connect:
            # Simulate successful reconnection
            async def reconnect_side_effect():
                event_publisher.connection = MagicMock(is_closed=False)
                event_publisher.channel = MagicMock(is_closed=False)
                event_publisher.exchange = MagicMock()

            mock_connect.side_effect = reconnect_side_effect

            result = await event_publisher._ensure_connected()

            assert result is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_connected_retries_on_failure(self, event_publisher):
        """Test that _ensure_connected retries with exponential backoff (P1-7)."""
        event_publisher.connection = None
        event_publisher.channel = None
        event_publisher.exchange = None

        attempt_count = 0

        async def failing_connect():
            nonlocal attempt_count
            attempt_count += 1
            raise AMQPConnectionError("Connection refused")

        with patch.object(event_publisher, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = failing_connect

            with patch('app.services.event_publisher.asyncio.sleep', new_callable=AsyncMock):
                result = await event_publisher._ensure_connected()

            assert result is False
            assert attempt_count == 3  # MAX_RECONNECT_ATTEMPTS


class TestPublishEvent:
    """Tests for publish_event method."""

    @pytest.mark.asyncio
    async def test_publish_event_success(self, event_publisher):
        """Test successful event publishing."""
        result = await event_publisher.publish_event(
            event_type="item.scraped",
            payload={"item_id": "123", "url": "https://example.com"},
            correlation_id="corr-123"
        )

        assert result is True
        event_publisher.exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_includes_required_fields(self, event_publisher):
        """Test that published message includes required fields."""
        await event_publisher.publish_event(
            event_type="item.scraped",
            payload={"item_id": "123"}
        )

        call_args = event_publisher.exchange.publish.call_args
        message = call_args[1]["message"] if "message" in call_args[1] else call_args[0][0]

        # Decode and check message body
        import json
        body = json.loads(message.body.decode())

        assert body["event_type"] == "item.scraped"
        assert body["service"] == "scraping-service"
        assert "timestamp" in body
        assert body["payload"]["item_id"] == "123"

    @pytest.mark.asyncio
    async def test_publish_event_returns_false_when_not_connected(self, event_publisher):
        """Test that publish_event returns False when connection unavailable."""
        event_publisher.connection = None
        event_publisher.channel = None
        event_publisher.exchange = None

        with patch.object(event_publisher, '_ensure_connected', new_callable=AsyncMock) as mock_ensure:
            mock_ensure.return_value = False

            result = await event_publisher.publish_event(
                event_type="item.scraped",
                payload={"item_id": "123"}
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_publish_event_retries_on_connection_error(self, event_publisher):
        """Test that publish_event retries on connection error (P1-7)."""
        # First publish fails, reconnection succeeds, retry succeeds
        call_count = 0

        async def publish_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise AMQPConnectionError("Connection lost")
            return None

        event_publisher.exchange.publish = AsyncMock(side_effect=publish_with_failure)

        with patch.object(event_publisher, '_ensure_connected', new_callable=AsyncMock) as mock_ensure:
            mock_ensure.return_value = True

            result = await event_publisher.publish_event(
                event_type="item.scraped",
                payload={"item_id": "123"}
            )

            assert result is True
            assert call_count == 2  # Initial + retry


class TestPublishBatch:
    """Tests for publish_batch method."""

    @pytest.mark.asyncio
    async def test_publish_batch_publishes_all_events(self, event_publisher):
        """Test that publish_batch publishes all events."""
        events = [
            {"event_type": "item.scraped", "payload": {"id": "1"}},
            {"event_type": "item.scraped", "payload": {"id": "2"}},
            {"event_type": "scraping.failed", "payload": {"id": "3"}},
        ]

        count = await event_publisher.publish_batch(events)

        assert count == 3
        assert event_publisher.exchange.publish.call_count == 3

    @pytest.mark.asyncio
    async def test_publish_batch_counts_failures(self, event_publisher):
        """Test that publish_batch counts successful publishes only."""
        call_count = 0

        async def alternate_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Random failure")
            return None

        event_publisher.exchange.publish = AsyncMock(side_effect=alternate_fail)

        events = [
            {"event_type": "e1", "payload": {}},
            {"event_type": "e2", "payload": {}},
            {"event_type": "e3", "payload": {}},
        ]

        count = await event_publisher.publish_batch(events)

        assert count == 2  # First and third succeed
