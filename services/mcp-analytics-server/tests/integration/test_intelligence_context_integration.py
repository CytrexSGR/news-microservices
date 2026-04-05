"""Integration test for get_intelligence_context MCP tool.

Tests the /api/v1/intelligence/context endpoint which returns raw intelligence
data for Claude to interpret directly (no LLM call).

Requirements:
- analytics-service running on port 8107
- search-service running on port 8106

Run with: pytest tests/integration/test_intelligence_context_integration.py -v -m integration

NOTE: When running inside Docker container, tests use news-analytics-service:8000.
When running from host, tests use localhost:8107 (mapped port).
"""

import os
import pytest
import httpx


def detect_analytics_url() -> str:
    """Detect the correct analytics service URL based on environment.

    When running inside Docker container:
    - Use news-analytics-service:8000 (the container's internal hostname/port)

    When running from host machine:
    - Use localhost:8107 (Docker port mapping)
    """
    # Check if ANALYTICS_SERVICE_URL is explicitly set
    explicit_url = os.environ.get("ANALYTICS_SERVICE_URL")
    if explicit_url:
        return explicit_url

    # Check if we're inside a Docker container by looking for /.dockerenv
    in_docker = os.path.exists("/.dockerenv")

    if in_docker:
        # Inside container, use internal hostname
        return "http://news-analytics-service:8000"
    else:
        # On host, use mapped port
        return "http://localhost:8107"


# Analytics service endpoint
ANALYTICS_BASE_URL = detect_analytics_url()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_intelligence_context_via_mcp():
    """Test the full MCP tool flow."""
    # This test requires running services
    # Skip if services not available
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if analytics service is running
            health = await client.get(f"{ANALYTICS_BASE_URL}/health")
            if health.status_code != 200:
                pytest.skip("Analytics service not running")
    except httpx.ConnectError:
        pytest.skip("Analytics service not running")

    # Test the endpoint directly
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/intelligence/context",
            params={
                "question": "What are the risks for defense companies?",
                "limit": 5,
            }
        )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "question" in data
    assert "articles" in data
    assert "total_found" in data
    assert "showing" in data
    assert "has_more" in data
    assert "intelligence_summary" in data

    # Verify no LLM answer
    assert "answer" not in data

    # Verify articles have expected fields
    if data["articles"]:
        article = data["articles"][0]
        assert "title" in article
        assert "similarity" in article
        assert "content_snippet" in article


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_intelligence_context_pagination():
    """Test that has_more works correctly."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            health = await client.get(f"{ANALYTICS_BASE_URL}/health")
            if health.status_code != 200:
                pytest.skip("Analytics service not running")
    except httpx.ConnectError:
        pytest.skip("Analytics service not running")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Request with small limit
        response = await client.get(
            f"{ANALYTICS_BASE_URL}/api/v1/intelligence/context",
            params={
                "question": "news",  # Broad query
                "limit": 2,
            }
        )

    assert response.status_code == 200
    data = response.json()

    # With small limit and broad query, should indicate more available
    assert data["showing"] <= 2
    # has_more should be True if there are more results
    if data["total_found"] > 2:
        assert data["has_more"] is True
