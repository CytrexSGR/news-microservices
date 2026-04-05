"""
Test Rate Limiting Implementation

Verifies rate limiting works across all services:
- Per-user limits (JWT-based)
- Global limits (unauthenticated)
- Redis backend connectivity
- 429 responses with proper headers
"""

import pytest
import httpx
import asyncio
from datetime import datetime


# Test services
SERVICES = {
    "auth": "http://localhost:8100",
    "feed": "http://localhost:8101",
    "analytics": "http://localhost:8107",
    "research": "http://localhost:8103",
    "osint": "http://localhost:8104",
    "notification": "http://localhost:8105",
    "search": "http://localhost:8106",
}


@pytest.mark.asyncio
async def test_health_endpoints_exempt_from_rate_limiting():
    """Health endpoints should not be rate-limited."""
    async with httpx.AsyncClient() as client:
        for service_name, base_url in SERVICES.items():
            # Make many requests to health endpoint
            for _ in range(100):
                response = await client.get(f"{base_url}/health")
                # Should never get 429 on health checks
                assert response.status_code in [200, 503], \
                    f"{service_name} health check got rate limited: {response.status_code}"


@pytest.mark.asyncio
async def test_unauthenticated_rate_limit():
    """
    Unauthenticated requests should hit global rate limit.

    Global limit: 30 requests/minute
    """
    # Use auth service login endpoint (non-exempt)
    base_url = SERVICES["auth"]
    endpoint = f"{base_url}/api/v1/auth/login"

    async with httpx.AsyncClient() as client:
        rate_limited = False

        # Make 35 requests (exceeds 30/min limit)
        for i in range(35):
            response = await client.post(
                endpoint,
                json={"email": "test@test.com", "password": "test123"}
            )

            if response.status_code == 429:
                rate_limited = True
                # Verify proper headers
                assert "Retry-After" in response.headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers

                # Verify response body
                data = response.json()
                assert data["error"] == "rate_limit_exceeded"
                assert "retry_after" in data
                assert data["type"] == "rate_limit_error"

                print(f"✓ Rate limit triggered after {i+1} requests")
                break

        assert rate_limited, "Global rate limit was not enforced"


@pytest.mark.asyncio
async def test_authenticated_rate_limit():
    """
    Authenticated requests should have higher per-user limits.

    User limit: 60 requests/minute

    Note: This test requires a valid JWT token.
    """
    # First, get a valid token
    auth_url = SERVICES["auth"]

    async with httpx.AsyncClient() as client:
        # Login to get token
        login_response = await client.post(
            f"{auth_url}/api/v1/auth/login",
            json={
                "email": "andreas@test.com",
                "password": "Aug2012#"
            }
        )

        if login_response.status_code != 200:
            pytest.skip("Cannot test authenticated rate limit without valid credentials")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Make 65 requests to feed service (exceeds 60/min limit)
        feed_url = SERVICES["feed"]
        endpoint = f"{feed_url}/api/v1/feeds"

        rate_limited = False
        for i in range(65):
            response = await client.get(endpoint, headers=headers)

            if response.status_code == 429:
                rate_limited = True
                print(f"✓ Authenticated rate limit triggered after {i+1} requests")
                break

        assert rate_limited, "Per-user rate limit was not enforced"


@pytest.mark.asyncio
async def test_rate_limit_headers_present():
    """Successful requests should include rate limit headers."""
    async with httpx.AsyncClient() as client:
        # Make a single authenticated request to feed service
        auth_url = SERVICES["auth"]
        login_response = await client.post(
            f"{auth_url}/api/v1/auth/login",
            json={
                "email": "andreas@test.com",
                "password": "Aug2012#"
            }
        )

        if login_response.status_code != 200:
            pytest.skip("Cannot test without valid credentials")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        feed_url = SERVICES["feed"]
        response = await client.get(f"{feed_url}/api/v1/feeds", headers=headers)

        # Should have rate limit info headers
        assert "X-RateLimit-Remaining-Minute" in response.headers, \
            "Missing minute rate limit header"
        assert "X-RateLimit-Remaining-Hour" in response.headers, \
            "Missing hour rate limit header"

        print(f"✓ Remaining (minute): {response.headers['X-RateLimit-Remaining-Minute']}")
        print(f"✓ Remaining (hour): {response.headers['X-RateLimit-Remaining-Hour']}")


@pytest.mark.asyncio
async def test_redis_connectivity():
    """Verify Redis is accessible for rate limiting."""
    import redis.asyncio as aioredis

    redis_url = "redis://:redis_secret_2024@localhost:6379/0"

    try:
        redis_client = await aioredis.from_url(redis_url)
        pong = await redis_client.ping()
        assert pong is True, "Redis ping failed"

        # Test set/get
        await redis_client.set("ratelimit:test", "1", ex=10)
        value = await redis_client.get("ratelimit:test")
        assert value == "1", "Redis set/get failed"

        await redis_client.close()
        print("✓ Redis connectivity verified")

    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")


def test_rate_limiting_config():
    """Verify rate limiting configuration is correct."""
    from common.rate_limiting import RateLimitConfig

    config = RateLimitConfig()

    # Verify limits
    assert config.USER_RATE_PER_MINUTE == 60, "User minute limit incorrect"
    assert config.USER_RATE_PER_HOUR == 1000, "User hour limit incorrect"
    assert config.GLOBAL_RATE_PER_MINUTE == 30, "Global minute limit incorrect"
    assert config.GLOBAL_RATE_PER_HOUR == 500, "Global hour limit incorrect"

    # Verify TTLs
    assert config.MINUTE_TTL == 60, "Minute TTL incorrect"
    assert config.HOUR_TTL == 3600, "Hour TTL incorrect"

    print("✓ Rate limiting configuration correct")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
