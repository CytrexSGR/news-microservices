"""Tests for MCP Protocol endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mcp-intelligence-server"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MCP Intelligence Server"
    assert "endpoints" in data
    assert "backend_services" in data


@pytest.mark.asyncio
async def test_list_tools(client: AsyncClient):
    """Test /mcp/tools/list endpoint."""
    response = await client.get("/mcp/tools/list")
    assert response.status_code == 200

    data = response.json()
    assert "tools" in data
    assert "server" in data
    assert "total_tools" in data
    assert data["server"] == "mcp-intelligence-server"

    # Verify expected tools exist
    tool_names = [tool["name"] for tool in data["tools"]]
    expected_tools = [
        "analyze_article",
        "extract_entities",
        "get_analysis_status",
        "canonicalize_entity",
        "get_entity_clusters",
        "detect_intelligence_patterns",
        "analyze_graph_quality",
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Tool {expected_tool} not found in registry"

    # Verify tool structure
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "service" in tool
        assert "category" in tool


@pytest.mark.asyncio
async def test_call_tool_invalid(client: AsyncClient):
    """Test calling non-existent tool."""
    response = await client.post(
        "/mcp/tools/call",
        json={"tool_name": "nonexistent_tool", "arguments": {}},
    )
    assert response.status_code == 200  # Returns 200 but with error in result

    data = response.json()
    assert data["tool_name"] == "nonexistent_tool"
    assert data["result"]["success"] is False
    assert "not found" in data["result"]["error"].lower()


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test Prometheus metrics endpoint."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Check for expected metrics
    content = response.text
    assert "mcp_tool_calls_total" in content
    assert "mcp_tool_duration_seconds" in content
