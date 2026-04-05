"""
Integration Tests for RabbitMQ Resilience

Tests DLQ, retry logic, and error handling for RabbitMQ consumers.

Task 406: RabbitMQ Resilience Tests
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.workers.rabbitmq_base_consumer import (
    BaseRabbitMQConsumer,
    MessageAction,
    RetryPolicy,
)
from app.workers.article_consumer_v2 import ArticleScrapedConsumer


# =============================================================================
# BaseRabbitMQConsumer Tests
# =============================================================================

class TestConsumer(BaseRabbitMQConsumer):
    """Test consumer implementation"""

    def __init__(self, **kwargs):
        super().__init__(
            rabbitmq_url="amqp://test",
            queue_name="test_queue",
            routing_keys=["test.event"],
            enable_metrics=False,
            **kwargs
        )
        self.processed_messages = []

    async def process_message(self, message_data):
        self.processed_messages.append(message_data)
        return MessageAction.ACK


@pytest.mark.asyncio
async def test_consumer_ack_on_success():
    """Test consumer ACKs message on successful processing"""
    consumer = TestConsumer()

    # Mock message
    mock_message = MagicMock()
    mock_message.body = json.dumps({"payload": {"test": "data"}}).encode()
    mock_message.headers = {}
    mock_message.ack = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should ACK
    mock_message.ack.assert_called_once()
    assert len(consumer.processed_messages) == 1
    assert consumer.processed_messages[0] == {"test": "data"}


@pytest.mark.asyncio
async def test_consumer_reject_on_permanent_error():
    """Test consumer rejects message on permanent error"""

    class RejectingConsumer(BaseRabbitMQConsumer):
        def __init__(self):
            super().__init__(
                rabbitmq_url="amqp://test",
                queue_name="test_queue",
                routing_keys=["test.event"],
                enable_metrics=False,
            )

        async def process_message(self, message_data):
            return MessageAction.REJECT

    consumer = RejectingConsumer()

    # Mock message
    mock_message = MagicMock()
    mock_message.body = json.dumps({"payload": {"test": "data"}}).encode()
    mock_message.headers = {}
    mock_message.reject = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should REJECT (send to DLQ)
    mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_consumer_retry_with_backoff():
    """Test consumer retries message with exponential backoff"""

    class RetryingConsumer(BaseRabbitMQConsumer):
        def __init__(self):
            super().__init__(
                rabbitmq_url="amqp://test",
                queue_name="test_queue",
                routing_keys=["test.event"],
                retry_policy=RetryPolicy(
                    max_retries=3,
                    initial_delay_ms=100,
                    exponential_base=2.0,
                ),
                enable_metrics=False,
            )

        async def process_message(self, message_data):
            return MessageAction.RETRY

    consumer = RetryingConsumer()
    consumer.channel = AsyncMock()
    consumer.channel.default_exchange.publish = AsyncMock()

    # Mock message
    mock_message = MagicMock()
    mock_message.body = json.dumps({"payload": {"test": "data"}}).encode()
    mock_message.headers = {}
    mock_message.ack = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should publish message back to queue with delay
    consumer.channel.default_exchange.publish.assert_called_once()

    # Should ACK original message
    mock_message.ack.assert_called_once()


@pytest.mark.asyncio
async def test_consumer_max_retries_exceeded():
    """Test consumer sends to DLQ after max retries"""

    class RetryingConsumer(BaseRabbitMQConsumer):
        def __init__(self):
            super().__init__(
                rabbitmq_url="amqp://test",
                queue_name="test_queue",
                routing_keys=["test.event"],
                retry_policy=RetryPolicy(max_retries=2),
                enable_metrics=False,
            )

        async def process_message(self, message_data):
            return MessageAction.RETRY

    consumer = RetryingConsumer()

    # Mock message with retry count = 2 (max)
    mock_message = MagicMock()
    mock_message.body = json.dumps({"payload": {"test": "data"}}).encode()
    mock_message.headers = {"x-retry-count": 2}
    mock_message.reject = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should REJECT (send to DLQ) instead of retrying
    mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_consumer_handles_json_decode_error():
    """Test consumer handles malformed JSON"""
    consumer = TestConsumer()

    # Mock message with invalid JSON
    mock_message = MagicMock()
    mock_message.body = b"invalid json {"
    mock_message.headers = {}
    mock_message.reject = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should REJECT (send to DLQ)
    mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_consumer_handles_unexpected_error():
    """Test consumer handles unexpected errors with retry"""

    class ErrorConsumer(BaseRabbitMQConsumer):
        def __init__(self):
            super().__init__(
                rabbitmq_url="amqp://test",
                queue_name="test_queue",
                routing_keys=["test.event"],
                retry_policy=RetryPolicy(max_retries=1),
                enable_metrics=False,
            )

        async def process_message(self, message_data):
            raise RuntimeError("Unexpected error")

    consumer = ErrorConsumer()
    consumer.channel = AsyncMock()
    consumer.channel.default_exchange.publish = AsyncMock()

    # Mock message
    mock_message = MagicMock()
    mock_message.body = json.dumps({"payload": {"test": "data"}}).encode()
    mock_message.headers = {}
    mock_message.ack = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should retry on unexpected error
    consumer.channel.default_exchange.publish.assert_called_once()


# =============================================================================
# ArticleScrapedConsumer Tests
# =============================================================================

@pytest.mark.asyncio
async def test_article_consumer_valid_message():
    """Test ArticleScrapedConsumer processes valid message"""
    consumer = ArticleScrapedConsumer()

    message_data = {
        "article_id": "550e8400-e29b-41d4-a716-446655440000",
        "url": "https://example.com/article",
        "title": "Test Article",
        "content": "Article content",
        "feed_id": "550e8400-e29b-41d4-a716-446655440001",
    }

    # Mock database
    with patch("app.workers.article_consumer_v2.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        # Process message
        action = await consumer.process_message(message_data)

        assert action == MessageAction.ACK
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_article_consumer_missing_required_fields():
    """Test ArticleScrapedConsumer rejects message with missing fields"""
    consumer = ArticleScrapedConsumer()

    message_data = {
        # Missing 'url' and 'title'
        "content": "Article content",
    }

    # Process message
    action = await consumer.process_message(message_data)

    # Should REJECT (permanent error)
    assert action == MessageAction.REJECT


@pytest.mark.asyncio
async def test_article_consumer_invalid_uuid():
    """Test ArticleScrapedConsumer rejects message with invalid UUID"""
    consumer = ArticleScrapedConsumer()

    message_data = {
        "article_id": "not-a-uuid",
        "url": "https://example.com/article",
        "title": "Test Article",
    }

    # Process message
    action = await consumer.process_message(message_data)

    # Should REJECT (permanent error)
    assert action == MessageAction.REJECT


@pytest.mark.asyncio
async def test_article_consumer_duplicate_article():
    """Test ArticleScrapedConsumer handles duplicate articles (idempotent)"""
    from sqlalchemy.exc import IntegrityError

    consumer = ArticleScrapedConsumer()

    message_data = {
        "article_id": "550e8400-e29b-41d4-a716-446655440000",
        "url": "https://example.com/article",
        "title": "Test Article",
    }

    # Mock database to raise IntegrityError (duplicate)
    with patch("app.workers.article_consumer_v2.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_db.return_value.__aenter__.return_value = mock_session

        # Process message
        action = await consumer.process_message(message_data)

        # Should ACK (idempotent - duplicate is expected)
        assert action == MessageAction.ACK


@pytest.mark.asyncio
async def test_article_consumer_database_error_retry():
    """Test ArticleScrapedConsumer retries on transient database errors"""
    consumer = ArticleScrapedConsumer()

    message_data = {
        "article_id": "550e8400-e29b-41d4-a716-446655440000",
        "url": "https://example.com/article",
        "title": "Test Article",
    }

    # Mock database to raise connection error
    with patch("app.workers.article_consumer_v2.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection lost"))
        mock_db.return_value.__aenter__.return_value = mock_session

        # Process message
        action = await consumer.process_message(message_data)

        # Should RETRY (transient error)
        assert action == MessageAction.RETRY


@pytest.mark.asyncio
async def test_article_consumer_generates_uuid():
    """Test ArticleScrapedConsumer generates UUID if missing"""
    consumer = ArticleScrapedConsumer()

    message_data = {
        # No article_id provided
        "url": "https://example.com/article",
        "title": "Test Article",
    }

    # Mock database
    with patch("app.workers.article_consumer_v2.AsyncSessionLocal") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        # Process message
        action = await consumer.process_message(message_data)

        # Should ACK (UUID was generated)
        assert action == MessageAction.ACK


# =============================================================================
# Retry Policy Tests
# =============================================================================

def test_retry_policy_default_values():
    """Test RetryPolicy default values"""
    policy = RetryPolicy()

    assert policy.max_retries == 3
    assert policy.initial_delay_ms == 1000
    assert policy.max_delay_ms == 60000
    assert policy.exponential_base == 2.0
    assert policy.enable_jitter is True


def test_retry_policy_custom_values():
    """Test RetryPolicy custom values"""
    policy = RetryPolicy(
        max_retries=5,
        initial_delay_ms=500,
        max_delay_ms=30000,
        exponential_base=3.0,
        enable_jitter=False,
    )

    assert policy.max_retries == 5
    assert policy.initial_delay_ms == 500
    assert policy.max_delay_ms == 30000
    assert policy.exponential_base == 3.0
    assert policy.enable_jitter is False


# =============================================================================
# Message Action Tests
# =============================================================================

def test_message_action_enum_values():
    """Test MessageAction enum values"""
    assert MessageAction.ACK == "ack"
    assert MessageAction.REJECT == "reject"
    assert MessageAction.RETRY == "retry"
    assert MessageAction.NACK == "nack"


# =============================================================================
# Integration Test with Real RabbitMQ (Optional)
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_with_real_rabbitmq():
    """
    Integration test with real RabbitMQ instance.

    This test requires RabbitMQ to be running on localhost:5672.
    Skip if RabbitMQ is not available.
    """
    pytest.skip("Real RabbitMQ integration test - run manually")

    # This would be implemented for manual integration testing
    # with a real RabbitMQ instance
