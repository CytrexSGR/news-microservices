"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.clients import (
    AnalyticsClient,
    PredictionClient,
    ExecutionClient,
)
from app.mcp import MCPProtocolHandler
import app.main as main_module


@pytest_asyncio.fixture
async def client():
    """Test client fixture with lifespan initialization."""
    # Initialize clients
    analytics_client = AnalyticsClient()
    prediction_client = PredictionClient()
    execution_client = ExecutionClient()

    # Initialize MCP handler
    mcp_handler = MCPProtocolHandler(
        analytics_client=analytics_client,
        prediction_client=prediction_client,
        execution_client=execution_client,
    )

    # Set global handler for endpoints to use
    main_module.mcp_handler = mcp_handler

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await analytics_client.close()
    await prediction_client.close()
    await execution_client.close()


@pytest.fixture
def sample_article_id():
    """Sample article ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_entity():
    """Sample entity for testing."""
    return {
        "entity_name": "Elon Musk",
        "entity_type": "PERSON",
    }
