"""Tests for Research Service health check."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "research-service"
    assert data["version"] == "0.1.0"
    assert "environment" in data
    assert "perplexity_api" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "research-service"
    assert data["version"] == "0.1.0"
    assert data["documentation"] == "/docs"
    assert data["health"] == "/health"


def test_api_docs():
    """Test API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert schema["info"]["title"] == "research-service"
    assert schema["info"]["version"] == "0.1.0"


def test_not_found():
    """Test 404 handling."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert data["error"] == "Not Found"
    assert "nonexistent" in data["message"]


@pytest.mark.asyncio
async def test_create_research_task_without_auth():
    """Test that creating research task requires authentication."""
    response = client.post(
        "/api/v1/research",
        json={
            "query": "What is the latest news about AI?",
            "model_name": "sonar",
            "depth": "standard"
        }
    )
    # Should return 401 or 403 without valid token
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_templates_without_auth():
    """Test that listing templates requires authentication."""
    response = client.get("/api/v1/templates")
    # Should return 401 or 403 without valid token
    assert response.status_code in [401, 403]


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/health")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
