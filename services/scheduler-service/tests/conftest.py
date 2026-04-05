"""
Pytest configuration and shared fixtures for scheduler service tests.

Provides common test fixtures for:
- Database sessions (with transaction rollback)
- HTTP clients (mocked)
- APScheduler instances
- RabbitMQ connections (mocked)
- Redis clients (mocked)
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.core.config import Settings
from database.models import Base, AnalysisJobQueue, JobType, JobStatus, FeedScheduleState


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test configuration with overrides"""
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",  # Test DB
        RABBITMQ_URL="amqp://guest:guest@localhost:5672/test",
        FEED_CHECK_INTERVAL=1,  # Fast for testing
        JOB_PROCESS_INTERVAL=1,
        MAX_CONCURRENT_JOBS=5,
        CIRCUIT_BREAKER_THRESHOLD=3,
        CIRCUIT_BREAKER_TIMEOUT=30,
    )


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db_engine(test_settings):
    """
    Create a test database engine.

    Uses SQLite in-memory database for fast tests.
    Each test function gets a fresh database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a test database session with automatic rollback.

    Each test gets a fresh session that rolls back after the test.
    This ensures test isolation.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_http_client():
    """Mock httpx.AsyncClient for testing HTTP calls"""
    client = AsyncMock()

    # Default successful responses
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.aclose = AsyncMock()

    return client


@pytest.fixture
def mock_feed_service_response():
    """Mock response from feed service"""
    return [
        {
            "id": "feed-123",
            "url": "https://example.com/feed.xml",
            "category": "finance",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "feed-456",
            "url": "https://example.com/feed2.xml",
            "category": "geopolitics",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]


@pytest.fixture
def mock_articles_response():
    """Mock response from feed service articles endpoint"""
    return [
        {
            "id": "article-123",
            "title": "Test Article 1",
            "url": "https://example.com/article1",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "content": "Test content 1"
        },
        {
            "id": "article-456",
            "title": "Test Article 2",
            "url": "https://example.com/article2",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "content": "Test content 2"
        }
    ]


# ============================================================================
# APScheduler Fixtures
# ============================================================================

@pytest.fixture
def mock_apscheduler():
    """Mock APScheduler for testing scheduled jobs"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    # Don't start the scheduler in tests
    scheduler.start = MagicMock()
    scheduler.shutdown = MagicMock()
    scheduler.add_job = MagicMock()
    scheduler.remove_job = MagicMock()
    scheduler.pause_job = MagicMock()
    scheduler.resume_job = MagicMock()
    scheduler.get_jobs = MagicMock(return_value=[])

    return scheduler


# ============================================================================
# RabbitMQ Fixtures
# ============================================================================

@pytest.fixture
async def mock_rabbitmq_connection():
    """Mock RabbitMQ connection for testing"""
    connection = AsyncMock()
    connection.is_closed = False
    connection.channel = AsyncMock()

    channel = AsyncMock()
    channel.declare_exchange = AsyncMock()
    channel.exchange = AsyncMock()

    connection.channel.return_value = channel

    return connection


@pytest.fixture
def mock_rabbitmq_message():
    """Mock RabbitMQ message"""
    message = MagicMock()
    message.body = b'{"event_type": "test", "payload": {}}'
    message.delivery_tag = "test-tag-123"
    message.ack = AsyncMock()
    message.nack = AsyncMock()

    return message


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture
async def mock_redis_client():
    """Mock Redis client for testing"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock(return_value=False)
    client.expire = AsyncMock()
    client.incr = AsyncMock(return_value=1)
    client.close = AsyncMock()

    return client


# ============================================================================
# Job Queue Fixtures
# ============================================================================

@pytest.fixture
def sample_pending_job(db_session) -> AnalysisJobQueue:
    """Create a sample pending job for testing"""
    job = AnalysisJobQueue(
        feed_id="feed-123",
        article_id="article-123",
        job_type=JobType.CATEGORIZATION,
        status=JobStatus.PENDING,
        priority=10,
        max_retries=3,
        retry_count=0
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_processing_job(db_session) -> AnalysisJobQueue:
    """Create a sample processing job for testing"""
    job = AnalysisJobQueue(
        feed_id="feed-123",
        article_id="article-456",
        job_type=JobType.FINANCE_SENTIMENT,
        status=JobStatus.PROCESSING,
        priority=8,
        max_retries=3,
        retry_count=0,
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_completed_job(db_session) -> AnalysisJobQueue:
    """Create a sample completed job for testing"""
    job = AnalysisJobQueue(
        feed_id="feed-123",
        article_id="article-789",
        job_type=JobType.STANDARD_SENTIMENT,
        status=JobStatus.COMPLETED,
        priority=5,
        max_retries=3,
        retry_count=0,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_failed_job(db_session) -> AnalysisJobQueue:
    """Create a sample failed job for testing"""
    job = AnalysisJobQueue(
        feed_id="feed-123",
        article_id="article-999",
        job_type=JobType.OSINT_ANALYSIS,
        status=JobStatus.FAILED,
        priority=7,
        max_retries=3,
        retry_count=3,
        error_message="Test error: API timeout",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


# ============================================================================
# Feed Monitor Fixtures
# ============================================================================

@pytest.fixture
def sample_feed_schedule_state(db_session) -> FeedScheduleState:
    """Create a sample feed schedule state for testing"""
    state = FeedScheduleState(
        feed_id="feed-123",
        last_checked_at=datetime.now(timezone.utc),
        total_articles_processed=10
    )
    db_session.add(state)
    db_session.commit()
    db_session.refresh(state)
    return state


# ============================================================================
# Time Mocking Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Fixture for freezing time in tests"""
    from freezegun import freeze_time
    return freeze_time


@pytest.fixture
def fixed_datetime():
    """Return a fixed datetime for testing"""
    return datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


# ============================================================================
# Async Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture
async def test_app():
    """Create FastAPI test application"""
    from fastapi.testclient import TestClient
    from app.main import app

    # Mock dependencies
    with patch('app.main.init_db'), \
         patch('app.main.feed_monitor.start'), \
         patch('app.main.job_processor.start'), \
         patch('app.main.cron_scheduler.start'):

        client = TestClient(app)
        yield client


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_response(status_code: int, json_data: dict = None, text: str = None):
    """Helper to create mock HTTP responses"""
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=json_data or {})
    response.text = text or ""
    response.raise_for_status = MagicMock()

    if status_code >= 400:
        from httpx import HTTPStatusError
        response.raise_for_status.side_effect = HTTPStatusError(
            f"{status_code} Error",
            request=MagicMock(),
            response=response
        )

    return response
