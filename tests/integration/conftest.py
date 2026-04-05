"""
Pytest configuration for integration tests

Provides fixtures for:
- Database access (SQLModel Session)
- HTTP client (AsyncClient with auth)
- Redis client (async)
- WebSocket connections
- Test credentials and headers
- Test data fixtures
"""

import pytest
import sys
import asyncio
import redis.asyncio as redis
import httpx
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator, Optional
import logging

logger = logging.getLogger(__name__)

# Add services to path for model imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "feed-service"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "auth-service"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "analytics-service"))

# Try importing models
try:
    from sqlmodel import Session, SQLModel, create_engine, select
    from app.models.core import Feed, Item, FetchLog
    from app.models.feeds import Source, FeedType, FeedHealth
    from app.models.base import FeedStatus, SourceType
    from app.models.user import UserSettings
except ImportError as e:
    logger.warning(f"Could not import models: {e}")


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    # Use test database (separate from production)
    db_url = "postgresql://news_user:+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=@localhost:5432/news_mcp"

    try:
        engine = create_engine(db_url, echo=False, pool_size=5, max_overflow=10)
        return engine
    except Exception as e:
        logger.warning(f"Could not create database engine: {e}")
        pytest.skip("Database not available")


@pytest.fixture(scope="session")
def create_tables(test_engine):
    """Create all tables once per test session"""
    try:
        SQLModel.metadata.create_all(test_engine)
        yield
    except Exception as e:
        logger.warning(f"Could not create tables: {e}")
        pytest.skip("Database not available")


@pytest.fixture(scope="function")
def db_session(test_engine, create_tables):
    """Provide a clean database session for each test"""
    try:
        connection = test_engine.connect()
        transaction = connection.begin()
        session = Session(bind=connection)

        yield session

        session.close()
        transaction.rollback()
        connection.close()
    except Exception as e:
        logger.warning(f"Database session error: {e}")
        pytest.skip("Database session unavailable")


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def test_credentials() -> dict:
    """Test user credentials (from CLAUDE.md)"""
    return {
        "username": "andreas",
        "password": "Aug2012#",
        "email": "andreas@test.com"
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async HTTP client for integration tests"""
    base_url = "http://localhost:8100"  # Auth service as base

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def auth_headers(async_client: httpx.AsyncClient, test_credentials: dict) -> dict:
    """Get authentication headers for API requests"""
    try:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_credentials["username"],
                "password": test_credentials["password"]
            }
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            return {"Authorization": f"Bearer {token}"}
        else:
            logger.warning(f"Authentication failed: {response.status_code}")
            return {}
    except Exception as e:
        logger.warning(f"Could not get auth headers: {e}")
        return {}


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def redis_pool():
    """Create Redis connection pool"""
    try:
        pool = redis.ConnectionPool.from_url(
            "redis://:redis_secret_2024@localhost:6379/0",
            decode_responses=True,
            max_connections=5
        )
        yield pool
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        pytest.skip("Redis unavailable")


@pytest.fixture
async def redis_client(redis_pool):
    """Get Redis client from pool"""
    try:
        async with redis.Redis(connection_pool=redis_pool) as r:
            # Test connection
            await r.ping()
            yield r
    except Exception as e:
        logger.warning(f"Redis client error: {e}")
        pytest.skip("Redis unavailable")


# ============================================================================
# WebSocket Fixtures
# ============================================================================

@pytest.fixture
def websocket_uri() -> str:
    """WebSocket URI for analytics service"""
    return "ws://localhost:8107/ws/analytics"


@pytest.fixture
def invalid_token() -> str:
    """Invalid token for testing error handling"""
    return "invalid_token_12345"


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_source(db_session: Session):
    """Create a test source"""
    try:
        source = Source(
            name="Test Source - Integration",
            type=SourceType.RSS,
            description="Test RSS source for integration tests",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)
        return source
    except Exception as e:
        logger.warning(f"Could not create test source: {e}")
        return None


@pytest.fixture
def test_feed_type(db_session: Session):
    """Create a test feed type"""
    try:
        feed_type = FeedType(
            name="Test RSS - Integration",
            default_interval_minutes=60,
            description="Test feed type for integration",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed_type)
        db_session.commit()
        db_session.refresh(feed_type)
        return feed_type
    except Exception as e:
        logger.warning(f"Could not create test feed type: {e}")
        return None


@pytest.fixture
def test_feed(db_session: Session, test_source: Source, test_feed_type: FeedType):
    """Create a test feed"""
    try:
        feed = Feed(
            url="https://example.com/test-feed-integration.rss",
            title="Test Feed - Integration",
            description="Test feed for integration tests",
            status=FeedStatus.ACTIVE,
            fetch_interval_minutes=60,
            source_id=test_source.id if test_source else 1,
            feed_type_id=test_feed_type.id if test_feed_type else 1,
            auto_analyze_enabled=False,
            health_score=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed)
        db_session.commit()
        db_session.refresh(feed)
        return feed
    except Exception as e:
        logger.warning(f"Could not create test feed: {e}")
        return None


@pytest.fixture
def derstandard_feed(db_session: Session):
    """Get or create Der Standard feed for testing"""
    try:
        # Try to get existing feed
        feed = db_session.exec(
            select(Feed).where(Feed.url == "https://www.derstandard.at/rss")
        ).first()

        if feed:
            return feed

        # Create new feed if not exists
        source = Source(
            name="Der Standard",
            type=SourceType.RSS,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)

        feed_type = FeedType(
            name="RSS Feed",
            default_interval_minutes=15,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed_type)
        db_session.commit()
        db_session.refresh(feed_type)

        feed = Feed(
            url="https://www.derstandard.at/rss",
            title="Der Standard",
            status=FeedStatus.ACTIVE,
            fetch_interval_minutes=15,
            source_id=source.id,
            feed_type_id=feed_type.id,
            auto_analyze_enabled=True,
            health_score=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(feed)
        db_session.commit()
        db_session.refresh(feed)
        return feed

    except Exception as e:
        logger.warning(f"Could not get/create Der Standard feed: {e}")
        return None


# ============================================================================
# Service Base URLs
# ============================================================================

class ServiceUrls:
    """Service endpoints for integration tests"""
    AUTH = "http://localhost:8100"
    FEED = "http://localhost:8101"
    CONTENT_ANALYSIS = "http://localhost:8102"
    RESEARCH = "http://localhost:8103"
    OSINT = "http://localhost:8104"
    NOTIFICATION = "http://localhost:8105"
    SEARCH = "http://localhost:8106"
    ANALYTICS = "http://localhost:8107"
    SCHEDULER = "http://localhost:8108"
    FMP = "http://localhost:8109"
    KNOWLEDGE_GRAPH = "http://localhost:8111"
    ENTITY_CANONICALIZATION = "http://localhost:8112"
    LLM_ORCHESTRATOR = "http://localhost:8113"
    PREDICTION = "http://localhost:8116"


@pytest.fixture
def service_urls() -> ServiceUrls:
    """Provide service URLs"""
    return ServiceUrls()


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    # Markers for test categorization
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>5s)"
    )


@pytest.fixture(scope="session", autouse=True)
def log_test_start():
    """Log test session start"""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST SUITE STARTING")
    logger.info("=" * 70)
    yield
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST SUITE COMPLETE")
    logger.info("=" * 70)
