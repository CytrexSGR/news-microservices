"""
Rate Limiting Configuration

Issue #3: Provides rate limiting for API endpoints to prevent abuse.

Usage in routes:
    from app.core.rate_limiting import limiter, RateLimits

    @router.post("/run")
    @limiter.limit(RateLimits.ANALYSIS)
    async def trigger_analysis(request: Request):
        ...
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


# Initialize global rate limiter
# Uses client IP for rate limit tracking
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)


class RateLimits:
    """
    Rate limit constants for different endpoint types.

    Limits are configured per-minute to allow burst traffic
    while preventing sustained abuse.
    """

    # Default: 100 req/min - standard read endpoints
    DEFAULT = "100/minute"

    # Analysis: 5 req/min - heavy Neo4j operations
    # Analysis runs can take 20-50 seconds each
    ANALYSIS = "5/minute"

    # Status: 60 req/min - lightweight health checks
    STATUS = "60/minute"


def get_rate_limit_info() -> dict:
    """Get current rate limit configuration for status endpoints."""
    return {
        "default": RateLimits.DEFAULT,
        "analysis": RateLimits.ANALYSIS,
        "status": RateLimits.STATUS,
    }
