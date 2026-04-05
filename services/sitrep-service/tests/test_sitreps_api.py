# services/sitrep-service/tests/test_sitreps_api.py
"""Tests for SITREP API endpoints.

Tests all REST API endpoints for the SITREP service:
- GET /api/v1/sitreps - List SITREPs
- GET /api/v1/sitreps/latest - Get latest SITREP
- GET /api/v1/sitreps/{id} - Get SITREP by ID
- POST /api/v1/sitreps/generate - Trigger generation
- PATCH /api/v1/sitreps/{id}/review - Mark as reviewed
- DELETE /api/v1/sitreps/{id} - Delete SITREP

Uses SQLite in-memory database and mocked authentication for isolation.
"""

from datetime import date, datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.sitrep import Base, SitrepReport
from app.repositories.sitrep_repository import SitrepRepository
from app.schemas.sitrep import SitrepResponse, KeyDevelopment, RiskAssessment
from app.schemas.story import TopStory


# ============================================================
# Test Configuration
# ============================================================


def create_test_token(user_id: str = "test-user-123") -> str:
    """Create a valid JWT token for testing."""
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc).timestamp() + 3600}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_expired_token(user_id: str = "test-user-123") -> str:
    """Create an expired JWT token for testing."""
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc).timestamp() - 3600}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_invalid_token() -> str:
    """Create an invalid JWT token for testing."""
    return "invalid.jwt.token"


# ============================================================
# Fixtures
# ============================================================


@pytest_asyncio.fixture
async def async_engine():
    """Create async SQLite engine for testing."""
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
    """Create async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def repository() -> SitrepRepository:
    """Create repository instance."""
    return SitrepRepository()


@pytest.fixture
def valid_auth_header() -> dict:
    """Create valid authorization header."""
    return {"Authorization": f"Bearer {create_test_token()}"}


@pytest.fixture
def sample_sitrep() -> SitrepResponse:
    """Create a sample SITREP response for testing."""
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
def sample_story() -> TopStory:
    """Create a sample TopStory for testing."""
    return TopStory(
        cluster_id=uuid4(),
        title="Test Story Cluster",
        article_count=10,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        tension_score=7.5,
        relevance_score=0.9,
        is_breaking=False,
        category="geopolitics",
        top_entities=["Entity1", "Entity2"],
    )


# ============================================================
# Authentication Tests
# ============================================================


class TestAuthentication:
    """Tests for JWT authentication on API endpoints."""

    @pytest.mark.asyncio
    async def test_list_sitreps_requires_auth(self, async_session, async_engine):
        """Endpoints should require authentication."""
        # Arrange
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps")

        # Assert - HTTPBearer returns 403 Forbidden when credentials are missing
        # and 401 Unauthorized when credentials are invalid
        assert response.status_code in [401, 403]  # No auth header

        # Cleanup
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, async_session):
        """Invalid JWT token should return 401."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers={"Authorization": f"Bearer {create_invalid_token()}"}
            )

        assert response.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, async_session):
        """Expired JWT token should return 401."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers={"Authorization": f"Bearer {create_expired_token()}"}
            )

        assert response.status_code == 401
        app.dependency_overrides.clear()


# ============================================================
# List SITREPs Tests
# ============================================================


class TestListSitreps:
    """Tests for GET /api/v1/sitreps endpoint."""

    @pytest.mark.asyncio
    async def test_list_sitreps_empty(
        self, async_session, valid_auth_header
    ):
        """List should return empty when no SITREPs exist."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers=valid_auth_header
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sitreps"] == []
        assert data["total"] == 0
        assert data["has_more"] is False
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_returns_records(
        self, async_session, repository, sample_sitrep, valid_auth_header
    ):
        """List should return existing SITREPs."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange
        await repository.save(async_session, sample_sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 1
        assert data["total"] == 1
        assert data["sitreps"][0]["title"] == sample_sitrep.title
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_pagination(
        self, async_session, repository, valid_auth_header
    ):
        """List should support pagination."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange - create 5 SITREPs
        for i in range(5):
            sitrep = SitrepResponse(
                id=uuid4(),
                report_date=date.today(),
                report_type="daily",
                title=f"SITREP {i}",
                executive_summary=f"Summary {i}",
                content_markdown=f"Content {i}",
                top_stories=[],
                key_entities=[],
                sentiment_summary={"overall": "neutral"},
                generation_model="test",
                generation_time_ms=100,
                articles_analyzed=10,
                created_at=datetime.now(timezone.utc),
            )
            await repository.save(async_session, sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - get first page of 2
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?limit=2&offset=0",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 2
        assert data["total"] == 5
        assert data["has_more"] is True
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_filter_by_type(
        self, async_session, repository, valid_auth_header
    ):
        """List should filter by report_type."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange - create daily and weekly SITREPs
        for report_type in ["daily", "daily", "weekly"]:
            sitrep = SitrepResponse(
                id=uuid4(),
                report_date=date.today(),
                report_type=report_type,
                title=f"{report_type} SITREP",
                executive_summary="Summary",
                content_markdown="Content",
                top_stories=[],
                key_entities=[],
                sentiment_summary={"overall": "neutral"},
                generation_model="test",
                generation_time_ms=100,
                articles_analyzed=10,
                created_at=datetime.now(timezone.utc),
            )
            await repository.save(async_session, sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - filter by daily
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?report_type=daily",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 2
        assert all(s["report_type"] == "daily" for s in data["sitreps"])
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_filter_by_category(
        self, async_session, repository, valid_auth_header
    ):
        """List should filter by category."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange - create SITREPs with different categories
        categories = ["politics", "politics", "finance", "technology"]
        for i, category in enumerate(categories):
            sitrep = SitrepResponse(
                id=uuid4(),
                report_date=date.today(),
                report_type="daily",
                category=category,
                title=f"{category} SITREP {i}",
                executive_summary="Summary",
                content_markdown="Content",
                top_stories=[],
                key_entities=[],
                sentiment_summary={"overall": "neutral"},
                generation_model="test",
                generation_time_ms=100,
                articles_analyzed=10,
                created_at=datetime.now(timezone.utc),
            )
            await repository.save(async_session, sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - filter by politics
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?category=politics",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 2
        assert data["total"] == 2
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_filter_by_category_and_type(
        self, async_session, repository, valid_auth_header
    ):
        """List should filter by both category and report_type."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange - create SITREPs with different categories and types
        configs = [
            ("politics", "daily"),
            ("politics", "weekly"),
            ("finance", "daily"),
            ("finance", "weekly"),
        ]
        for i, (category, report_type) in enumerate(configs):
            sitrep = SitrepResponse(
                id=uuid4(),
                report_date=date.today(),
                report_type=report_type,
                category=category,
                title=f"{category} {report_type} SITREP {i}",
                executive_summary="Summary",
                content_markdown="Content",
                top_stories=[],
                key_entities=[],
                sentiment_summary={"overall": "neutral"},
                generation_model="test",
                generation_time_ms=100,
                articles_analyzed=10,
                created_at=datetime.now(timezone.utc),
            )
            await repository.save(async_session, sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - filter by politics AND daily
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?category=politics&report_type=daily",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 1
        assert data["total"] == 1
        assert data["sitreps"][0]["report_type"] == "daily"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_invalid_category_returns_422(
        self, async_session, valid_auth_header
    ):
        """List should return 422 for invalid category."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - use invalid category
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?category=invalid_category",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "Invalid category" in data["detail"]
        assert "invalid_category" in data["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sitreps_all_valid_categories(
        self, async_session, repository, valid_auth_header
    ):
        """All valid categories should be accepted."""
        from app.main import app
        from app.api.deps import get_db
        from app.constants import SITREP_CATEGORIES

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act - test all valid categories
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            for category in SITREP_CATEGORIES.keys():
                response = await client.get(
                    f"/api/v1/sitreps?category={category}",
                    headers=valid_auth_header
                )
                # Assert - should not return 422 validation error
                assert response.status_code == 200, f"Category '{category}' should be valid"

        app.dependency_overrides.clear()


# ============================================================
# Get Latest SITREP Tests
# ============================================================


class TestGetLatestSitrep:
    """Tests for GET /api/v1/sitreps/latest endpoint."""

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent(
        self, async_session, repository, sample_sitrep, valid_auth_header
    ):
        """Should return the most recent SITREP of specified type."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange
        await repository.save(async_session, sample_sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/latest?report_type=daily",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_sitrep.title
        assert data["report_type"] == "daily"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_latest_returns_404_when_empty(
        self, async_session, valid_auth_header
    ):
        """Should return 404 when no SITREPs exist."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/latest",
                headers=valid_auth_header
            )

        assert response.status_code == 404
        app.dependency_overrides.clear()


# ============================================================
# Get SITREP by ID Tests
# ============================================================


class TestGetSitrepById:
    """Tests for GET /api/v1/sitreps/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_sitrep(
        self, async_session, repository, sample_sitrep, valid_auth_header
    ):
        """Should return SITREP when found."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange
        saved = await repository.save(async_session, sample_sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{saved.id}",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(saved.id)
        assert data["title"] == sample_sitrep.title
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_404_when_not_found(
        self, async_session, valid_auth_header
    ):
        """Should return 404 for non-existent ID."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{uuid4()}",
                headers=valid_auth_header
            )

        assert response.status_code == 404
        app.dependency_overrides.clear()


# ============================================================
# Generate SITREP Tests
# ============================================================


class TestGenerateSitrep:
    """Tests for POST /api/v1/sitreps/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_returns_503_when_aggregator_unavailable(
        self, async_session, valid_auth_header
    ):
        """Should return 503 when aggregator is not available."""
        from app.main import app
        from app.api.deps import get_db, get_story_aggregator
        from fastapi import HTTPException

        async def override_get_db():
            yield async_session

        def override_get_aggregator():
            raise HTTPException(
                status_code=503,
                detail="Story aggregator not available"
            )

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_story_aggregator] = override_get_aggregator

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/sitreps/generate",
                json={"report_type": "daily"},
                headers=valid_auth_header
            )

        assert response.status_code == 503
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_returns_400_when_no_stories(
        self, async_session, valid_auth_header
    ):
        """Should return 400 when no stories available."""
        from app.main import app
        from app.api.deps import get_db, get_story_aggregator
        from app.services.story_aggregator import StoryAggregator

        async def override_get_db():
            yield async_session

        # Create mock aggregator that returns no stories
        mock_aggregator = AsyncMock(spec=StoryAggregator)
        mock_aggregator.get_top_stories = AsyncMock(return_value=[])

        def override_get_aggregator():
            return mock_aggregator

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_story_aggregator] = override_get_aggregator

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/sitreps/generate",
                json={"report_type": "daily"},
                headers=valid_auth_header
            )

        assert response.status_code == 400
        assert "No stories available" in response.json()["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_creates_sitrep_successfully(
        self, async_session, sample_story, sample_sitrep, valid_auth_header
    ):
        """Should generate and save SITREP when stories available."""
        from app.main import app
        from app.api.deps import get_db, get_story_aggregator
        from app.services.story_aggregator import StoryAggregator
        from app.services.sitrep_generator import SitrepGenerator

        async def override_get_db():
            yield async_session

        # Create mock aggregator
        mock_aggregator = AsyncMock(spec=StoryAggregator)
        mock_aggregator.get_top_stories = AsyncMock(return_value=[sample_story])

        def override_get_aggregator():
            return mock_aggregator

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_story_aggregator] = override_get_aggregator

        # Mock the generator
        with patch.object(
            SitrepGenerator,
            'generate',
            return_value=sample_sitrep
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/sitreps/generate",
                    json={"report_type": "daily"},
                    headers=valid_auth_header
                )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["sitrep_id"] is not None
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_sitrep_with_category_filter(
        self, async_session, sample_story, sample_sitrep, valid_auth_header
    ):
        """Generate SITREP with category filter should call aggregator with category."""
        from app.main import app
        from app.api.deps import get_db, get_story_aggregator
        from app.services.story_aggregator import StoryAggregator
        from app.services.sitrep_generator import SitrepGenerator

        async def override_get_db():
            yield async_session

        # Create mock aggregator
        mock_aggregator = AsyncMock(spec=StoryAggregator)
        mock_aggregator.get_top_stories = AsyncMock(return_value=[sample_story])

        def override_get_aggregator():
            return mock_aggregator

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_story_aggregator] = override_get_aggregator

        # Mock the generator
        with patch.object(
            SitrepGenerator,
            'generate',
            return_value=sample_sitrep
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/sitreps/generate",
                    json={
                        "report_type": "daily",
                        "category": "politics",
                        "top_stories_count": 10,
                    },
                    headers=valid_auth_header
                )

        # Assert
        assert response.status_code == 201

        # Verify aggregator was called with category filter
        mock_aggregator.get_top_stories.assert_called_once()
        call_kwargs = mock_aggregator.get_top_stories.call_args.kwargs
        assert call_kwargs.get("category") == "politics"
        assert call_kwargs.get("max_age_hours") == 24  # daily = 24h
        assert call_kwargs.get("is_breaking_only") is False

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_breaking_sitrep_uses_correct_filters(
        self, async_session, sample_story, sample_sitrep, valid_auth_header
    ):
        """Generate breaking SITREP should use is_breaking_only=True and 6h max age."""
        from app.main import app
        from app.api.deps import get_db, get_story_aggregator
        from app.services.story_aggregator import StoryAggregator
        from app.services.sitrep_generator import SitrepGenerator

        async def override_get_db():
            yield async_session

        # Create mock aggregator
        mock_aggregator = AsyncMock(spec=StoryAggregator)
        mock_aggregator.get_top_stories = AsyncMock(return_value=[sample_story])

        def override_get_aggregator():
            return mock_aggregator

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_story_aggregator] = override_get_aggregator

        # Mock the generator
        with patch.object(
            SitrepGenerator,
            'generate',
            return_value=sample_sitrep
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/sitreps/generate",
                    json={
                        "report_type": "breaking",
                        "top_stories_count": 5,
                    },
                    headers=valid_auth_header
                )

        # Assert
        assert response.status_code == 201

        # Verify aggregator was called with breaking-specific filters
        mock_aggregator.get_top_stories.assert_called_once()
        call_kwargs = mock_aggregator.get_top_stories.call_args.kwargs
        assert call_kwargs.get("max_age_hours") == 6  # breaking = 6h
        assert call_kwargs.get("is_breaking_only") is True

        app.dependency_overrides.clear()


# ============================================================
# Mark Reviewed Tests
# ============================================================


class TestMarkReviewed:
    """Tests for PATCH /api/v1/sitreps/{id}/review endpoint."""

    @pytest.mark.asyncio
    async def test_mark_reviewed_updates_flag(
        self, async_session, repository, sample_sitrep, valid_auth_header
    ):
        """Should update human_reviewed flag."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange
        saved = await repository.save(async_session, sample_sitrep)
        assert saved.human_reviewed is False

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/sitreps/{saved.id}/review?reviewed=true",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["human_reviewed"] is True
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_mark_reviewed_returns_404_when_not_found(
        self, async_session, valid_auth_header
    ):
        """Should return 404 for non-existent SITREP."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/sitreps/{uuid4()}/review",
                headers=valid_auth_header
            )

        assert response.status_code == 404
        app.dependency_overrides.clear()


# ============================================================
# Delete SITREP Tests
# ============================================================


class TestDeleteSitrep:
    """Tests for DELETE /api/v1/sitreps/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_removes_sitrep(
        self, async_session, repository, sample_sitrep, valid_auth_header
    ):
        """Should delete SITREP and return 204."""
        from app.main import app
        from app.api.deps import get_db

        # Arrange
        saved = await repository.save(async_session, sample_sitrep)

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        # Act
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/sitreps/{saved.id}",
                headers=valid_auth_header
            )

        # Assert
        assert response.status_code == 204

        # Verify deleted
        deleted = await repository.get_by_id(async_session, saved.id)
        assert deleted is None
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_returns_404_when_not_found(
        self, async_session, valid_auth_header
    ):
        """Should return 404 for non-existent SITREP."""
        from app.main import app
        from app.api.deps import get_db

        async def override_get_db():
            yield async_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/sitreps/{uuid4()}",
                headers=valid_auth_header
            )

        assert response.status_code == 404
        app.dependency_overrides.clear()


# ============================================================
# OpenAPI Documentation Tests
# ============================================================


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_schema_available(self):
        """OpenAPI schema should be accessible."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/sitreps" in schema["paths"]
        assert "/api/v1/sitreps/latest" in schema["paths"]
        assert "/api/v1/sitreps/{sitrep_id}" in schema["paths"]
        assert "/api/v1/sitreps/generate" in schema["paths"]

    @pytest.mark.asyncio
    async def test_swagger_ui_available(self):
        """Swagger UI should be accessible."""
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/docs")

        assert response.status_code == 200
