"""
Datetime utility functions for consistent UTC handling across all services.

All timestamps in the database MUST be timezone-aware UTC.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with tzinfo=timezone.utc

    Example:
        >>> created_at = utc_now()
        >>> assert created_at.tzinfo == timezone.utc
    """
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC timezone.

    Args:
        dt: Datetime to convert (naive or aware)

    Returns:
        datetime: Timezone-aware UTC datetime

    Example:
        >>> import pytz
        >>> eastern = pytz.timezone('US/Eastern')
        >>> local_time = eastern.localize(datetime(2025, 1, 15, 12, 0))
        >>> utc_time = to_utc(local_time)
        >>> assert utc_time.tzinfo == timezone.utc
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)

    # Convert to UTC
    return dt.astimezone(timezone.utc)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """
    Ensure datetime is UTC, return None if None passed.

    Args:
        dt: Datetime to convert or None

    Returns:
        datetime | None: UTC datetime or None
    """
    if dt is None:
        return None

    return to_utc(dt)
