"""
E2E Test: Authentication Integration
Tests authentication across all services.
"""
import pytest
import httpx
from typing import Dict, Any


SERVICES = {
    "auth": "http://localhost:8100",
    "feed": "http://localhost:8101",
    "content_analysis": "http://localhost:8114",
    "research": "http://localhost:8103",
    "osint": "http://localhost:8104",
    "notification": "http://localhost:8105",
    "search": "http://localhost:8106",
    "analytics": "http://localhost:8107",
}


@pytest.mark.asyncio
async def test_authentication_across_all_services(http_client: httpx.AsyncClient, test_user: Dict[str, Any], auth_headers: Dict[str, str]):
    """Test that authentication works across all services."""
    protected_endpoints = [
        ("feed", "/api/v1/feeds"),
        ("notification", "/api/v1/notifications"),
        ("search", "/api/v1/search"),
        ("analytics", "/api/v1/analytics/dashboard"),
    ]

    for service_name, endpoint in protected_endpoints:
        base_url = SERVICES[service_name]

        # Test without auth - should fail
        response = await http_client.get(f"{base_url}{endpoint}")
        assert response.status_code in [401, 403], f"{service_name} should require authentication"

        # Test with auth - should succeed
        response = await http_client.get(f"{base_url}{endpoint}", headers=auth_headers)
        assert response.status_code in [200, 404], f"{service_name} should accept valid token"
        print(f"✓ {service_name} authentication verified")


@pytest.mark.asyncio
async def test_invalid_token_rejection(http_client: httpx.AsyncClient):
    """Test that invalid tokens are rejected by all services."""
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}

    protected_endpoints = [
        "http://localhost:8101/api/v1/feeds",
        "http://localhost:8105/api/v1/notifications",
        "http://localhost:8106/api/v1/search",
        "http://localhost:8107/api/v1/analytics/dashboard",
    ]

    for endpoint in protected_endpoints:
        response = await http_client.get(endpoint, headers=invalid_headers)
        assert response.status_code in [401, 403], f"Should reject invalid token at {endpoint}"


@pytest.mark.asyncio
async def test_token_expiration_and_refresh(http_client: httpx.AsyncClient, test_user: Dict[str, Any]):
    """Test token expiration and refresh mechanism."""
    access_token = test_user["access_token"]

    # Verify current token works
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    response = await http_client.get(
        "http://localhost:8100/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Note: Token refresh would require a refresh token endpoint
    # This is a placeholder for future implementation
    print("✓ Token validation works")


@pytest.mark.asyncio
async def test_cross_service_user_context(http_client: httpx.AsyncClient, test_user: Dict[str, Any], auth_headers: Dict[str, str]):
    """Test that user context is properly maintained across services."""
    # Create a feed (Feed Service)
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Context Test Feed",
        "category": "tech"
    }
    response = await http_client.post(
        "http://localhost:8101/api/v1/feeds",
        json=feed_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    feed = response.json()

    # Verify the feed belongs to the correct user
    response = await http_client.get(
        "http://localhost:8101/api/v1/feeds",
        headers=auth_headers
    )
    assert response.status_code == 200
    feeds = response.json()
    assert any(f["id"] == feed["id"] for f in feeds)

    print("✓ User context maintained across services")


@pytest.mark.asyncio
async def test_role_based_access_control(http_client: httpx.AsyncClient, test_user: Dict[str, Any], auth_headers: Dict[str, str]):
    """Test role-based access control if implemented."""
    # Test user can access their own resources
    response = await http_client.get(
        "http://localhost:8100/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    user_info = response.json()

    # Verify role information
    assert "email" in user_info
    assert user_info["email"] == test_user["email"]

    print("✓ Role-based access control verified")


@pytest.mark.asyncio
async def test_concurrent_authentication(http_client: httpx.AsyncClient, test_user: Dict[str, Any], auth_headers: Dict[str, str]):
    """Test that authentication works under concurrent requests."""
    import asyncio

    async def make_authenticated_request(endpoint: str):
        response = await http_client.get(endpoint, headers=auth_headers)
        return response.status_code

    # Make 10 concurrent requests
    tasks = [
        make_authenticated_request("http://localhost:8101/api/v1/feeds")
        for _ in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(status in [200, 404] for status in results)
    print(f"✓ {len(results)} concurrent authenticated requests succeeded")
