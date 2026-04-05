"""
Pytest configuration and fixtures for Feed Service tests
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_async_db
from app.models.feed import Base
# Import all models so SQLAlchemy registers them with Base.metadata
from app.models.feed import Feed, FeedItem, FetchLog, FeedHealth, FeedCategory
from app.models.source import Source, SourceFeed, SourceAssessmentHistory
from app.models.intelligence import ArticleCluster, ArticleVersion, PublicationReviewQueue, SitrepReport
from app.config import settings

# Test database URL (use SQLite for tests)
# Using StaticPool to share the same connection for in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with StaticPool to share connection
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables (models are imported at module level)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Clean up tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with overridden database dependency."""

    async def override_get_db() -> AsyncSession:
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_feed_data():
    """Sample feed data for testing."""
    return {
        "name": "Test Feed",
        "url": "https://example.com/feed.xml",
        "description": "A test RSS feed",
        "fetch_interval": 60,
        "scrape_full_content": False,
        "scrape_method": "newspaper4k",
        "scrape_failure_threshold": 5,
        "categories": ["technology", "news"],
    }


@pytest.fixture
def sample_feed_update():
    """Sample feed update data."""
    return {
        "name": "Updated Feed Name",
        "description": "Updated description",
        "fetch_interval": 120,
        "is_active": False,
    }


@pytest.fixture
def mock_feed_content():
    """Mock RSS feed content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>https://example.com</link>
            <description>Test RSS feed</description>
            <item>
                <title>Test Article 1</title>
                <link>https://example.com/article1</link>
                <description>This is the first test article</description>
                <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
                <guid>article-1</guid>
            </item>
            <item>
                <title>Test Article 2</title>
                <link>https://example.com/article2</link>
                <description>This is the second test article</description>
                <pubDate>Mon, 01 Jan 2024 13:00:00 +0000</pubDate>
                <guid>article-2</guid>
            </item>
        </channel>
    </rss>
    """


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""
    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def utcnow(cls):
            return datetime(2024, 1, 1, 12, 0, 0)

    monkeypatch.setattr("app.services.feed_fetcher.datetime", MockDatetime)
    monkeypatch.setattr("app.models.feed.datetime", MockDatetime)
    return MockDatetime


# ========== Fixture Aliases (for test compatibility) ==========

@pytest_asyncio.fixture(scope="function")
async def async_client(client: TestClient) -> TestClient:
    """Alias for client (test compatibility)."""
    return client


@pytest_asyncio.fixture(scope="function")
async def db(db_session: AsyncSession) -> AsyncSession:
    """Alias for db_session (test compatibility)."""
    return db_session