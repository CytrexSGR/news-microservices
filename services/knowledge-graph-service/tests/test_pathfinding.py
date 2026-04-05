"""
Tests for Pathfinding Endpoint

Tests the graph pathfinding functionality.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_pathfinding_basic():
    """Test basic pathfinding between two entities."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"max_depth": 3, "limit": 3}
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "paths" in data
    assert "shortest_path_length" in data
    assert "query_time_ms" in data
    assert "total_paths_found" in data
    assert data["entity1"] == "Trump"
    assert data["entity2"] == "Tesla"
    assert data["max_depth"] == 3


@pytest.mark.asyncio
async def test_pathfinding_with_params():
    """Test pathfinding with custom parameters."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"max_depth": 2, "limit": 5, "min_confidence": 0.7}
        )

    assert response.status_code == 200
    data = response.json()

    assert data["max_depth"] == 2
    assert len(data["paths"]) <= 5

    # Verify all relationships have confidence >= 0.7
    for path in data["paths"]:
        for rel in path["relationships"]:
            assert rel["confidence"] >= 0.7


@pytest.mark.asyncio
async def test_pathfinding_nonexistent_entity():
    """Test pathfinding with non-existent entity."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/path/NonExistentEntity/Tesla"
        )

    assert response.status_code == 200
    data = response.json()

    # Should return empty paths
    assert data["paths"] == []
    assert data["total_paths_found"] == 0
    assert data["shortest_path_length"] == 0


@pytest.mark.asyncio
async def test_pathfinding_response_model():
    """Test that response matches PathfindingResponse model."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/graph/path/Trump/Tesla")

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields
    required_fields = [
        "paths", "shortest_path_length", "query_time_ms",
        "entity1", "entity2", "max_depth", "total_paths_found"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Verify path structure
    if data["paths"]:
        path = data["paths"][0]
        assert "length" in path
        assert "nodes" in path
        assert "relationships" in path

        # Verify node structure
        if path["nodes"]:
            node = path["nodes"][0]
            assert "name" in node
            assert "type" in node

        # Verify relationship structure
        if path["relationships"]:
            rel = path["relationships"][0]
            assert "type" in rel
            assert "confidence" in rel
            assert 0.0 <= rel["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_pathfinding_max_depth_validation():
    """Test that max_depth parameter is validated."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test max_depth too high
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"max_depth": 10}
        )
        assert response.status_code == 422  # Validation error

        # Test max_depth too low
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"max_depth": 0}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_pathfinding_limit_validation():
    """Test that limit parameter is validated."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test limit too high
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"limit": 20}
        )
        assert response.status_code == 422

        # Test limit too low
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"limit": 0}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_pathfinding_path_ordering():
    """Test that paths are ordered by length (shortest first)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/graph/path/Trump/Tesla",
            params={"max_depth": 5, "limit": 10}
        )

    assert response.status_code == 200
    data = response.json()

    if len(data["paths"]) > 1:
        # Verify paths are sorted by length
        for i in range(len(data["paths"]) - 1):
            assert data["paths"][i]["length"] <= data["paths"][i + 1]["length"]


@pytest.mark.asyncio
async def test_pathfinding_query_time():
    """Test that query_time_ms is reasonable."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/graph/path/Trump/Tesla")

    assert response.status_code == 200
    data = response.json()

    # Query should complete in reasonable time (< 5 seconds)
    assert data["query_time_ms"] < 5000
    assert data["query_time_ms"] > 0
