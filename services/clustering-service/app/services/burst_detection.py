"""Enhanced burst detection with time-windowed velocity tracking.

Provides intelligent breaking news detection based on article arrival
velocity within configurable time windows.

Features:
- Sliding window velocity calculation
- Multiple severity levels (low, medium, high, critical)
- Cooldown period to prevent alert spam
- Prometheus metrics for monitoring

Example:
    >>> service = BurstDetectionService()
    >>> result = service.detect_burst(cluster_id, article_timestamps)
    >>> if result:
    ...     print(f"Burst detected: {result.severity} at {result.velocity} articles/window")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class BurstSeverity(str, Enum):
    """Severity levels for burst detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BurstResult:
    """Result of burst detection analysis.

    Attributes:
        cluster_id: UUID of the cluster with burst activity
        severity: Severity level (low, medium, high, critical)
        velocity: Number of articles within the detection window
        window_minutes: Size of the detection window
        detected_at: Timestamp when burst was detected
    """
    cluster_id: UUID
    severity: BurstSeverity
    velocity: int
    window_minutes: int
    detected_at: datetime


# Prometheus metrics
BURST_DETECTED = Counter(
    "clustering_burst_detected_total",
    "Total bursts detected",
    ["severity"]
)

BURST_VELOCITY = Histogram(
    "clustering_burst_velocity",
    "Velocity of detected bursts (articles/window)",
    buckets=[3, 5, 10, 20, 50, 100]
)


class BurstDetectionService:
    """
    Time-windowed velocity tracking for breaking news detection.

    Uses sliding window algorithm to track article arrival velocity
    and detect bursts based on configurable thresholds.

    Attributes:
        window_minutes: Size of the sliding window for velocity calculation
        velocity_thresholds: Dict mapping severity to minimum velocity
        cooldown_minutes: Time to wait before re-alerting on same cluster

    Example:
        >>> service = BurstDetectionService(
        ...     window_minutes=5,
        ...     velocity_thresholds={"low": 3, "medium": 5, "high": 10, "critical": 20},
        ...     cooldown_minutes=30
        ... )
        >>> timestamps = [datetime.now(timezone.utc) - timedelta(minutes=i) for i in range(10)]
        >>> result = service.detect_burst(cluster_id, timestamps)
    """

    def __init__(
        self,
        window_minutes: int = 5,
        velocity_thresholds: Optional[Dict[str, int]] = None,
        cooldown_minutes: int = 30,
    ):
        """
        Initialize burst detection service.

        Args:
            window_minutes: Size of sliding window for velocity calculation
            velocity_thresholds: Dict mapping severity level to minimum velocity
            cooldown_minutes: Minutes to wait before re-alerting same cluster
        """
        self.window_minutes = window_minutes
        self.velocity_thresholds = velocity_thresholds or {
            "low": 3,
            "medium": 5,
            "high": 10,
            "critical": 20,
        }
        self.cooldown_minutes = cooldown_minutes

        # Internal state: cluster_id -> last alert timestamp
        self._cooldowns: Dict[UUID, datetime] = {}

    def detect_burst(
        self,
        cluster_id: UUID,
        article_timestamps: List[datetime],
    ) -> Optional[BurstResult]:
        """
        Detect if cluster has burst activity.

        Calculates velocity (articles within window) and checks against
        thresholds. Returns None if no burst or cluster is in cooldown.

        Args:
            cluster_id: UUID of the cluster to check
            article_timestamps: List of article arrival timestamps

        Returns:
            BurstResult if burst detected, None otherwise
        """
        now = datetime.now(timezone.utc)

        # Check cooldown
        if self._is_in_cooldown(cluster_id, now):
            logger.debug(f"Cluster {cluster_id} in cooldown, skipping detection")
            return None

        # Calculate velocity (articles in window)
        velocity = self._calculate_velocity(article_timestamps, now)

        # Determine severity (highest matching threshold)
        severity = self._determine_severity(velocity)

        if severity is None:
            return None

        # Record metrics
        BURST_DETECTED.labels(severity=severity.value).inc()
        BURST_VELOCITY.observe(velocity)

        logger.info(
            f"Burst detected: cluster={cluster_id} severity={severity.value} "
            f"velocity={velocity} window={self.window_minutes}min"
        )

        return BurstResult(
            cluster_id=cluster_id,
            severity=severity,
            velocity=velocity,
            window_minutes=self.window_minutes,
            detected_at=now,
        )

    def mark_alerted(self, cluster_id: UUID) -> None:
        """
        Mark cluster as alerted to start cooldown period.

        Args:
            cluster_id: UUID of the cluster that was alerted
        """
        self._cooldowns[cluster_id] = datetime.now(timezone.utc)
        logger.debug(f"Cluster {cluster_id} marked as alerted, cooldown started")

    def clear_cooldown(self, cluster_id: UUID) -> None:
        """
        Clear cooldown for a cluster (e.g., after manual reset).

        Args:
            cluster_id: UUID of the cluster to clear
        """
        self._cooldowns.pop(cluster_id, None)
        logger.debug(f"Cluster {cluster_id} cooldown cleared")

    def _is_in_cooldown(self, cluster_id: UUID, now: datetime) -> bool:
        """Check if cluster is still in cooldown period."""
        last_alert = self._cooldowns.get(cluster_id)
        if last_alert is None:
            return False

        cooldown_end = last_alert + timedelta(minutes=self.cooldown_minutes)
        return now < cooldown_end

    def _calculate_velocity(
        self,
        timestamps: List[datetime],
        now: datetime
    ) -> int:
        """Calculate number of articles within the detection window."""
        window_start = now - timedelta(minutes=self.window_minutes)

        count = sum(
            1 for ts in timestamps
            if ts >= window_start and ts <= now
        )

        return count

    def _determine_severity(self, velocity: int) -> Optional[BurstSeverity]:
        """Determine highest matching severity level for velocity."""
        # Check thresholds from highest to lowest
        for severity in reversed(list(BurstSeverity)):
            threshold = self.velocity_thresholds.get(severity.value, float('inf'))
            if velocity >= threshold:
                return severity

        return None
