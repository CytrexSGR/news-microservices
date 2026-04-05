"""
E2E Test Configuration and Fixtures
Provides shared test infrastructure for end-to-end testing.
"""
import pytest
import asyncio
import httpx
from typing import AsyncGenerator, Dict, Any
import time
import os


# Service URLs (mapped to avoid conflicts)
SERVICES = {
    "auth": "http://localhost:8100",
    "feed": "http://localhost:8101",
    "content_analysis": "http://localhost:8114",
    "research": "http://localhost:8103",
    "osint": "http://localhost:8104",
    "notification": "http://localhost:8105",
    "search": "http://localhost:8106",
    "analytics": "http://localhost:8107",
    "traefik": "http://localhost:81",
}

API_PREFIX = "/api/v1"

HEALTH_ENDPOINTS = {
    "content_analysis": f"{API_PREFIX}/health",
    "research": f"{API_PREFIX}/health",
    "osint": f"{API_PREFIX}/health",
}


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def health_check():
    """Wait for all services to be healthy before running tests."""
    max_retries = 60
    retry_interval = 2

    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, base_url in SERVICES.items():
            if service_name == "traefik":
                continue

            health_path = HEALTH_ENDPOINTS.get(service_name, "/health")
            health_url = f"{base_url}{health_path}"

            for attempt in range(max_retries):
                try:
                    response = await client.get(health_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "healthy":
                            print(f"✓ {service_name} service healthy")
                            break
                except Exception as e:
                    if attempt == max_retries - 1:
                        pytest.fail(f"Service {service_name} not healthy after {max_retries} retries: {e}")
                    time.sleep(retry_interval)


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide async HTTP client for tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def test_user(http_client: httpx.AsyncClient) -> Dict[str, Any]:
    """Create and return a test user with authentication token."""
    auth_url = f"{SERVICES['auth']}{API_PREFIX}/auth"

    # Create unique user for this test
    import uuid
    user_id = str(uuid.uuid4())[:8]

    user_data = {
        "email": f"test_{user_id}@example.com",
        "password": "Test123!@#",
        "username": f"testuser_{user_id}",
        "full_name": f"Test User {user_id}"
    }

    # Register user
    response = await http_client.post(f"{auth_url}/register", json=user_data)
    assert response.status_code == 201, f"User registration failed: {response.text}"

    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = await http_client.post(f"{auth_url}/login", json=login_data)
    assert response.status_code == 200, f"User login failed: {response.text}"

    token_data = response.json()

    return {
        **user_data,
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "user_id": token_data.get("user_id")
    }


@pytest.fixture
def auth_headers(test_user: Dict[str, Any]) -> Dict[str, str]:
    """Provide authentication headers for requests."""
    return {
        "Authorization": f"{test_user['token_type']} {test_user['access_token']}"
    }


@pytest.fixture
async def test_feed(http_client: httpx.AsyncClient, auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Create a test RSS feed."""
    import uuid
    feed_url = f"{SERVICES['feed']}{API_PREFIX}/feeds"

    # Use unique URL to avoid conflicts
    test_id = str(uuid.uuid4())[:8]
    feed_data = {
        "url": f"https://news.ycombinator.com/rss?test={test_id}",
        "name": f"Hacker News Test {test_id}",
        "category": "technology",
        "fetch_interval": 1440  # Max allowed: 1440 minutes (24 hours)
    }

    response = await http_client.post(feed_url, json=feed_data, headers=auth_headers)
    assert response.status_code == 201, f"Feed creation failed: {response.text}"

    return response.json()


@pytest.fixture
async def test_article(http_client: httpx.AsyncClient, auth_headers: Dict[str, str], test_feed: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch articles from test feed."""
    feed_id = test_feed["id"]
    feed_url = f"{SERVICES['feed']}{API_PREFIX}/feeds/{feed_id}/fetch"

    response = await http_client.post(feed_url, headers=auth_headers)
    assert response.status_code == 200, f"Article fetch failed: {response.text}"

    result = response.json()

    # Get the first article
    articles_url = f"{SERVICES['feed']}{API_PREFIX}/feeds/{feed_id}/articles"
    response = await http_client.get(articles_url, headers=auth_headers)
    articles = response.json()

    if articles and len(articles) > 0:
        return articles[0]

    return result


@pytest.fixture(scope="session")
def rabbitmq_config() -> Dict[str, str]:
    """RabbitMQ connection configuration."""
    return {
        "host": os.getenv("RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("RABBITMQ_PORT", "5673")),
        "user": os.getenv("RABBITMQ_USER", "admin"),
        "password": os.getenv("RABBITMQ_PASS", "rabbit_secret_2024"),
        "vhost": os.getenv("RABBITMQ_VHOST", "news_mcp")
    }


@pytest.fixture(scope="session")
def redis_config() -> Dict[str, Any]:
    """Redis connection configuration."""
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6380")),
        "password": os.getenv("REDIS_PASSWORD", "redis_secret_2024"),
        "db": 0
    }


@pytest.fixture(scope="session")
def postgres_config() -> Dict[str, str]:
    """PostgreSQL connection configuration."""
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "your_db_password"),
        "database": os.getenv("POSTGRES_DB", "news_mcp")
    }


@pytest.fixture
async def cleanup_test_data(http_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Cleanup test data after tests complete."""
    yield

    # Cleanup logic can be added here if needed
    # For now, each test creates unique data
    pass
