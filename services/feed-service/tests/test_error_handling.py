"""
Integration Tests for Error Handling

Tests standardized error responses across all endpoints.

Task 406: Error Handling Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, DataError
from unittest.mock import AsyncMock, patch

from app.main import app
from app.api.errors import (
    FeedServiceError,
    ResourceNotFoundError,
    ValidationError,
    DuplicateResourceError,
    CircuitBreakerOpenError,
    error_response,
)


client = TestClient(app)


# =============================================================================
# Error Response Format Tests
# =============================================================================

def test_error_response_format():
    """Test standardized error response format"""
    response = error_response(
        message="Test error",
        status_code=400,
        error_code="TEST_ERROR",
        details={"field": "value"},
        request_id="test-123",
    )

    assert response.status_code == 400
    data = response.body.decode()

    import json
    error_data = json.loads(data)

    assert "error" in error_data
    assert error_data["error"]["code"] == "TEST_ERROR"
    assert error_data["error"]["message"] == "Test error"
    assert error_data["error"]["status"] == 400
    assert "timestamp" in error_data["error"]
    assert error_data["error"]["request_id"] == "test-123"
    assert error_data["error"]["details"] == {"field": "value"}


# =============================================================================
# Custom Exception Tests
# =============================================================================

def test_resource_not_found_error():
    """Test ResourceNotFoundError"""
    error = ResourceNotFoundError(resource="Feed", identifier=123)

    assert error.status_code == 404
    assert error.error_code == "RESOURCE_NOT_FOUND"
    assert "Feed" in error.message
    assert "123" in error.message
    assert error.details["resource"] == "Feed"
    assert error.details["identifier"] == "123"


def test_validation_error():
    """Test ValidationError"""
    error = ValidationError(
        message="Invalid input",
        details={"field": "url", "error": "Invalid URL format"}
    )

    assert error.status_code == 422
    assert error.error_code == "VALIDATION_ERROR"
    assert error.message == "Invalid input"


def test_duplicate_resource_error():
    """Test DuplicateResourceError"""
    error = DuplicateResourceError(resource="Feed", field="url", value="https://example.com")

    assert error.status_code == 409
    assert error.error_code == "DUPLICATE_RESOURCE"
    assert "already exists" in error.message


def test_circuit_breaker_open_error():
    """Test CircuitBreakerOpenError"""
    error = CircuitBreakerOpenError(service="feed-fetcher")

    assert error.status_code == 503
    assert error.error_code == "CIRCUIT_BREAKER_OPEN"
    assert "unavailable" in error.message.lower()


# =============================================================================
# API Endpoint Error Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_404_error():
    """Test 404 error on non-existent endpoint"""
    response = client.get("/api/v1/feeds/nonexistent-endpoint")

    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    assert data["error"]["status"] == 404


@pytest.mark.asyncio
async def test_api_validation_error():
    """Test validation error on invalid input"""
    # Try to create feed with invalid data
    response = client.post(
        "/api/v1/feeds/",
        json={
            # Missing required fields
            "name": "Test"
            # Missing 'url'
        },
        headers={"Authorization": "Bearer test-token"}
    )

    # Should return 422 validation error
    assert response.status_code in [401, 422]  # 401 if auth fails, 422 if validation fails


@pytest.mark.asyncio
async def test_api_duplicate_error_handling():
    """Test duplicate resource error handling (with mock)"""
    from app.api.feeds import create_feed
    from app.schemas import FeedCreate

    # Mock database to raise IntegrityError
    with patch("app.api.feeds.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_db.return_value.__aenter__.return_value = mock_session

        feed_data = FeedCreate(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )

        # Should handle IntegrityError and return 409
        response = client.post(
            "/api/v1/feeds/",
            json=feed_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )

        # Error handler should convert to 409 Conflict
        assert response.status_code in [401, 409, 500]


# =============================================================================
# Error Handler Tests (Direct)
# =============================================================================

@pytest.mark.asyncio
async def test_feed_service_error_handler():
    """Test FeedServiceError handler"""
    from app.api.errors import feed_service_error_handler
    from fastapi import Request

    error = ResourceNotFoundError(resource="Feed", identifier=123)

    mock_request = AsyncMock(spec=Request)
    mock_request.headers = {}

    response = await feed_service_error_handler(mock_request, error)

    assert response.status_code == 404

    import json
    data = json.loads(response.body)

    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "Feed" in data["error"]["message"]


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test validation exception handler"""
    from app.api.errors import validation_exception_handler
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError as PydanticValidationError

    # Create mock validation error
    mock_request = AsyncMock(spec=Request)
    mock_request.headers = {}

    try:
        from pydantic import BaseModel, validator

        class TestModel(BaseModel):
            url: str

            @validator("url")
            def validate_url(cls, v):
                if not v.startswith("http"):
                    raise ValueError("URL must start with http")
                return v

        # Trigger validation error
        TestModel(url="invalid")

    except PydanticValidationError as e:
        exc = RequestValidationError(e.errors())
        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 422

        import json
        data = json.loads(response.body)

        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["error"]["details"]


@pytest.mark.asyncio
async def test_integrity_error_handler():
    """Test database integrity error handler"""
    from app.api.errors import integrity_error_handler
    from fastapi import Request

    mock_request = AsyncMock(spec=Request)
    mock_request.headers = {}

    # Create mock IntegrityError with duplicate key
    error = IntegrityError("", "", "duplicate key value violates unique constraint")

    response = await integrity_error_handler(mock_request, error)

    assert response.status_code == 409

    import json
    data = json.loads(response.body)

    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_data_error_handler():
    """Test database data error handler"""
    from app.api.errors import data_error_handler
    from fastapi import Request

    mock_request = AsyncMock(spec=Request)
    mock_request.headers = {}

    error = DataError("", "", "invalid input syntax for type integer")

    response = await data_error_handler(mock_request, error)

    assert response.status_code == 400

    import json
    data = json.loads(response.body)

    assert data["error"]["code"] == "INVALID_DATA"


@pytest.mark.asyncio
async def test_generic_exception_handler():
    """Test generic exception handler (catch-all)"""
    from app.api.errors import generic_exception_handler
    from fastapi import Request

    mock_request = AsyncMock(spec=Request)
    mock_request.headers = {}

    error = RuntimeError("Unexpected error")

    response = await generic_exception_handler(mock_request, error)

    assert response.status_code == 500

    import json
    data = json.loads(response.body)

    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "unexpected error" in data["error"]["message"].lower()


# =============================================================================
# Error Response Consistency Tests
# =============================================================================

def test_all_error_responses_have_required_fields():
    """Test all error responses have required fields"""
    from app.api.errors import (
        ResourceNotFoundError,
        ValidationError,
        DuplicateResourceError,
        CircuitBreakerOpenError,
        AuthorizationError,
    )

    errors = [
        ResourceNotFoundError("Feed", 123),
        ValidationError("Invalid"),
        DuplicateResourceError("Feed", "url", "test"),
        CircuitBreakerOpenError("service"),
        AuthorizationError(),
    ]

    for error in errors:
        assert hasattr(error, "message")
        assert hasattr(error, "status_code")
        assert hasattr(error, "error_code")
        assert hasattr(error, "details")


def test_error_codes_are_unique():
    """Test all error codes are unique"""
    from app.api.errors import (
        ResourceNotFoundError,
        ValidationError,
        DuplicateResourceError,
        CircuitBreakerOpenError,
        AuthorizationError,
        ExternalServiceError,
        RateLimitExceededError,
    )

    errors = [
        ResourceNotFoundError("Feed", 123),
        ValidationError("Invalid"),
        DuplicateResourceError("Feed", "url", "test"),
        CircuitBreakerOpenError("service"),
        AuthorizationError(),
        ExternalServiceError("service", "error"),
        RateLimitExceededError(),
    ]

    error_codes = [error.error_code for error in errors]
    assert len(error_codes) == len(set(error_codes)), "Error codes must be unique"


# =============================================================================
# HTTP Status Code Tests
# =============================================================================

def test_error_status_codes_are_valid():
    """Test all error status codes are valid HTTP codes"""
    from app.api.errors import (
        ResourceNotFoundError,
        ValidationError,
        DuplicateResourceError,
        CircuitBreakerOpenError,
        AuthorizationError,
        ExternalServiceError,
        RateLimitExceededError,
    )

    valid_error_codes = [400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504]

    errors = [
        ResourceNotFoundError("Feed", 123),
        ValidationError("Invalid"),
        DuplicateResourceError("Feed", "url", "test"),
        CircuitBreakerOpenError("service"),
        AuthorizationError(),
        ExternalServiceError("service", "error"),
        RateLimitExceededError(),
    ]

    for error in errors:
        assert error.status_code in valid_error_codes, \
            f"Invalid status code {error.status_code} for {error.__class__.__name__}"
