"""
Pytest configuration and fixtures for scraping-service tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    mock = AsyncMock()

    # Create a mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"scrape_failure_threshold": 5})

    mock.get = AsyncMock(return_value=mock_response)
    mock.patch = AsyncMock(return_value=mock_response)
    mock.aclose = AsyncMock()

    return mock


@pytest.fixture
def mock_rabbitmq_connection():
    """Create a mock RabbitMQ connection for testing."""
    mock_connection = AsyncMock()
    mock_connection.is_closed = False
    mock_connection.close = AsyncMock()

    mock_channel = AsyncMock()
    mock_channel.is_closed = False
    mock_channel.close = AsyncMock()
    mock_channel.set_qos = AsyncMock()

    mock_exchange = AsyncMock()
    mock_exchange.publish = AsyncMock()

    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_connection.channel = AsyncMock(return_value=mock_channel)

    return {
        "connection": mock_connection,
        "channel": mock_channel,
        "exchange": mock_exchange
    }


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing."""
    from jose import jwt
    from app.core.config import settings

    payload = {
        "sub": "test-user-123",
        "username": "testuser",
        "roles": ["user"],
        "exp": datetime.now(timezone.utc).timestamp() + 3600,
        "iat": datetime.now(timezone.utc).timestamp(),
        "type": "access"
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing."""
    from jose import jwt
    from app.core.config import settings

    payload = {
        "sub": "test-user-123",
        "username": "testuser",
        "roles": ["user"],
        "exp": datetime.now(timezone.utc).timestamp() - 3600,  # Expired 1 hour ago
        "iat": datetime.now(timezone.utc).timestamp() - 7200,
        "type": "access"
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
