"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.clients import (
    ContentAnalysisClient,
    EntityCanonClient,
    OSINTClient,
    IntelligenceClient,
    NarrativeClient,
)
from app.mcp import MCPProtocolHandler
import app.main as main_module


@pytest_asyncio.fixture
async def client():
    """Test client fixture with lifespan initialization."""
    # Initialize clients
    content_analysis_client = ContentAnalysisClient()
    entity_canon_client = EntityCanonClient()
    osint_client = OSINTClient()
    intelligence_client = IntelligenceClient()
    narrative_client = NarrativeClient()

    # Initialize MCP handler
    mcp_handler = MCPProtocolHandler(
        content_analysis_client=content_analysis_client,
        entity_canon_client=entity_canon_client,
        osint_client=osint_client,
        intelligence_client=intelligence_client,
        narrative_client=narrative_client,
    )

    # Set global handler for endpoints to use
    main_module.mcp_handler = mcp_handler

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await content_analysis_client.close()
    await entity_canon_client.close()
    await osint_client.close()
    await intelligence_client.close()
    await narrative_client.close()


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
