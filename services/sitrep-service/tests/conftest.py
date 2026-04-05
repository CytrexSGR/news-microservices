# services/sitrep-service/tests/conftest.py
"""Shared pytest fixtures for sitrep-service tests.

Provides common fixtures used across test modules:
- Database fixtures (async engine, session, session maker)
- Auth fixtures (JWT tokens, headers)
- Sample data factories (sitreps, stories)
- Mock objects (aggregator, LLM responses)

Usage:
    Tests automatically have access to these fixtures without importing.

    def test_example(async_session, sample_sitrep):
        # async_session is ready to use
        # sample_sitrep is a SitrepResponse object
        pass
"""

from datetime import date, datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.sitrep import Base, SitrepReport
from app.repositories.sitrep_repository import SitrepRepository
from app.schemas.sitrep import (
    KeyDevelopment,
    RiskAssessment,
    SitrepResponse,
)
from app.schemas.story import TopStory
from app.services.story_aggregator import StoryAggregator


# ============================================================
# Database Fixtures
# ============================================================


@pytest_asyncio.fixture
async def async_engine():
    """Create async SQLite engine for testing.

    Uses in-memory SQLite for fast, isolated test execution.
    Tables are created fresh for each test session.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing.

    Provides a database session that automatically rolls back after each test.
    """
    session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def session_maker(async_engine):
    """Create session maker for dependency injection.

    Useful when testing components that need to create their own sessions.
    """
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# ============================================================
# Repository Fixtures
# ============================================================


@pytest.fixture
def repository() -> SitrepRepository:
    """Create SitrepRepository instance."""
    return SitrepRepository()


# ============================================================
# Auth Fixtures
# ============================================================


@pytest.fixture
def valid_jwt_token() -> str:
    """Create a valid JWT token for testing.

    Token is valid for 1 hour from creation time.
    """
    payload = {
        "sub": "test-user-id",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def auth_headers(valid_jwt_token) -> dict:
    """Create authorization headers with valid JWT token."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def expired_jwt_token() -> str:
    """Create an expired JWT token for testing auth failures."""
    payload = {
        "sub": "test-user-id",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ============================================================
# Sample Data Fixtures
# ============================================================


@pytest.fixture
def sample_sitrep() -> SitrepResponse:
    """Create a fully populated sample SITREP response for testing."""
    return SitrepResponse(
        id=uuid4(),
        report_date=date.today(),
        report_type="daily",
        title="Daily Intelligence Briefing - Test",
        executive_summary="Test executive summary with key findings.",
        content_markdown="# Test SITREP\n\nTest content in markdown.",
        content_html="<h1>Test SITREP</h1><p>Test content.</p>",
        key_developments=[
            KeyDevelopment(
                title="Test Development",
                summary="A significant test development occurred.",
                significance="High impact on testing.",
                risk_assessment=RiskAssessment(
                    level="medium",
                    category="operational",
                    description="Test risk",
                    likelihood=0.5,
                    impact=5.0,
                ),
                related_entities=["TestEntity"],
            )
        ],
        top_stories=[
            {
                "cluster_id": str(uuid4()),
                "title": "Test Story",
                "article_count": 5,
                "tension_score": 0.75,
                "is_breaking": False,
                "category": "default",
            }
        ],
        key_entities=[
            {"name": "TestOrg", "type": "organization", "mention_count": 10}
        ],
        sentiment_summary={
            "overall": "neutral",
            "positive_percent": 30.0,
            "negative_percent": 25.0,
            "neutral_percent": 45.0,
        },
        emerging_signals=[
            {
                "signal_type": "trend",
                "description": "Test trend detected",
                "confidence": 0.8,
            }
        ],
        generation_model="gpt-4-turbo-preview",
        generation_time_ms=1500,
        prompt_tokens=1000,
        completion_tokens=500,
        articles_analyzed=50,
        confidence_score=0.85,
        human_reviewed=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_stories() -> list[TopStory]:
    """Create sample TopStory objects for testing."""
    now = datetime.now(timezone.utc)
    return [
        TopStory(
            cluster_id=uuid4(),
            title="Breaking: Major Market Event",
            article_count=15,
            first_seen_at=now - timedelta(hours=1),
            last_updated_at=now,
            tension_score=8.5,
            relevance_score=0.95,
            is_breaking=True,
            category="breaking_news",
            top_entities=["NYSE", "Fed"],
        ),
        TopStory(
            cluster_id=uuid4(),
            title="Tech Company Earnings Report",
            article_count=8,
            first_seen_at=now - timedelta(hours=3),
            last_updated_at=now - timedelta(hours=1),
            tension_score=6.0,
            relevance_score=0.75,
            is_breaking=False,
            category="technology",
            top_entities=["TechCorp", "Q4"],
        ),
        TopStory(
            cluster_id=uuid4(),
            title="Geopolitical Analysis: Trade Relations",
            article_count=5,
            first_seen_at=now - timedelta(hours=6),
            last_updated_at=now - timedelta(hours=2),
            tension_score=5.0,
            relevance_score=0.65,
            is_breaking=False,
            category="geopolitics",
            top_entities=["EU", "US"],
        ),
    ]


# ============================================================
# Factory Functions
# ============================================================


def create_sample_sitrep(
    report_date: date = None,
    report_type: str = "daily",
    title: str = "Test SITREP",
) -> SitrepResponse:
    """Factory function to create test SITREP responses.

    Args:
        report_date: Date for the report (defaults to today)
        report_type: Type of report (daily, weekly, breaking)
        title: Report title

    Returns:
        SitrepResponse with test data
    """
    return SitrepResponse(
        id=uuid4(),
        report_date=report_date or date.today(),
        report_type=report_type,
        title=title,
        executive_summary="Test summary",
        content_markdown="# Test\n\nContent",
        top_stories=[{"title": "Story", "count": 3}],
        key_entities=[{"name": "Entity", "type": "org"}],
        sentiment_summary={"overall": "neutral"},
        generation_model="test-model",
        generation_time_ms=100,
        articles_analyzed=10,
        created_at=datetime.now(timezone.utc),
    )


def create_sample_story(
    title: str = "Test Story",
    article_count: int = 5,
    is_breaking: bool = False,
    tension_score: float = 5.0,
) -> TopStory:
    """Factory function to create test TopStory objects.

    Args:
        title: Story title
        article_count: Number of articles in cluster
        is_breaking: Whether story is breaking news
        tension_score: Story tension score (0-10)

    Returns:
        TopStory with test data
    """
    now = datetime.now(timezone.utc)
    return TopStory(
        cluster_id=uuid4(),
        title=title,
        article_count=article_count,
        first_seen_at=now - timedelta(hours=2),
        last_updated_at=now,
        tension_score=tension_score,
        relevance_score=0.75,
        is_breaking=is_breaking,
        category="default",
        top_entities=["Entity1", "Entity2"],
    )


# ============================================================
# Mock Fixtures
# ============================================================


@pytest.fixture
def mock_aggregator() -> StoryAggregator:
    """Create a StoryAggregator instance for testing."""
    return StoryAggregator()


@pytest.fixture
def mock_llm_response() -> dict:
    """Standard mock LLM response for sitrep generation tests."""
    return {
        "executive_summary": "Test executive summary for unit testing.",
        "key_developments": [
            {
                "title": "Key Development 1",
                "summary": "Summary of development.",
                "significance": "High impact.",
                "risk_level": "medium",
                "risk_category": "economic",
                "related_entities": ["Entity1"],
            }
        ],
        "sentiment_analysis": {
            "overall": "neutral",
            "positive_percent": 30.0,
            "negative_percent": 25.0,
            "neutral_percent": 45.0,
            "rationale": "Mixed sentiment.",
        },
        "emerging_signals": [
            {
                "signal_type": "trend",
                "description": "Trend detected.",
                "confidence": 0.8,
                "related_entities": ["Market"],
            }
        ],
        "content_markdown": "# SITREP\n\nTest content.",
    }


# ============================================================
# Pytest Configuration
# ============================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
