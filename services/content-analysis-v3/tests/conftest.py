"""
Pytest configuration and fixtures for Content-Analysis-V3 tests
"""

import pytest
import pytest_asyncio
import asyncpg
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.providers.base import ProviderMetadata
from app.models.schemas import TriageDecision, Tier1Results, Entity, Relation, Topic


@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """Create test database connection pool."""
    pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=1,
        max_size=2
    )
    yield pool
    await pool.close()


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        "id": uuid4(),
        "title": "Test Article: Market Analysis",
        "url": "https://example.com/test-article",
        "content": """
        The Federal Reserve announced today a 0.25% interest rate increase,
        marking the third consecutive hike this year. Fed Chair Jerome Powell
        stated that the decision was made to combat persistent inflation.

        Market analysts expect this move to impact mortgage rates and consumer
        spending. Major stock indices fell 2% following the announcement.

        Economists predict the central bank will continue this policy through
        the end of the year to stabilize the economy.
        """
    }


@pytest.fixture
def mock_triage_decision():
    """Mock Tier0 triage decision."""
    return TriageDecision(
        PriorityScore=7,
        category="FINANCE",
        keep=True,
        tokens_used=800,
        cost_usd=0.00002,
        model="gemini-2.0-flash-exp"
    )


@pytest.fixture
def mock_tier1_results():
    """Mock Tier1 extraction results."""
    return Tier1Results(
        entities=[
            Entity(
                name="Federal Reserve",
                type="ORGANIZATION",
                confidence=0.95,
                mentions=2,
                aliases=["Fed"],
                role="Central Bank"
            ),
            Entity(
                name="Jerome Powell",
                type="PERSON",
                confidence=0.90,
                mentions=1,
                aliases=[],
                role="Fed Chair"
            )
        ],
        relations=[
            Relation(
                subject="Federal Reserve",
                predicate="announced",
                object="interest rate increase",
                confidence=0.95
            ),
            Relation(
                subject="Jerome Powell",
                predicate="stated",
                object="decision made to combat inflation",
                confidence=0.90
            )
        ],
        topics=[
            Topic(
                keyword="FINANCE",
                confidence=0.95,
                parent_category="Economic Policy"
            ),
            Topic(
                keyword="POLITICS",
                confidence=0.70,
                parent_category="Government"
            )
        ],
        impact_score=7.5,
        credibility_score=8.0,
        urgency_score=6.5,
        tokens_used=2000,
        cost_usd=0.00007,
        model="gemini-2.0-flash-exp"
    )


@pytest.fixture
def mock_provider():
    """Mock LLM provider for testing."""
    provider = AsyncMock()

    # Configure generate method
    async def mock_generate(prompt, max_tokens, response_format=None, temperature=0.0):
        if response_format == TriageDecision:
            response = """{
                "PriorityScore": 7,
                "category": "FINANCE",
                "keep": true
            }"""
        else:
            response = """{
                "entities": [
                    {
                        "name": "Federal Reserve",
                        "type": "ORGANIZATION",
                        "confidence": 0.95,
                        "mentions": 2,
                        "aliases": ["Fed"],
                        "role": "Central Bank"
                    }
                ],
                "relations": [
                    {
                        "subject": "Federal Reserve",
                        "predicate": "announced",
                        "object": "interest rate increase",
                        "confidence": 0.95
                    }
                ],
                "topics": [
                    {
                        "keyword": "FINANCE",
                        "confidence": 0.95,
                        "parent_category": "Economic Policy"
                    }
                ],
                "impact_score": 7.5,
                "credibility_score": 8.0,
                "urgency_score": 6.5
            }"""

        metadata = ProviderMetadata(
            tokens_used=1000,
            cost_usd=0.00003,
            model="gemini-2.0-flash-exp",
            latency_ms=500,
            provider="gemini"
        )

        return response, metadata

    provider.generate = mock_generate
    provider.calculate_cost = MagicMock(return_value=0.00003)

    return provider


@pytest_asyncio.fixture
async def clean_test_data(db_pool):
    """Clean up test data after each test."""
    yield

    # Cleanup after test
    async with db_pool.acquire() as conn:
        # Delete test data (be careful in production!)
        await conn.execute("DELETE FROM tier1_topics WHERE article_id IN (SELECT article_id FROM tier1_scores WHERE model LIKE '%test%')")
        await conn.execute("DELETE FROM tier1_relations WHERE article_id IN (SELECT article_id FROM tier1_scores WHERE model LIKE '%test%')")
        await conn.execute("DELETE FROM tier1_entities WHERE article_id IN (SELECT article_id FROM tier1_scores WHERE model LIKE '%test%')")
        await conn.execute("DELETE FROM tier1_scores WHERE model LIKE '%test%'")
        await conn.execute("DELETE FROM triage_decisions WHERE model LIKE '%test%'")
