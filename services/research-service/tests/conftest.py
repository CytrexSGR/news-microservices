"""
Pytest configuration and fixtures for Research Service tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import redis

from app.main import app
from app.models.research import Base, ResearchTask, ResearchTemplate, ResearchCache, CostTracking
from app.core.database import get_db
from app.core.config import settings

# Create in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_perplexity_response():
    """Mock Perplexity API response."""
    return {
        "content": "This is a detailed research response about the topic. It includes comprehensive information with citations.",
        "citations": [
            {
                "url": "https://example.com/article1",
                "title": "Example Article 1",
                "snippet": "Relevant excerpt from article 1"
            },
            {
                "url": "https://example.com/article2",
                "title": "Example Article 2",
                "snippet": "Relevant excerpt from article 2"
            }
        ],
        "sources": [
            {
                "url": "https://example.com/article1",
                "title": "Example Article 1",
                "snippet": "Relevant excerpt from article 1"
            },
            {
                "url": "https://example.com/article2",
                "title": "Example Article 2",
                "snippet": "Relevant excerpt from article 2"
            }
        ],
        "tokens_used": 1500,
        "cost": 0.0075,
        "model": "sonar",
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_perplexity_client(mock_perplexity_response):
    """Mock Perplexity client."""
    with patch("app.services.perplexity.perplexity_client") as mock_client:
        mock_client.research = AsyncMock(return_value=mock_perplexity_response)
        mock_client.check_health = AsyncMock(return_value=True)
        yield mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    return mock_client


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return 1


@pytest.fixture
def auth_headers(test_user_id):
    """Mock authentication headers."""
    # Create a mock JWT token
    token = "mock.jwt.token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_auth():
    """Mock authentication dependency."""
    from app.core.auth import CurrentUser

    with patch("app.core.auth.get_current_user") as mock_get_user:
        mock_user = CurrentUser(
            user_id=1,
            email="test@example.com",
            roles=["user"]
        )
        mock_get_user.return_value = mock_user
        yield mock_get_user


@pytest.fixture
def sample_research_task(db_session, test_user_id):
    """Create a sample research task."""
    task = ResearchTask(
        user_id=test_user_id,
        query="What are the latest developments in AI?",
        model_name="sonar",
        depth="standard",
        status="completed",
        result={
            "content": "AI developments include...",
            "sources": [{"url": "https://example.com", "title": "AI News"}]
        },
        tokens_used=1500,
        cost=0.0075,
        completed_at=datetime.utcnow()
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_template(db_session, test_user_id):
    """Create a sample research template."""
    template = ResearchTemplate(
        user_id=test_user_id,
        name="News Research Template",
        description="Template for researching news topics",
        query_template="What are the latest developments in {{topic}}? Focus on {{aspect}}.",
        parameters={"topic": "string", "aspect": "string"},
        default_model="sonar",
        default_depth="standard",
        is_active=True,
        is_public=False,
        usage_count=0
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def sample_cache_entry(db_session):
    """Create a sample cache entry."""
    cache_entry = ResearchCache(
        cache_key="test_cache_key_123",
        query="Test query",
        model_name="sonar",
        depth="standard",
        result={"content": "Cached result"},
        tokens_used=1000,
        cost=0.005,
        hit_count=5,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(cache_entry)
    db_session.commit()
    db_session.refresh(cache_entry)
    return cache_entry


@pytest.fixture
def sample_cost_tracking(db_session, test_user_id):
    """Create sample cost tracking entries."""
    entries = []
    for i in range(5):
        entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow() - timedelta(days=i),
            model_name="sonar",
            tokens_used=1000 + i * 100,
            cost=0.005 + i * 0.001,
            task_id=None
        )
        db_session.add(entry)
        entries.append(entry)

    db_session.commit()
    return entries


@pytest.fixture
def disable_cost_tracking():
    """Temporarily disable cost tracking."""
    original = settings.ENABLE_COST_TRACKING
    settings.ENABLE_COST_TRACKING = False
    yield
    settings.ENABLE_COST_TRACKING = original


@pytest.fixture
def disable_cache():
    """Temporarily disable caching."""
    original = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = False
    yield
    settings.CACHE_ENABLED = original


@pytest.fixture
def mock_celery():
    """Mock Celery tasks."""
    with patch("app.workers.tasks.process_research_task") as mock_task:
        mock_task.delay.return_value = MagicMock(id="mock-task-id")
        yield mock_task


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
