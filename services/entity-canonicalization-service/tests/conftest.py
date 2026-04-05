"""Pytest configuration and fixtures for entity-canonicalization-service tests."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.dependencies import get_db_session
from app.database.models import Base, CanonicalEntity, EntityAlias


# SQLite async engine for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.rollback = AsyncMock()
    return session


@pytest_asyncio.fixture
async def db_session():
    """Create a real async database session for integration tests."""
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Create async test client for API tests."""
    # Override the database session dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_canonical_entity(db_session):
    """Create a sample canonical entity for testing."""
    entity = CanonicalEntity(
        name="United States",
        wikidata_id="Q30",
        type="LOCATION"
    )
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest_asyncio.fixture
async def sample_entity_alias(db_session, sample_canonical_entity):
    """Create a sample entity alias for testing."""
    alias = EntityAlias(
        canonical_id=sample_canonical_entity.id,
        alias="USA"
    )
    db_session.add(alias)
    await db_session.commit()
    await db_session.refresh(alias)
    return alias


@pytest.fixture
def mock_deps():
    """
    Mock dependencies for API tests.

    Patches database session and returns mock objects for:
    - FragmentationMetrics
    - AliasStore
    """
    with patch("app.api.routes.canonicalization.get_db_session") as mock_db, \
         patch("app.api.routes.canonicalization.FragmentationMetrics") as mock_frag, \
         patch("app.api.routes.canonicalization.AliasStore") as mock_store:

        # Setup mock session
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        # Make get_db_session return the mock session
        async def mock_get_db():
            yield mock_session
        mock_db.return_value = mock_get_db()

        # Setup FragmentationMetrics mock
        mock_frag_instance = MagicMock()
        mock_frag_instance.generate_report = AsyncMock(return_value={
            "entity_type": "ORGANIZATION",
            "fragmentation_score": 0.4,
            "total_entities": 100,
            "total_aliases": 250,
            "avg_aliases_per_entity": 2.5,
            "singleton_count": 30,
            "singleton_percentage": 30.0,
            "potential_duplicates": [],
            "potential_duplicate_count": 0,
            "improvement_target": "30% reduction in singletons"
        })
        mock_frag_instance.find_potential_duplicates = AsyncMock(return_value=[
            {"entity_id_1": 1, "name1": "Apple Inc.", "entity_id_2": 2, "name2": "Apple Inc", "similarity": 0.98}
        ])
        mock_frag_instance.get_singleton_entities = AsyncMock(return_value=[
            MagicMock(id=1, name="Lonely Entity", type="ORGANIZATION", wikidata_id="Q123")
        ])
        mock_frag.return_value = mock_frag_instance

        # Setup AliasStore mock
        mock_store_instance = MagicMock()
        mock_store_instance.get_most_used_entities = AsyncMock(return_value=[
            (MagicMock(name="United States", type="LOCATION"), 500),
            (MagicMock(name="Germany", type="LOCATION"), 300)
        ])
        mock_store.return_value = mock_store_instance

        yield {
            "session": mock_session,
            "fragmentation_metrics": mock_frag_instance,
            "alias_store": mock_store_instance
        }
