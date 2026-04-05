"""
Shared Rate Limiting Middleware

Redis-backed rate limiting with per-user and global limits.
Implements secure rate limiting with:
- Per-user tracking (JWT user_id)
- Global limits for unauthenticated requests
- Configurable limits from environment
- 429 responses with retry headers
- Automatic key cleanup

Configuration (from shared config):
- 60 requests per minute (per user)
- 1000 requests per hour (per user)
- Global fallback for unauthenticated (50% of user limits)

Usage:
    from common.rate_limiting import setup_rate_limiting

    app = FastAPI(...)
    setup_rate_limiting(app, redis_url=settings.get_redis_url())
"""

from datetime import datetime, timedelta
from typing import Optional, Callable
import hashlib
import logging

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as aioredis


logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration."""

    # Per-user limits (authenticated)
    USER_RATE_PER_MINUTE = 60
    USER_RATE_PER_HOUR = 1000

    # Global limits (unauthenticated) - 50% of user limits
    GLOBAL_RATE_PER_MINUTE = 30
    GLOBAL_RATE_PER_HOUR = 500

    # Redis key prefixes
    KEY_PREFIX = "ratelimit"
    USER_PREFIX = f"{KEY_PREFIX}:user"
    GLOBAL_PREFIX = f"{KEY_PREFIX}:global"

    # TTL for cleanup
    MINUTE_TTL = 60  # 1 minute
    HOUR_TTL = 3600  # 1 hour

    # Internal service whitelist (service names that bypass rate limiting)
    INTERNAL_SERVICE_NAMES = {
        "scheduler-service",
        "feed-service",
        "content-analysis-service",
        "auth-service",
        "research-service",
        "osint-service",
        "notification-service",
        "analytics-service",
        "search-service",
    }

    # Docker internal network prefixes (bypass rate limiting)
    INTERNAL_NETWORK_PREFIXES = (
        "172.",  # Docker default bridge
        "10.",   # Docker swarm
        "192.168.",  # Docker compose default
    )


class SecureRateLimiter:
    """
    Secure rate limiter with Redis backend.

    Features:
    - Per-user tracking via JWT user_id
    - Global limits for unauthenticated requests
    - Multiple time windows (minute/hour)
    - Automatic key cleanup
    - Retry-After headers
    """

    def __init__(self, redis_url: str):
        """
        Initialize rate limiter with Redis connection.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.config = RateLimitConfig()

    async def connect(self):
        """Establish Redis connection."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Rate limiter connected to Redis")

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Rate limiter disconnected from Redis")

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from JWT token in request.

        Args:
            request: FastAPI request object

        Returns:
            User ID if authenticated, None otherwise
        """
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        # Decode JWT (simple base64 decode for user_id extraction)
        # Note: We don't verify signature here - that's done by auth middleware
        # We just need the user_id for rate limit key generation
        try:
            import base64
            import json

            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += "=" * (4 - len(payload) % 4)

            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)

            # Extract user_id (or sub claim)
            user_id = payload_data.get("user_id") or payload_data.get("sub")
            return str(user_id) if user_id else None

        except Exception as e:
            logger.debug(f"Failed to extract user_id from JWT: {e}")
            return None

    def _is_internal_request(self, request: Request) -> bool:
        """
        Check if request is from an internal service.

        Security: Only Docker-internal IPs bypass rate limiting.
        The X-Service-Name header is used for logging only, not for granting bypass,
        since headers can be spoofed by external clients.

        Args:
            request: FastAPI request object

        Returns:
            True if request is from Docker internal network
        """
        client_ip = get_remote_address(request)
        if client_ip and any(client_ip.startswith(prefix) for prefix in self.config.INTERNAL_NETWORK_PREFIXES):
            service_name = request.headers.get("X-Service-Name", "unknown")
            logger.debug(f"Internal network request from {client_ip} (service: {service_name})")
            return True

        return False

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.

        Priority:
        1. Authenticated user ID (from JWT)
        2. IP address (hashed for privacy)

        Args:
            request: FastAPI request object

        Returns:
            Client identifier string
        """
        # Try to get user_id from JWT
        user_id = self._extract_user_id(request)
        if user_id:
            return f"user:{user_id}"

        # Fallback to IP address (hashed)
        ip = get_remote_address(request)
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        return f"ip:{ip_hash}"

    async def _check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if rate limit is exceeded.

        Args:
            key: Redis key for this limit
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        if not self.redis:
            await self.connect()

        # Increment counter
        current = await self.redis.incr(key)

        # Set expiry on first request
        if current == 1:
            await self.redis.expire(key, window_seconds)

        # Check if limit exceeded
        allowed = current <= limit
        remaining = max(0, limit - current)

        return allowed, current, remaining

    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check rate limits and return error response if exceeded.

        Checks both minute and hour limits.
        Internal service-to-service requests are exempt.

        Args:
            request: FastAPI request object

        Returns:
            JSONResponse with 429 error if limit exceeded, None if allowed
        """
        # Bypass rate limiting for internal service requests
        if self._is_internal_request(request):
            return None

        client_id = self._get_client_identifier(request)
        is_authenticated = client_id.startswith("user:")

        # Determine limits based on authentication
        if is_authenticated:
            minute_limit = self.config.USER_RATE_PER_MINUTE
            hour_limit = self.config.USER_RATE_PER_HOUR
            prefix = self.config.USER_PREFIX
        else:
            minute_limit = self.config.GLOBAL_RATE_PER_MINUTE
            hour_limit = self.config.GLOBAL_RATE_PER_HOUR
            prefix = self.config.GLOBAL_PREFIX

        # Check minute limit
        minute_key = f"{prefix}:{client_id}:minute"
        minute_allowed, minute_current, minute_remaining = await self._check_limit(
            minute_key, minute_limit, self.config.MINUTE_TTL
        )

        if not minute_allowed:
            return self._create_rate_limit_response(
                "Rate limit exceeded (minute)",
                minute_limit,
                minute_current,
                self.config.MINUTE_TTL
            )

        # Check hour limit
        hour_key = f"{prefix}:{client_id}:hour"
        hour_allowed, hour_current, hour_remaining = await self._check_limit(
            hour_key, hour_limit, self.config.HOUR_TTL
        )

        if not hour_allowed:
            return self._create_rate_limit_response(
                "Rate limit exceeded (hour)",
                hour_limit,
                hour_current,
                self.config.HOUR_TTL
            )

        # Add rate limit headers to response (will be added by middleware)
        request.state.rate_limit_minute_remaining = minute_remaining
        request.state.rate_limit_hour_remaining = hour_remaining

        return None

    def _create_rate_limit_response(
        self,
        message: str,
        limit: int,
        current: int,
        retry_after: int
    ) -> JSONResponse:
        """
        Create 429 Too Many Requests response.

        Args:
            message: Error message
            limit: Rate limit threshold
            current: Current request count
            retry_after: Seconds until retry allowed

        Returns:
            JSONResponse with 429 status and headers
        """
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": message,
                "limit": limit,
                "current": current,
                "retry_after": retry_after,
                "type": "rate_limit_error"
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp()) + retry_after)
            }
        )


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.

    Checks rate limits before processing request.
    Adds rate limit headers to response.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response with rate limit headers
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/metrics", "/"]:
        return await call_next(request)

    # Check rate limit
    limiter: SecureRateLimiter = request.app.state.rate_limiter
    error_response = await limiter.check_rate_limit(request)

    if error_response:
        return error_response

    # Process request
    response = await call_next(request)

    # Add rate limit headers to successful responses
    if hasattr(request.state, "rate_limit_minute_remaining"):
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            request.state.rate_limit_minute_remaining
        )

    if hasattr(request.state, "rate_limit_hour_remaining"):
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            request.state.rate_limit_hour_remaining
        )

    return response


def setup_rate_limiting(app: FastAPI, redis_url: str):
    """
    Configure rate limiting for FastAPI application.

    Sets up:
    - Redis-backed rate limiter
    - Per-user and global limits
    - Rate limit middleware
    - Cleanup on shutdown

    Args:
        app: FastAPI application instance
        redis_url: Redis connection URL

    Example:
        app = FastAPI(...)
        setup_rate_limiting(app, settings.get_redis_url())
    """
    # Create rate limiter
    limiter = SecureRateLimiter(redis_url)

    # Store in app state
    app.state.rate_limiter = limiter

    # Add middleware
    app.middleware("http")(rate_limit_middleware)

    # Connect on startup
    @app.on_event("startup")
    async def startup_rate_limiter():
        await limiter.connect()
        logger.info(
            f"Rate limiting enabled: {RateLimitConfig.USER_RATE_PER_MINUTE}/min, "
            f"{RateLimitConfig.USER_RATE_PER_HOUR}/hour (authenticated)"
        )

    # Cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown_rate_limiter():
        await limiter.close()

    logger.info("Rate limiting configured")
