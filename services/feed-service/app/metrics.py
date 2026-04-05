"""
Prometheus metrics for feed service.

This module defines Prometheus metrics for monitoring feed assessments.
Metrics are collected at key points in the assessment lifecycle:
- Started: When assessment request is initiated
- Succeeded: When assessment completes successfully
- Failed: When assessment fails (timeout, error, etc.)
- Duration: Time from start to completion

Usage:
    from app.metrics import (
        ASSESSMENT_STARTED, ASSESSMENT_SUCCEEDED, ASSESSMENT_FAILED,
        ASSESSMENT_DURATION, track_assessment_started, track_assessment_completed
    )

    # Start assessment
    track_assessment_started(feed_id="abc-123")

    # Complete assessment (success)
    track_assessment_completed(feed_id="abc-123", success=True, duration_seconds=12.5)

    # Complete assessment (failure)
    track_assessment_completed(feed_id="abc-123", success=False, duration_seconds=8.2, error_type="timeout")
"""

from prometheus_client import Counter, Histogram

# Counter: Assessments started
ASSESSMENT_STARTED = Counter(
    'feed_assessment_started_total',
    'Total number of feed assessments started',
    ['feed_id']
)

# Counter: Assessments succeeded
ASSESSMENT_SUCCEEDED = Counter(
    'feed_assessment_succeeded_total',
    'Total number of feed assessments that completed successfully',
    ['feed_id', 'credibility_tier']
)

# Counter: Assessments failed
ASSESSMENT_FAILED = Counter(
    'feed_assessment_failed_total',
    'Total number of feed assessments that failed',
    ['feed_id', 'error_type']
)

# Histogram: Assessment duration (time from start to completion)
ASSESSMENT_DURATION = Histogram(
    'feed_assessment_duration_seconds',
    'Time taken for feed assessment to complete (success or failure)',
    ['feed_id', 'status'],  # status = completed | failed | timeout
    buckets=(5.0, 10.0, 15.0, 20.0, 30.0, 60.0, 120.0, 240.0, float('inf'))
)


def track_assessment_started(feed_id: str):
    """
    Track that an assessment has been started.

    Args:
        feed_id: UUID of the feed being assessed

    Example:
        track_assessment_started("bba49986-e780-4c8f-b8ca-d8f258bc42ad")
    """
    ASSESSMENT_STARTED.labels(feed_id=feed_id).inc()


def track_assessment_completed(
    feed_id: str,
    success: bool,
    duration_seconds: float,
    credibility_tier: str = None,
    error_type: str = None
):
    """
    Track that an assessment has been completed (success or failure).

    Args:
        feed_id: UUID of the feed being assessed
        success: True if assessment succeeded, False if failed
        duration_seconds: Time taken from start to completion
        credibility_tier: Credibility tier (tier_1, tier_2, tier_3) - required if success=True
        error_type: Error type (timeout, http_error, validation_error) - required if success=False

    Examples:
        # Success
        track_assessment_completed(
            feed_id="bba49986-e780-4c8f-b8ca-d8f258bc42ad",
            success=True,
            duration_seconds=12.5,
            credibility_tier="tier_2"
        )

        # Failure
        track_assessment_completed(
            feed_id="bba49986-e780-4c8f-b8ca-d8f258bc42ad",
            success=False,
            duration_seconds=8.2,
            error_type="timeout"
        )
    """
    if success:
        # Record success
        ASSESSMENT_SUCCEEDED.labels(
            feed_id=feed_id,
            credibility_tier=credibility_tier or "unknown"
        ).inc()

        # Record duration for successful assessment
        ASSESSMENT_DURATION.labels(
            feed_id=feed_id,
            status="completed"
        ).observe(duration_seconds)
    else:
        # Record failure
        ASSESSMENT_FAILED.labels(
            feed_id=feed_id,
            error_type=error_type or "unknown"
        ).inc()

        # Record duration for failed assessment
        ASSESSMENT_DURATION.labels(
            feed_id=feed_id,
            status="failed"
        ).observe(duration_seconds)
