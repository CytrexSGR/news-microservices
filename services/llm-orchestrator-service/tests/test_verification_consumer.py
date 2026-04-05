"""
Tests for Verification Consumer (RabbitMQ)

Coverage:
- RabbitMQ connection
- Message handling
- Error scenarios
- Planner/Verifier integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from app.services.verification_consumer import VerificationConsumer, get_consumer


class TestVerificationConsumerInitialization:
    """Test VerificationConsumer initialization."""

    def test_initialization(self):
        """Test consumer initializes with planner and verifier."""
        consumer = VerificationConsumer()

        assert consumer.connection is None  # Not connected yet
        assert consumer.channel is None
        assert consumer.exchange is None
        assert consumer.queue is None
        assert consumer.planner is not None
        assert consumer.verifier is not None


class TestRabbitMQConnection:
    """Test RabbitMQ connection setup."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_rabbitmq_connection, mock_settings):
        """Test successful RabbitMQ connection."""
        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(return_value=mock_rabbitmq_connection["connection"])):

                consumer = VerificationConsumer()
                await consumer.connect()

                assert consumer.connection is not None
                assert consumer.channel is not None
                assert consumer.exchange is not None
                assert consumer.queue is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_settings):
        """Test handling of connection failures."""
        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(side_effect=Exception("Connection failed"))):

                consumer = VerificationConsumer()

                with pytest.raises(Exception, match="Connection failed"):
                    await consumer.connect()

    @pytest.mark.asyncio
    async def test_connect_declares_exchange(self, mock_rabbitmq_connection, mock_settings):
        """Test that connect declares the exchange with correct config."""
        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(return_value=mock_rabbitmq_connection["connection"])):

                consumer = VerificationConsumer()
                await consumer.connect()

                # Verify exchange was declared
                mock_rabbitmq_connection["channel"].declare_exchange.assert_called_once()
                call_args = mock_rabbitmq_connection["channel"].declare_exchange.call_args
                assert call_args[0][0] == "verification_exchange"

    @pytest.mark.asyncio
    async def test_connect_declares_queue_with_dlx(self, mock_rabbitmq_connection, mock_settings):
        """Test that queue is declared with dead letter exchange."""
        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(return_value=mock_rabbitmq_connection["connection"])):

                consumer = VerificationConsumer()
                await consumer.connect()

                # Verify queue was declared with DLX
                mock_rabbitmq_connection["channel"].declare_queue.assert_called_once()
                call_args = mock_rabbitmq_connection["channel"].declare_queue.call_args
                assert call_args[0][0] == "verification_queue"
                assert "arguments" in call_args[1]
                assert "x-dead-letter-exchange" in call_args[1]["arguments"]


class TestMessageHandling:
    """Test handling of incoming messages."""

    @pytest.mark.asyncio
    async def test_handle_message_success(
        self,
        mock_rabbitmq_message,
        sample_verification_event,
        sample_problem_hypothesis,
        sample_verification_plan,
        sample_tool_execution_result
    ):
        """Test successful message handling."""
        consumer = VerificationConsumer()

        # Mock planner to return hypothesis and plan
        consumer.planner.process_verification_request = AsyncMock(
            return_value=(sample_problem_hypothesis, sample_verification_plan)
        )

        # Mock verifier to return evidence package
        from models.verification_events import EvidencePackage
        mock_evidence = EvidencePackage(
            verification_request_id=sample_verification_event.event_id,
            problem_hypothesis=sample_problem_hypothesis,
            verification_plan=sample_verification_plan.model_dump(),
            tool_executions=[sample_tool_execution_result],
            total_execution_time_ms=2000,
            hypothesis_confirmed=True,
            confidence_score=0.85,
            key_findings=["Test finding"],
            corrected_facts={},
            source_citations=[],
            verification_quality={
                "source_reliability": 0.9,
                "evidence_consistency": 0.8,
                "coverage_completeness": 1.0
            }
        )
        consumer.verifier.execute_verification = AsyncMock(return_value=mock_evidence)

        # Handle message
        await consumer._handle_message(mock_rabbitmq_message)

        # Verify planner was called
        consumer.planner.process_verification_request.assert_called_once()

        # Verify verifier was called
        consumer.verifier.execute_verification.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self):
        """Test handling of invalid JSON in message."""
        consumer = VerificationConsumer()

        # Create message with invalid JSON
        mock_msg = AsyncMock()
        mock_msg.body = b"Invalid JSON{{{{"
        mock_msg.routing_key = "verification.required.high"
        mock_msg.delivery_tag = 12345
        mock_msg.process = MagicMock()
        mock_msg.process.return_value.__aenter__ = AsyncMock()
        mock_msg.process.return_value.__aexit__ = AsyncMock()

        # Should not raise - error should be caught
        await consumer._handle_message(mock_msg)

        # Message should be NACKed (process context manager handles this)

    @pytest.mark.asyncio
    async def test_handle_message_planner_failure(
        self,
        mock_rabbitmq_message,
        sample_verification_event
    ):
        """Test handling when planner fails."""
        consumer = VerificationConsumer()

        # Mock planner to raise exception
        consumer.planner.process_verification_request = AsyncMock(
            side_effect=Exception("Planner failed")
        )

        # Should not raise - error should be caught and logged
        await consumer._handle_message(mock_rabbitmq_message)

        # Verify planner was called
        consumer.planner.process_verification_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_verifier_failure(
        self,
        mock_rabbitmq_message,
        sample_problem_hypothesis,
        sample_verification_plan
    ):
        """Test handling when verifier fails."""
        consumer = VerificationConsumer()

        # Mock planner success
        consumer.planner.process_verification_request = AsyncMock(
            return_value=(sample_problem_hypothesis, sample_verification_plan)
        )

        # Mock verifier failure
        consumer.verifier.execute_verification = AsyncMock(
            side_effect=Exception("Verifier failed")
        )

        # Should not raise - error should be caught and logged
        await consumer._handle_message(mock_rabbitmq_message)

        # Verify both were called
        consumer.planner.process_verification_request.assert_called_once()
        consumer.verifier.execute_verification.assert_called_once()


class TestConsumerLifecycle:
    """Test consumer lifecycle (start/stop)."""

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing RabbitMQ connection."""
        consumer = VerificationConsumer()
        consumer.connection = AsyncMock()

        await consumer.close()

        consumer.connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_connection(self):
        """Test close when no connection exists."""
        consumer = VerificationConsumer()
        consumer.connection = None

        # Should not raise
        await consumer.close()


class TestConsumerSingleton:
    """Test singleton consumer instance."""

    @pytest.mark.asyncio
    async def test_get_consumer_creates_singleton(self, mock_rabbitmq_connection, mock_settings):
        """Test that get_consumer returns singleton instance."""
        # Reset global consumer
        import app.services.verification_consumer as vc_module
        vc_module._consumer = None

        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(return_value=mock_rabbitmq_connection["connection"])):

                # First call creates instance
                consumer1 = await get_consumer()

                # Second call returns same instance
                consumer2 = await get_consumer()

                assert consumer1 is consumer2

        # Cleanup
        vc_module._consumer = None

    @pytest.mark.asyncio
    async def test_get_consumer_connects_automatically(self, mock_rabbitmq_connection, mock_settings):
        """Test that get_consumer connects to RabbitMQ automatically."""
        # Reset global consumer
        import app.services.verification_consumer as vc_module
        vc_module._consumer = None

        with patch('app.services.verification_consumer.settings', mock_settings):
            with patch('app.services.verification_consumer.aio_pika.connect_robust',
                      AsyncMock(return_value=mock_rabbitmq_connection["connection"])):

                consumer = await get_consumer()

                # Should be connected
                assert consumer.connection is not None
                assert consumer.channel is not None

        # Cleanup
        vc_module._consumer = None
