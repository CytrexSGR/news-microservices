"""
High-level smoke tests to validate core service touchpoints.
"""

import pytest
import httpx
from uuid import uuid4

from conftest import SERVICES, API_PREFIX


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_auth_login_smoke(test_user: dict):
    """Ensure auth service issues usable tokens."""
    assert test_user["access_token"], "access token missing"
    assert test_user["token_type"].lower() == "bearer"


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_feed_create_smoke(test_feed: dict):
    """Verify feed creation workflow."""
    assert "id" in test_feed
    assert test_feed["url"].startswith("https://")


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_content_analysis_sentiment_smoke(
    http_client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Run a short sentiment analysis to ensure LLM pipeline responds."""
    payload = {
        "content": "The upgrade rollout completed successfully and customers are delighted.",
        "article_id": str(uuid4()),
        "detect_bias": False,
        "detect_emotion": True,
        "use_cache": True,
    }
    response = await http_client.post(
        f"{SERVICES['content_analysis']}{API_PREFIX}/analyze/sentiment",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "overall_sentiment" in data
    assert data.get("confidence") is not None


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_search_query_smoke(
    http_client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Execute a basic search query."""
    params = {"query": "news"}
    response = await http_client.get(
        f"{SERVICES['search']}{API_PREFIX}/search",
        params=params,
        headers=auth_headers,
    )
    assert response.status_code in {200, 204, 404}, response.text


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_notification_health_smoke(http_client: httpx.AsyncClient):
    """Ensure notification service exposes health endpoint."""
    response = await http_client.get(f"{SERVICES['notification']}/health")
    assert response.status_code == 200, response.text
    assert response.json().get("status") == "healthy"
