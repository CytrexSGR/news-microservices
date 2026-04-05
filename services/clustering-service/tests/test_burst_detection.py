"""Unit tests for BurstDetectionService."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.burst_detection import BurstDetectionService, BurstSeverity


class TestBurstDetectionService:
    """Tests for BurstDetectionService."""

    @pytest.fixture
    def service(self):
        """Create burst detection service with default config."""
        return BurstDetectionService(
            window_minutes=5,
            velocity_thresholds={
                "low": 3,       # 3+ articles in 5 min
                "medium": 5,    # 5+ articles in 5 min
                "high": 10,     # 10+ articles in 5 min
                "critical": 20  # 20+ articles in 5 min
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
        assert result.velocity == 4  # 4 articles in window

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
        assert result is not None
        assert result.velocity == 5  # 5 articles in 5-min window
