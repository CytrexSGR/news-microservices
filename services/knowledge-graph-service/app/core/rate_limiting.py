"""
Rate Limiting Configuration

Post-Incident #18: Provides rate limiting decorators for API endpoints
to prevent abuse and protect Neo4j from overload.

Usage in routes:
    from app.core.rate_limiting import limiter, RateLimits

    @router.get("/search")
    @limiter.limit(RateLimits.SEARCH)
    async def search(request: Request):
        ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


# Initialize global rate limiter
# Uses client IP for rate limit tracking, in-memory storage
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT]
)


class RateLimits:
    """
    Rate limit constants for different endpoint types.

    Limits are configured per-minute to allow burst traffic
    while preventing sustained abuse.
    """

    # Default: 100 req/min - standard read endpoints
    DEFAULT = settings.RATE_LIMIT_DEFAULT

    # Search: 60 req/min - heavier queries on Neo4j
    SEARCH = settings.RATE_LIMIT_SEARCH

    # Write: 30 req/min - graph mutations
    WRITE = settings.RATE_LIMIT_WRITE

    # Admin: 10 req/min - raw Cypher queries, dangerous operations
    ADMIN = settings.RATE_LIMIT_ADMIN


def get_rate_limit_info() -> dict:
    """Get current rate limit configuration for health/status endpoints."""
    return {
        "default": RateLimits.DEFAULT,
        "search": RateLimits.SEARCH,
        "write": RateLimits.WRITE,
        "admin": RateLimits.ADMIN,
    }
