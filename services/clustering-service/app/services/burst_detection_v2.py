"""Enhanced burst detection v2 with multi-signal analysis.

Improvements over v1:
- Growth rate: Compares current window to previous period (detects acceleration)
- Activity concentration: % of articles in recent time vs total (detects sudden interest)
- Source diversity: Unique sources count (multi-source = real story, not single outlet)
- Baseline comparison: Compares to cluster's historical activity level

Example:
    >>> service = EnhancedBurstDetectionService()
    >>> result = service.detect_burst(cluster_id, article_timestamps, source_ids)
    >>> if result:
    ...     print(f"Burst: {result.severity} (growth={result.growth_rate}x)")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
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
class EnhancedBurstResult:
    """Result of enhanced burst detection analysis.

    Attributes:
        cluster_id: UUID of the cluster with burst activity
        severity: Severity level (low, medium, high, critical)
        velocity: Number of articles within the detection window
        window_minutes: Size of the detection window
        detected_at: Timestamp when burst was detected
        growth_rate: Multiplier vs previous period (2.0 = doubled)
        concentration: % of articles in window vs total cluster articles
        unique_sources: Number of different news sources
        signals: Dict of which signals triggered (for debugging)
    """
    cluster_id: UUID
    severity: BurstSeverity
    velocity: int
    window_minutes: int
    detected_at: datetime
    growth_rate: float = 1.0
    concentration: float = 0.0
    unique_sources: int = 1
    signals: Dict[str, bool] = field(default_factory=dict)


# Prometheus metrics
BURST_V2_DETECTED = Counter(
    "clustering_burst_v2_detected_total",
    "Total enhanced bursts detected",
    ["severity", "signal"]
)

BURST_V2_GROWTH_RATE = Histogram(
    "clustering_burst_v2_growth_rate",
    "Growth rate of detected bursts",
    buckets=[1.5, 2.0, 3.0, 5.0, 10.0, 20.0]
)


class EnhancedBurstDetectionService:
    """
    Multi-signal burst detection for breaking news.

    Uses multiple signals to reduce false positives:
    - Velocity: Raw article count in window (legacy compatibility)
    - Growth Rate: Acceleration vs previous period
    - Concentration: Activity spike detection
    - Source Diversity: Multi-source validation

    A burst is detected when MULTIPLE signals agree, not just velocity.

    Example:
        >>> service = EnhancedBurstDetectionService(
        ...     window_minutes=15,
        ...     growth_rate_threshold=2.0,
        ...     min_sources=2
        ... )
        >>> result = service.detect_burst(cluster_id, timestamps, sources)
    """

    def __init__(
        self,
        window_minutes: int = 15,
        velocity_thresholds: Optional[Dict[str, int]] = None,
        cooldown_minutes: int = 30,
        growth_rate_threshold: float = 2.0,
        concentration_threshold: float = 0.5,
        min_sources: int = 2,
        require_multi_signal: bool = True,
    ):
        """
        Initialize enhanced burst detection.

        Args:
            window_minutes: Size of detection window
            velocity_thresholds: Dict mapping severity to min velocity
            cooldown_minutes: Cooldown between alerts per cluster
            growth_rate_threshold: Min growth rate to trigger (e.g., 2.0 = doubled)
            concentration_threshold: Min % of articles in window (e.g., 0.5 = 50%)
            min_sources: Minimum unique sources required
            require_multi_signal: If True, need velocity + at least one other signal
        """
        self.window_minutes = window_minutes
        self.velocity_thresholds = velocity_thresholds or {
            "low": 3,
            "medium": 5,
            "high": 10,
            "critical": 20,
        }
        self.cooldown_minutes = cooldown_minutes
        self.growth_rate_threshold = growth_rate_threshold
        self.concentration_threshold = concentration_threshold
        self.min_sources = min_sources
        self.require_multi_signal = require_multi_signal

        # Internal state
        self._cooldowns: Dict[UUID, datetime] = {}

    def detect_burst(
        self,
        cluster_id: UUID,
        article_timestamps: List[datetime],
        source_ids: Optional[List[str]] = None,
    ) -> Optional[EnhancedBurstResult]:
        """
        Detect burst using multiple signals.

        Args:
            cluster_id: UUID of the cluster to check
            article_timestamps: List of article arrival timestamps
            source_ids: Optional list of source IDs (parallel to timestamps)

        Returns:
            EnhancedBurstResult if burst detected, None otherwise
        """
        now = datetime.now(timezone.utc)

        # Check cooldown
        if self._is_in_cooldown(cluster_id, now):
            logger.debug(f"Cluster {cluster_id} in cooldown, skipping")
            return None

        if not article_timestamps:
            return None

        # Calculate all signals
        velocity = self._calculate_velocity(article_timestamps, now)
        growth_rate = self._calculate_growth_rate(article_timestamps, now)
        concentration = self._calculate_concentration(article_timestamps, now)
        unique_sources = self._calculate_source_diversity(
            article_timestamps, source_ids, now
        )

        # Evaluate signals
        signals = {
            "velocity": velocity >= self.velocity_thresholds.get("low", 3),
            "growth_rate": growth_rate >= self.growth_rate_threshold,
            "concentration": concentration >= self.concentration_threshold,
            "multi_source": unique_sources >= self.min_sources,
        }

        # Decision logic
        velocity_ok = signals["velocity"]
        other_signals = sum([
            signals["growth_rate"],
            signals["concentration"],
            signals["multi_source"],
        ])

        if not velocity_ok:
            return None

        if self.require_multi_signal and other_signals < 1:
            # Velocity alone isn't enough
            logger.debug(
                f"Cluster {cluster_id}: velocity={velocity} but no supporting signals"
            )
            return None

        # Determine severity based on strongest signals
        severity = self._determine_severity(velocity, growth_rate, concentration)

        # Record metrics
        primary_signal = "velocity"
        if signals["growth_rate"]:
            primary_signal = "growth_rate"
        elif signals["concentration"]:
            primary_signal = "concentration"

        BURST_V2_DETECTED.labels(severity=severity.value, signal=primary_signal).inc()
        BURST_V2_GROWTH_RATE.observe(growth_rate)

        logger.info(
            f"Enhanced burst detected: cluster={cluster_id} "
            f"severity={severity.value} velocity={velocity} "
            f"growth_rate={growth_rate:.1f}x concentration={concentration:.0%} "
            f"sources={unique_sources} signals={signals}"
        )

        return EnhancedBurstResult(
            cluster_id=cluster_id,
            severity=severity,
            velocity=velocity,
            window_minutes=self.window_minutes,
            detected_at=now,
            growth_rate=growth_rate,
            concentration=concentration,
            unique_sources=unique_sources,
            signals=signals,
        )

    def mark_alerted(self, cluster_id: UUID) -> None:
        """Mark cluster as alerted to start cooldown."""
        self._cooldowns[cluster_id] = datetime.now(timezone.utc)

    def clear_cooldown(self, cluster_id: UUID) -> None:
        """Clear cooldown for a cluster."""
        self._cooldowns.pop(cluster_id, None)

    def _is_in_cooldown(self, cluster_id: UUID, now: datetime) -> bool:
        """Check if cluster is in cooldown."""
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
        """Calculate articles in current window."""
        window_start = now - timedelta(minutes=self.window_minutes)
        return sum(1 for ts in timestamps if window_start <= ts <= now)

    def _calculate_growth_rate(
        self,
        timestamps: List[datetime],
        now: datetime
    ) -> float:
        """
        Calculate growth rate: current window vs previous period.

        Growth rate = current_count / previous_count
        - 1.0 = same as before
        - 2.0 = doubled
        - 0.5 = halved
        """
        window_duration = timedelta(minutes=self.window_minutes)
        current_start = now - window_duration
        previous_start = current_start - window_duration

        current_count = sum(1 for ts in timestamps if current_start <= ts <= now)
        previous_count = sum(
            1 for ts in timestamps if previous_start <= ts < current_start
        )

        if previous_count == 0:
            # No baseline - if we have articles now, it's "infinite" growth
            # Cap at 10.0 to avoid extreme values
            return min(10.0, float(current_count)) if current_count > 0 else 0.0

        return current_count / previous_count

    def _calculate_concentration(
        self,
        timestamps: List[datetime],
        now: datetime
    ) -> float:
        """
        Calculate activity concentration: % of articles in window vs total.

        High concentration = sudden spike of interest
        - 0.8 = 80% of all cluster articles arrived in this window
        - 0.2 = only 20% of articles are recent (steady activity)
        """
        if not timestamps:
            return 0.0

        window_start = now - timedelta(minutes=self.window_minutes)
        window_count = sum(1 for ts in timestamps if window_start <= ts <= now)
        total_count = len(timestamps)

        return window_count / total_count

    def _calculate_source_diversity(
        self,
        timestamps: List[datetime],
        source_ids: Optional[List[str]],
        now: datetime
    ) -> int:
        """
        Calculate unique sources in window.

        High diversity = real breaking news (multiple outlets reporting)
        Low diversity = single source spam
        """
        if source_ids is None or not source_ids:
            return 1  # Assume at least one source

        window_start = now - timedelta(minutes=self.window_minutes)

        # Get sources for articles in window
        sources_in_window: Set[str] = set()
        for ts, source in zip(timestamps, source_ids):
            if window_start <= ts <= now:
                sources_in_window.add(source)

        return len(sources_in_window)

    def _determine_severity(
        self,
        velocity: int,
        growth_rate: float,
        concentration: float
    ) -> BurstSeverity:
        """
        Determine severity from multiple factors.

        Uses weighted scoring:
        - Velocity contributes to base severity
        - Growth rate can boost severity
        - Concentration can boost severity
        """
        # Base severity from velocity
        base_severity = BurstSeverity.LOW
        for severity in reversed(list(BurstSeverity)):
            threshold = self.velocity_thresholds.get(severity.value, float('inf'))
            if velocity >= threshold:
                base_severity = severity
                break

        # Calculate boost score
        boost = 0
        if growth_rate >= 5.0:
            boost += 2
        elif growth_rate >= 3.0:
            boost += 1

        if concentration >= 0.8:
            boost += 1

        # Apply boost
        severities = list(BurstSeverity)
        base_idx = severities.index(base_severity)
        boosted_idx = min(base_idx + boost, len(severities) - 1)

        return severities[boosted_idx]
