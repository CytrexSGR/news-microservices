"""
Pytest configuration and fixtures for search-service tests.

Supports two test modes:
1. Default (SQLite) - Fast, no external dependencies
2. PostgreSQL (--postgresql flag) - Full PostgreSQL features with testcontainers
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Optional
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.auth import get_optional_user
from app.models.search import ArticleIndex

# Disable PostgreSQL-specific features for SQLite tests
os.environ['ENABLE_FUZZY_SEARCH'] = 'false'


# Use SQLite for tests (faster and no external dependencies)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async SQLite engine for testing
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Also keep sync engine for database setup
sync_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Check if using PostgreSQL (for conditional test skipping)
IS_POSTGRESQL = sync_engine.dialect.name == 'postgresql'
IS_SQLITE = sync_engine.dialect.name == 'sqlite'


async def override_get_db():
    """Override database dependency for tests with async session."""
    async with AsyncTestingSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


def mock_get_optional_user() -> Optional[dict]:
    """
    Mock auth dependency for tests.

    Returns a test user instead of requiring valid JWT token.
    This allows tests to pass without authentication.
    """
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "user"
    }


# Override auth dependency for all tests
app.dependency_overrides[get_optional_user] = mock_get_optional_user


@pytest.fixture(autouse=True)
def setup_sqlite_db(request):
    """
    Auto-override get_db for SQLite tests.

    Only runs for non-PostgreSQL tests to avoid conflicts.
    """
    # Skip for PostgreSQL tests
    if "postgresql" in request.keywords:
        yield  # Still need to yield even if skipping
        return

    # Override for SQLite tests
    app.dependency_overrides[get_db] = override_get_db
    yield
    # Cleanup
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


# Mock Redis client to avoid connection issues in tests
class MockRedisClient:
    """Mock Redis client that doesn't require actual Redis connection."""

    async def get(self, key: str):
        """Always return None (cache miss)."""
        return None

    async def set(self, key: str, value: str, ex: int = None):
        """No-op set."""
        pass

    async def setex(self, key: str, time: int, value: str):
        """No-op setex."""
        pass

    async def delete(self, *keys):
        """No-op delete."""
        pass

    async def close(self):
        """No-op close."""
        pass


async def mock_get_redis_client():
    """Return mock Redis client for tests."""
    return MockRedisClient()


# Patch Redis client getter
import app.core.redis_client as redis_client
redis_client.get_redis_client = mock_get_redis_client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Setup test database schema.

    Creates all tables before tests run and drops them after.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """
    Create a fresh database session for each test.

    Yields an async session and ensures rollback after test.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client.

    This client can be used to make HTTP requests to the API.
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def sample_articles(db_session: AsyncSession):
    """
    Create sample articles for testing.

    Inserts test articles into the database for search tests.
    Note: SQLite doesn't support TSVECTOR, so we skip that for tests.
    """
    articles = [
        ArticleIndex(
            article_id="art1",
            title="Python Programming Tutorial",
            content="Learn Python programming with this comprehensive tutorial covering basics to advanced topics.",
            author="John Doe",
            source="TechBlog",
            url="https://example.com/python-tutorial",
            sentiment="positive",
        ),
        ArticleIndex(
            article_id="art2",
            title="JavaScript Async/Await Guide",
            content="Master asynchronous JavaScript with async/await patterns and promises.",
            author="Jane Smith",
            source="DevNews",
            url="https://example.com/js-async",
            sentiment="neutral",
        ),
        ArticleIndex(
            article_id="art3",
            title="Database Design Best Practices",
            content="Learn database design principles and normalization techniques for efficient data storage.",
            author="Bob Johnson",
            source="DataScience",
            url="https://example.com/db-design",
            sentiment="positive",
        ),
    ]

    for article in articles:
        db_session.add(article)

    await db_session.commit()

    # Refresh to load generated IDs
    for article in articles:
        await db_session.refresh(article)

    return articles


@pytest_asyncio.fixture(autouse=True)
async def reset_db(db_session: AsyncSession):
    """
    Clean database before each test.

    Ensures tests start with a clean slate.
    """
    yield
    # Cleanup after each test
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()


# ============================================================================
# PostgreSQL Test Container Support (--postgresql flag required)
# ============================================================================

# Global PostgreSQL container (session-scoped)
_postgres_container = None
_postgres_async_engine = None
_PostgresAsyncTestingSessionLocal = None


@pytest.fixture(scope="session")
def postgres_container(request):
    """
    Start PostgreSQL container for testing.

    This fixture is session-scoped, so the container runs once for all tests.
    Requires testcontainers package and Docker access.

    Note: Only works when run from host system, not inside Docker container.
    """
    # Skip if not running PostgreSQL tests
    if not request.config.getoption("--postgresql"):
        pytest.skip("PostgreSQL container only available with --postgresql flag")

    global _postgres_container

    if _postgres_container is None:
        try:
            from testcontainers.postgres import PostgresContainer
        except ImportError:
            pytest.skip("testcontainers package not installed")

        try:
            # Start PostgreSQL 16 container
            _postgres_container = PostgresContainer("postgres:16-alpine")
            _postgres_container.with_exposed_ports(5432)
            _postgres_container.start()

            # Wait for PostgreSQL to be ready
            _postgres_container.get_connection_url()
        except Exception as e:
            pytest.skip(f"Cannot start PostgreSQL container: {e}")

    yield _postgres_container

    # Cleanup is handled by pytest session end


@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Get PostgreSQL connection URL for asyncpg."""
    # testcontainers gives us psycopg2 URL, we need asyncpg
    url = postgres_container.get_connection_url()
    # Replace postgresql:// or postgresql+psycopg2:// with postgresql+asyncpg://
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    return url


@pytest_asyncio.fixture(scope="session")
async def postgres_engine(postgres_url):
    """
    Create async PostgreSQL engine for testing.

    This engine is session-scoped and shared across all tests.
    """
    global _postgres_async_engine, _PostgresAsyncTestingSessionLocal

    if _postgres_async_engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        _postgres_async_engine = create_async_engine(
            postgres_url,
            echo=False,
            pool_pre_ping=True,
        )

        _PostgresAsyncTestingSessionLocal = async_sessionmaker(
            _postgres_async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create all tables
        async with _postgres_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield _postgres_async_engine

    # Cleanup is handled by pytest session end


@pytest_asyncio.fixture
async def postgres_session(postgres_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh PostgreSQL database session for each test.

    Automatically rolls back after each test to ensure isolation.
    """
    async with _PostgresAsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def cleanup_postgres(postgres_engine):
    """
    Clean database after each PostgreSQL test.

    Only used for tests marked with @pytest.mark.postgresql.
    Use explicitly in PostgreSQL tests, not autouse.
    """
    yield

    # Cleanup after each test
    async with _PostgresAsyncTestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


def pytest_addoption(parser):
    """Add --postgresql option to pytest."""
    parser.addoption(
        "--postgresql",
        action="store_true",
        default=False,
        help="Run tests with PostgreSQL container (slower but more realistic)"
    )


def pytest_configure(config):
    """Register postgresql marker."""
    config.addinivalue_line(
        "markers", "postgresql: mark test to run only with PostgreSQL container"
    )


def pytest_collection_modifyitems(config, items):
    """Skip PostgreSQL tests if --postgresql flag not provided."""
    if not config.getoption("--postgresql"):
        skip_postgres = pytest.mark.skip(reason="Use --postgresql to run PostgreSQL integration tests")
        for item in items:
            if "postgresql" in item.keywords:
                item.add_marker(skip_postgres)
