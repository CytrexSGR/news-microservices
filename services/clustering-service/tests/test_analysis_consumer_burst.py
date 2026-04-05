"""Tests for enhanced burst detection in analysis consumer.

Epic 1.3: Enhanced Burst Detection Integration Tests
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.burst_detection import BurstDetectionService, BurstResult, BurstSeverity
from app.workers.analysis_consumer import AnalysisConsumer


class TestAnalysisConsumerBurstDetection:
    """Tests for burst detection integration in AnalysisConsumer."""

    @pytest.fixture
    def consumer(self):
        """Create consumer with mocked dependencies."""
        consumer = AnalysisConsumer()
        consumer.event_publisher = AsyncMock()
        return consumer

    def test_consumer_initializes_burst_services(self):
        """Consumer should initialize burst detection and webhook services."""
        consumer = AnalysisConsumer()

        assert consumer.burst_detection_service is not None
        assert isinstance(consumer.burst_detection_service, BurstDetectionService)
        # Webhook service depends on BURST_WEBHOOK_ENABLED setting
        # Default is True, so it should be initialized

    def test_burst_detection_service_config(self):
        """Burst detection service should use settings from config."""
        consumer = AnalysisConsumer()
        service = consumer.burst_detection_service

        # Default config values
        assert service.window_minutes == 5
        assert service.cooldown_minutes == 30
        assert "low" in service.velocity_thresholds
        assert "critical" in service.velocity_thresholds

    @pytest.mark.asyncio
    async def test_check_burst_detection_no_burst(self, consumer):
        """Should return None when velocity below all thresholds."""
        cluster_id = uuid4()

        # Mock repositories
        mock_session = AsyncMock()

        # Mock ClusterRepository to return few timestamps (below threshold)
        with patch('app.workers.analysis_consumer.ClusterRepository') as MockClusterRepo:
            with patch('app.workers.analysis_consumer.BurstRepository') as MockBurstRepo:
                mock_cluster_repo = MockClusterRepo.return_value
                mock_burst_repo = MockBurstRepo.return_value

                # Not in cooldown - use AsyncMock for async methods
                mock_burst_repo.is_in_cooldown = AsyncMock(return_value=False)

                # Only 2 articles in window (below low threshold of 3)
                now = datetime.now(timezone.utc)
                mock_cluster_repo.get_article_timestamps = AsyncMock(return_value=[
                    now - timedelta(minutes=1),
                    now,
                ])

                result = await consumer._check_burst_detection(
                    session=mock_session,
                    cluster_id=cluster_id,
                    cluster_title="Test Cluster",
                    top_entities=["Entity1"],
                )

        assert result is None
        # Should not record any alert
        mock_burst_repo.record_burst_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_burst_detection_triggers_burst(self, consumer):
        """Should detect burst when velocity exceeds threshold."""
        cluster_id = uuid4()
        mock_session = AsyncMock()

        with patch('app.workers.analysis_consumer.ClusterRepository') as MockClusterRepo:
            with patch('app.workers.analysis_consumer.BurstRepository') as MockBurstRepo:
                mock_cluster_repo = MockClusterRepo.return_value
                mock_burst_repo = MockBurstRepo.return_value

                # Not in cooldown - use AsyncMock
                mock_burst_repo.is_in_cooldown = AsyncMock(return_value=False)

                # 5 articles in 5 min window (medium severity)
                now = datetime.now(timezone.utc)
                mock_cluster_repo.get_article_timestamps = AsyncMock(return_value=[
                    now - timedelta(minutes=i) for i in range(5)
                ])

                # Mock alert recording - use AsyncMock
                mock_burst_repo.record_burst_alert = AsyncMock(return_value=uuid4())
                mock_burst_repo.mark_alert_sent = AsyncMock()

                result = await consumer._check_burst_detection(
                    session=mock_session,
                    cluster_id=cluster_id,
                    cluster_title="Breaking News",
                    top_entities=["Entity1", "Entity2"],
                )

        assert result is not None
        assert result.velocity == 5
        assert result.severity == BurstSeverity.MEDIUM

        # Should record alert
        mock_burst_repo.record_burst_alert.assert_called_once()

        # Should publish event
        consumer.event_publisher.publish_burst_detected.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_burst_detection_respects_cooldown(self, consumer):
        """Should skip detection when cluster is in cooldown."""
        cluster_id = uuid4()
        mock_session = AsyncMock()

        with patch('app.workers.analysis_consumer.ClusterRepository') as MockClusterRepo:
            with patch('app.workers.analysis_consumer.BurstRepository') as MockBurstRepo:
                mock_burst_repo = MockBurstRepo.return_value

                # Cluster is in cooldown - use AsyncMock
                mock_burst_repo.is_in_cooldown = AsyncMock(return_value=True)
                mock_burst_repo.record_burst_alert = AsyncMock()

                result = await consumer._check_burst_detection(
                    session=mock_session,
                    cluster_id=cluster_id,
                    cluster_title="Test Cluster",
                )

        assert result is None
        # Should not check timestamps or record alert
        mock_burst_repo.record_burst_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_webhook_sent_on_burst(self, consumer):
        """Should send webhook alert when burst detected."""
        cluster_id = uuid4()
        mock_session = AsyncMock()

        # Mock the alert service
        consumer.alert_service = AsyncMock()
        consumer.alert_service.send_alert = AsyncMock(return_value=True)

        with patch('app.workers.analysis_consumer.ClusterRepository') as MockClusterRepo:
            with patch('app.workers.analysis_consumer.BurstRepository') as MockBurstRepo:
                mock_cluster_repo = MockClusterRepo.return_value
                mock_burst_repo = MockBurstRepo.return_value

                mock_burst_repo.is_in_cooldown = AsyncMock(return_value=False)

                # 10 articles = HIGH severity
                now = datetime.now(timezone.utc)
                mock_cluster_repo.get_article_timestamps = AsyncMock(return_value=[
                    now - timedelta(seconds=i * 30) for i in range(10)
                ])

                alert_id = uuid4()
                mock_burst_repo.record_burst_alert = AsyncMock(return_value=alert_id)
                mock_burst_repo.mark_alert_sent = AsyncMock()

                result = await consumer._check_burst_detection(
                    session=mock_session,
                    cluster_id=cluster_id,
                    cluster_title="Breaking News",
                    top_entities=["Market", "Crash"],
                )

        assert result is not None
        assert result.severity == BurstSeverity.HIGH

        # Webhook should be called
        consumer.alert_service.send_alert.assert_called_once()
        call_kwargs = consumer.alert_service.send_alert.call_args.kwargs
        assert call_kwargs['cluster_id'] == cluster_id
        assert call_kwargs['severity'] == BurstSeverity.HIGH

        # Alert should be marked as sent
        mock_burst_repo.mark_alert_sent.assert_called_once_with(alert_id)

    @pytest.mark.asyncio
    async def test_critical_severity_detection(self, consumer):
        """Should detect CRITICAL severity for very high velocity."""
        cluster_id = uuid4()
        mock_session = AsyncMock()

        with patch('app.workers.analysis_consumer.ClusterRepository') as MockClusterRepo:
            with patch('app.workers.analysis_consumer.BurstRepository') as MockBurstRepo:
                mock_cluster_repo = MockClusterRepo.return_value
                mock_burst_repo = MockBurstRepo.return_value

                mock_burst_repo.is_in_cooldown = AsyncMock(return_value=False)

                # 25 articles in 5 min = CRITICAL severity
                now = datetime.now(timezone.utc)
                mock_cluster_repo.get_article_timestamps = AsyncMock(return_value=[
                    now - timedelta(seconds=i * 10) for i in range(25)
                ])

                mock_burst_repo.record_burst_alert = AsyncMock(return_value=uuid4())
                mock_burst_repo.mark_alert_sent = AsyncMock()

                result = await consumer._check_burst_detection(
                    session=mock_session,
                    cluster_id=cluster_id,
                    cluster_title="Major Breaking News",
                )

        assert result is not None
        assert result.severity == BurstSeverity.CRITICAL
        assert result.velocity >= 20


class TestBurstDetectionService:
    """Unit tests for BurstDetectionService."""

    @pytest.fixture
    def service(self):
        """Create burst detection service with default config."""
        return BurstDetectionService(
            window_minutes=5,
            velocity_thresholds={
                "low": 3,
                "medium": 5,
                "high": 10,
                "critical": 20,
            },
            cooldown_minutes=30
        )

    def test_no_burst_below_threshold(self, service):
        """Should return None when velocity below all thresholds."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        # 2 articles in window (below lowest threshold of 3)
        timestamps = [now - timedelta(minutes=1), now]

        result = service.detect_burst(cluster_id, timestamps)

        assert result is None

    def test_low_severity_burst(self, service):
        """Should detect low severity burst at 3+ articles/window."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        # 4 articles in 5 min window
        timestamps = [
            now - timedelta(minutes=4),
            now - timedelta(minutes=3),
            now - timedelta(minutes=2),
            now,
        ]

        result = service.detect_burst(cluster_id, timestamps)

        assert result is not None
        assert result.severity == BurstSeverity.LOW
        assert result.velocity == 4

    def test_critical_severity_burst(self, service):
        """Should detect critical severity at 20+ articles/window."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        # 25 articles in 5 min
        timestamps = [
            now - timedelta(seconds=i * 10) for i in range(25)
        ]

        result = service.detect_burst(cluster_id, timestamps)

        assert result is not None
        assert result.severity == BurstSeverity.CRITICAL
        assert result.velocity >= 20

    def test_cooldown_prevents_repeat_detection(self, service):
        """Should not re-detect burst during cooldown period."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        timestamps = [now - timedelta(minutes=i) for i in range(5)]

        # First detection should work
        result1 = service.detect_burst(cluster_id, timestamps)
        assert result1 is not None

        # Mark as alerted (simulating cooldown)
        service.mark_alerted(cluster_id)

        # Second detection during cooldown should return None
        timestamps.append(now)
        result2 = service.detect_burst(cluster_id, timestamps)

        assert result2 is None

    def test_cooldown_expires(self, service):
        """Should detect new burst after cooldown expires."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        # Create service with 1-minute cooldown for testing
        short_cooldown_service = BurstDetectionService(
            window_minutes=5,
            velocity_thresholds={"low": 3, "medium": 5, "high": 10, "critical": 20},
            cooldown_minutes=1
        )

        timestamps = [now - timedelta(minutes=i) for i in range(5)]

        # First detection
        result1 = short_cooldown_service.detect_burst(cluster_id, timestamps)
        assert result1 is not None

        # Mark alerted and manually expire cooldown
        short_cooldown_service.mark_alerted(cluster_id)
        short_cooldown_service._cooldowns[cluster_id] = now - timedelta(minutes=2)

        # Detection after cooldown
        result2 = short_cooldown_service.detect_burst(cluster_id, timestamps)
        assert result2 is not None

    def test_velocity_calculation(self, service):
        """Should calculate correct velocity (articles per window)."""
        cluster_id = uuid4()
        now = datetime.now(timezone.utc)

        # 10 articles spread over 10 minutes (only 5 in window)
        timestamps = [now - timedelta(minutes=i) for i in range(10)]

        result = service.detect_burst(cluster_id, timestamps)

        # Only articles within 5-minute window should count
        # minutes 0, 1, 2, 3, 4 are in window = 5 articles
        assert result is not None
        assert result.velocity == 5  # 5 articles in 5-min window
