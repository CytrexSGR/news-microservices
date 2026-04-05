"""Tests for RabbitMQ event publisher."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.events.publisher import EventPublisher, get_event_publisher


class TestEventPublisher:
    """Tests for EventPublisher class."""

    @pytest.fixture
    def publisher(self):
        """Create a fresh publisher instance."""
        return EventPublisher()

    @pytest.fixture
    def mock_connection(self):
        """Create mock RabbitMQ connection."""
        mock_exchange = MagicMock()
        mock_exchange.publish = AsyncMock()

        mock_channel = MagicMock()
        mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)

        mock_conn = MagicMock()
        mock_conn.is_closed = False
        mock_conn.channel = AsyncMock(return_value=mock_channel)
        mock_conn.close = AsyncMock()

        return mock_conn, mock_channel, mock_exchange

    @pytest.mark.asyncio
    async def test_connect_establishes_connection(self, publisher, mock_connection):
        """Test that connect() establishes RabbitMQ connection."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            await publisher.connect()

            assert publisher._connection == mock_conn
            assert publisher._channel == mock_channel
            assert publisher._exchange == mock_exchange

    @pytest.mark.asyncio
    async def test_connect_skips_if_already_connected(self, publisher, mock_connection):
        """Test that connect() does nothing if already connected."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)) as mock_connect:
            # First connection
            await publisher.connect()
            assert mock_connect.call_count == 1

            # Second call should skip
            await publisher.connect()
            assert mock_connect.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_closes_connection(self, publisher, mock_connection):
        """Test that disconnect() closes the connection."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            await publisher.connect()
            await publisher.disconnect()

            mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_sends_message(self, publisher, mock_connection):
        """Test that publish() sends message to exchange."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            await publisher.connect()

            test_data = {"key": "value"}
            await publisher.publish("test.routing.key", test_data)

            mock_exchange.publish.assert_called_once()
            call_args = mock_exchange.publish.call_args
            message = call_args[0][0]

            # Verify message content
            body = json.loads(message.body.decode())
            assert body == test_data
            assert call_args[1]['routing_key'] == "test.routing.key"

    @pytest.mark.asyncio
    async def test_publish_auto_connects(self, publisher, mock_connection):
        """Test that publish() auto-connects if not connected."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            # Publish without explicit connect
            await publisher.publish("test.key", {"data": "test"})

            # Should have auto-connected
            assert publisher._connection is not None
            mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_articles_fetched(self, publisher, mock_connection):
        """Test publish_articles_fetched() formats event correctly."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            await publisher.connect()

            articles = [
                {"url": "https://example.com/1", "title": "Article 1"},
                {"url": "https://example.com/2", "title": "Article 2"}
            ]

            await publisher.publish_articles_fetched(
                articles=articles,
                source="live",
                query_params={"keywords": "test"}
            )

            mock_exchange.publish.assert_called_once()
            call_args = mock_exchange.publish.call_args
            message = call_args[0][0]
            body = json.loads(message.body.decode())

            assert body["event_type"] == "news.articles.fetched"
            assert body["source"] == "mediastack_live"
            assert body["article_count"] == 2
            assert body["articles"] == articles
            assert body["query_params"] == {"keywords": "test"}
            assert call_args[1]['routing_key'] == "news.articles.fetched"

    @pytest.mark.asyncio
    async def test_publish_urls_discovered(self, publisher, mock_connection):
        """Test publish_urls_discovered() formats event correctly."""
        mock_conn, mock_channel, mock_exchange = mock_connection

        with patch('app.events.publisher.aio_pika.connect_robust',
                   AsyncMock(return_value=mock_conn)):
            await publisher.connect()

            urls = [
                {"url": "https://example.com/1", "title": "Article 1", "source": "cnn"},
                {"url": "https://example.com/2", "title": "Article 2", "source": "bbc"}
            ]

            await publisher.publish_urls_discovered(
                urls=urls,
                batch_id="test-batch-123"
            )

            mock_exchange.publish.assert_called_once()
            call_args = mock_exchange.publish.call_args
            message = call_args[0][0]
            body = json.loads(message.body.decode())

            assert body["event_type"] == "news.urls.discovered"
            assert body["batch_id"] == "test-batch-123"
            assert body["url_count"] == 2
            assert body["urls"] == urls
            assert call_args[1]['routing_key'] == "news.urls.discovered"


class TestGetEventPublisher:
    """Tests for get_event_publisher singleton."""

    def test_returns_same_instance(self):
        """Test that get_event_publisher returns singleton."""
        # Reset the global instance
        import app.events.publisher as publisher_module
        publisher_module._publisher = None

        instance1 = get_event_publisher()
        instance2 = get_event_publisher()

        assert instance1 is instance2

    def test_returns_event_publisher_instance(self):
        """Test that get_event_publisher returns EventPublisher type."""
        import app.events.publisher as publisher_module
        publisher_module._publisher = None

        instance = get_event_publisher()
        assert isinstance(instance, EventPublisher)
