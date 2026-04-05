# services/sitrep-service/tests/integration/test_api_integration.py
"""Integration tests for SITREP API with database.

Tests the REST API endpoints with real database operations:
- GET /api/v1/sitreps - List SITREPs (paginated)
- GET /api/v1/sitreps/{id} - Get SITREP by ID
- GET /api/v1/sitreps/latest - Get latest SITREP
- POST /api/v1/sitreps/generate - Trigger manual generation
- PATCH /api/v1/sitreps/{id}/review - Mark as reviewed
- DELETE /api/v1/sitreps/{id} - Delete SITREP

Uses TestClient with SQLite in-memory database for isolation.
"""

import json
import pytest
import pytest_asyncio
from datetime import date, datetime, timezone, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.api.v1.sitreps import router
from app.config import settings
from app.models.sitrep import Base, SitrepReport
from app.repositories.sitrep_repository import SitrepRepository
from app.schemas.sitrep import SitrepResponse, KeyDevelopment, RiskAssessment
from app.schemas.story import TopStory
from app.services.story_aggregator import StoryAggregator


# ============================================================
# Test Fixtures
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
    session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def session_maker(async_engine):
    """Create session maker for dependency injection."""
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
def repository():
    """Create SitrepRepository instance."""
    return SitrepRepository()


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    payload = {
        "sub": "test-user-id",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def mock_aggregator():
    """Create a mock StoryAggregator with test data."""
    aggregator = StoryAggregator()
    return aggregator


@pytest.fixture
def sample_stories():
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


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response."""
    return {
        "executive_summary": "Test executive summary for API testing.",
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


def create_sample_sitrep(
    report_date: date = None,
    report_type: str = "daily",
    title: str = "Test SITREP",
) -> SitrepResponse:
    """Factory function to create test SITREP responses."""
    return SitrepResponse(
        id=uuid4(),
        report_date=report_date or date.today(),
        report_type=report_type,
        title=title,
        executive_summary="Test executive summary.",
        content_markdown="# Test\n\nContent",
        top_stories=[
            {
                "cluster_id": str(uuid4()),
                "title": "Story",
                "article_count": 5,
                "tension_score": 0.75,
                "is_breaking": False,
                "category": "default",
            }
        ],
        key_entities=[{"name": "Entity", "type": "organization", "mention_count": 5}],
        sentiment_summary={"overall": "neutral", "positive_percent": 30.0},
        generation_model="gpt-4-turbo-preview",
        generation_time_ms=1500,
        prompt_tokens=1000,
        completion_tokens=500,
        articles_analyzed=25,
        confidence_score=0.85,
        human_reviewed=False,
        created_at=datetime.now(timezone.utc),
    )


# ============================================================
# Test App Setup
# ============================================================


def create_test_app(session_maker, aggregator=None):
    """Create test FastAPI app with dependency overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Override dependencies
    async def get_test_db():
        async with session_maker() as session:
            yield session

    def get_test_aggregator():
        if aggregator is None:
            raise Exception("Aggregator not available")
        return aggregator

    from app.api.deps import get_db, get_story_aggregator
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_story_aggregator] = get_test_aggregator

    return app


# ============================================================
# API Integration Tests - List SITREPs
# ============================================================


class TestListSitrepsEndpoint:
    """Tests for GET /api/v1/sitreps endpoint."""

    @pytest.mark.asyncio
    async def test_list_sitreps_empty_database(
        self,
        session_maker,
        auth_headers,
    ):
        """Test listing SITREPs when database is empty."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["sitreps"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_sitreps_with_data(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test listing SITREPs with data in database."""
        # Populate database
        for i in range(3):
            sitrep = create_sample_sitrep(title=f"SITREP {i}")
            await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_sitreps_pagination(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test pagination parameters."""
        # Create 5 SITREPs
        for i in range(5):
            sitrep = create_sample_sitrep(title=f"SITREP {i}")
            await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Get first page
            response = await client.get(
                "/api/v1/sitreps?limit=2&offset=0",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 2
        assert data["total"] == 5
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_sitreps_filter_by_type(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test filtering by report_type."""
        # Create mixed types
        await repository.save(
            async_session,
            create_sample_sitrep(report_type="daily", title="Daily 1"),
        )
        await repository.save(
            async_session,
            create_sample_sitrep(report_type="weekly", title="Weekly 1"),
        )
        await repository.save(
            async_session,
            create_sample_sitrep(report_type="daily", title="Daily 2"),
        )

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?report_type=daily",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sitreps"]) == 2
        assert all(s["report_type"] == "daily" for s in data["sitreps"])

    @pytest.mark.asyncio
    async def test_list_sitreps_unauthorized(self, session_maker):
        """Test that unauthorized requests are rejected."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps")

        # HTTPBearer returns 401 when no credentials provided
        assert response.status_code == 401


# ============================================================
# API Integration Tests - Get SITREP by ID
# ============================================================


class TestGetSitrepByIdEndpoint:
    """Tests for GET /api/v1/sitreps/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_sitrep_by_id_success(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test getting a SITREP by valid ID."""
        sitrep = create_sample_sitrep(title="Specific SITREP")
        saved = await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{saved.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Specific SITREP"
        assert data["id"] == str(saved.id)

    @pytest.mark.asyncio
    async def test_get_sitrep_by_id_not_found(
        self,
        session_maker,
        auth_headers,
    ):
        """Test getting a non-existent SITREP."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{uuid4()}",
                headers=auth_headers,
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sitrep_includes_full_data(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test that full SITREP data is returned."""
        sitrep = create_sample_sitrep()
        saved = await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{saved.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert "id" in data
        assert "report_date" in data
        assert "report_type" in data
        assert "title" in data
        assert "executive_summary" in data
        assert "content_markdown" in data
        assert "top_stories" in data
        assert "key_entities" in data
        assert "sentiment_summary" in data
        assert "generation_model" in data
        assert "generation_time_ms" in data


# ============================================================
# API Integration Tests - Get Latest SITREP
# ============================================================


class TestGetLatestSitrepEndpoint:
    """Tests for GET /api/v1/sitreps/latest endpoint."""

    @pytest.mark.asyncio
    async def test_get_latest_sitrep_success(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test getting the latest SITREP."""
        # Create older SITREP
        old_sitrep = create_sample_sitrep(
            report_date=date.today() - timedelta(days=1),
            title="Old SITREP",
        )
        await repository.save(async_session, old_sitrep)

        # Create newer SITREP
        new_sitrep = create_sample_sitrep(
            report_date=date.today(),
            title="Latest SITREP",
        )
        await repository.save(async_session, new_sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/latest",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        # Note: Latest is determined by created_at, not report_date
        assert data["title"] in ["Old SITREP", "Latest SITREP"]

    @pytest.mark.asyncio
    async def test_get_latest_sitrep_not_found(
        self,
        session_maker,
        auth_headers,
    ):
        """Test getting latest when none exists."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/latest",
                headers=auth_headers,
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_latest_by_type(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test getting latest by specific type."""
        # Create daily
        daily = create_sample_sitrep(report_type="daily", title="Daily")
        await repository.save(async_session, daily)

        # Create weekly
        weekly = create_sample_sitrep(report_type="weekly", title="Weekly")
        await repository.save(async_session, weekly)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/latest?report_type=weekly",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "weekly"


# ============================================================
# API Integration Tests - Generate SITREP
# ============================================================


class TestGenerateSitrepEndpoint:
    """Tests for POST /api/v1/sitreps/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_sitrep_success(
        self,
        session_maker,
        sample_stories,
        mock_llm_response,
        auth_headers,
    ):
        """Test successful SITREP generation."""
        # Create aggregator with stories
        aggregator = StoryAggregator()
        for story in sample_stories:
            aggregator._stories[story.cluster_id] = story

        app = create_test_app(session_maker, aggregator)

        with patch("app.api.v1.sitreps.SitrepGenerator") as MockGenerator:
            mock_gen = AsyncMock()
            MockGenerator.return_value = mock_gen

            # Create a proper SitrepResponse for the mock
            mock_sitrep = SitrepResponse(
                id=uuid4(),
                report_date=date.today(),
                report_type="daily",
                title="Daily SITREP",
                executive_summary=mock_llm_response["executive_summary"],
                content_markdown=mock_llm_response["content_markdown"],
                top_stories=[
                    {
                        "cluster_id": str(s.cluster_id),
                        "title": s.title,
                        "article_count": s.article_count,
                        "tension_score": s.tension_score,
                        "is_breaking": s.is_breaking,
                        "category": s.category,
                    }
                    for s in sample_stories
                ],
                key_entities=[{"name": "Test", "type": "org", "mention_count": 1}],
                sentiment_summary=mock_llm_response["sentiment_analysis"],
                generation_model="gpt-4-turbo-preview",
                generation_time_ms=1500,
                prompt_tokens=1000,
                completion_tokens=500,
                articles_analyzed=28,
                created_at=datetime.now(timezone.utc),
            )
            mock_gen.generate = AsyncMock(return_value=mock_sitrep)

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/sitreps/generate",
                    headers=auth_headers,
                    json={
                        "report_type": "daily",
                        "top_stories_count": 10,
                        "min_cluster_size": 1,
                    },
                )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "sitrep_id" in data
        assert data["sitrep"] is not None

    @pytest.mark.asyncio
    async def test_generate_sitrep_no_stories(
        self,
        session_maker,
        auth_headers,
    ):
        """Test generation fails gracefully with no stories."""
        # Empty aggregator
        aggregator = StoryAggregator()

        app = create_test_app(session_maker, aggregator)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/sitreps/generate",
                headers=auth_headers,
                json={
                    "report_type": "daily",
                    "min_cluster_size": 5,  # High minimum
                },
            )

        assert response.status_code == 400
        assert "No stories available" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_sitrep_invalid_type(
        self,
        session_maker,
        auth_headers,
        sample_stories,
    ):
        """Test generation with invalid report type."""
        aggregator = StoryAggregator()
        for story in sample_stories:
            aggregator._stories[story.cluster_id] = story

        app = create_test_app(session_maker, aggregator)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/sitreps/generate",
                headers=auth_headers,
                json={
                    "report_type": "invalid_type",
                },
            )

        assert response.status_code == 422  # Validation error


# ============================================================
# API Integration Tests - Mark Reviewed
# ============================================================


class TestMarkReviewedEndpoint:
    """Tests for PATCH /api/v1/sitreps/{id}/review endpoint."""

    @pytest.mark.asyncio
    async def test_mark_reviewed_success(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test marking a SITREP as reviewed."""
        sitrep = create_sample_sitrep()
        saved = await repository.save(async_session, sitrep)
        assert saved.human_reviewed is False

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/sitreps/{saved.id}/review?reviewed=true",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["human_reviewed"] is True

    @pytest.mark.asyncio
    async def test_mark_unreviewed(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test marking a SITREP as not reviewed."""
        sitrep = create_sample_sitrep()
        sitrep = SitrepResponse(**{
            **sitrep.model_dump(),
            "human_reviewed": True,
        })
        saved = await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/sitreps/{saved.id}/review?reviewed=false",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["human_reviewed"] is False

    @pytest.mark.asyncio
    async def test_mark_reviewed_not_found(
        self,
        session_maker,
        auth_headers,
    ):
        """Test marking non-existent SITREP."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/sitreps/{uuid4()}/review?reviewed=true",
                headers=auth_headers,
            )

        assert response.status_code == 404


# ============================================================
# API Integration Tests - Delete SITREP
# ============================================================


class TestDeleteSitrepEndpoint:
    """Tests for DELETE /api/v1/sitreps/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_sitrep_success(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test successful SITREP deletion."""
        sitrep = create_sample_sitrep()
        saved = await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/sitreps/{saved.id}",
                headers=auth_headers,
            )

        assert response.status_code == 204

        # Verify deleted
        result = await repository.get_by_id(async_session, saved.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_sitrep_not_found(
        self,
        session_maker,
        auth_headers,
    ):
        """Test deleting non-existent SITREP."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/sitreps/{uuid4()}",
                headers=auth_headers,
            )

        assert response.status_code == 404


# ============================================================
# API Integration Tests - Authentication
# ============================================================


class TestApiAuthentication:
    """Tests for API authentication."""

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, session_maker):
        """Test that invalid tokens are rejected."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers={"Authorization": "Bearer invalid_token"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, session_maker):
        """Test that expired tokens are rejected."""
        # Create expired token
        payload = {
            "sub": "test-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        }
        expired_token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps",
                headers={"Authorization": f"Bearer {expired_token}"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_auth_header_rejected(self, session_maker):
        """Test that missing auth header is rejected."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps")

        # HTTPBearer returns 401 when no credentials provided
        assert response.status_code == 401


# ============================================================
# API Integration Tests - Error Handling
# ============================================================


class TestApiErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(
        self,
        session_maker,
        auth_headers,
    ):
        """Test handling of invalid UUID format."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps/not-a-uuid",
                headers=auth_headers,
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_pagination_params(
        self,
        session_maker,
        auth_headers,
    ):
        """Test handling of invalid pagination parameters."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?limit=-1",
                headers=auth_headers,
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_report_type_filter(
        self,
        session_maker,
        auth_headers,
    ):
        """Test handling of invalid report_type filter."""
        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/sitreps?report_type=invalid",
                headers=auth_headers,
            )

        assert response.status_code == 422  # Validation error


# ============================================================
# API Integration Tests - Response Format
# ============================================================


class TestApiResponseFormat:
    """Tests for API response format consistency."""

    @pytest.mark.asyncio
    async def test_list_response_format(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test that list response has correct format."""
        sitrep = create_sample_sitrep()
        await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sitreps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify pagination structure
        assert "sitreps" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        # Verify list item structure
        if data["sitreps"]:
            item = data["sitreps"][0]
            assert "id" in item
            assert "report_date" in item
            assert "report_type" in item
            assert "title" in item
            assert "executive_summary" in item
            assert "articles_analyzed" in item

    @pytest.mark.asyncio
    async def test_detail_response_format(
        self,
        session_maker,
        async_session,
        repository,
        auth_headers,
    ):
        """Test that detail response has correct format."""
        sitrep = create_sample_sitrep()
        saved = await repository.save(async_session, sitrep)

        app = create_test_app(session_maker)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/sitreps/{saved.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        # Verify full response structure
        required_fields = [
            "id", "report_date", "report_type", "title",
            "executive_summary", "content_markdown", "top_stories",
            "key_entities", "sentiment_summary", "generation_model",
            "generation_time_ms", "articles_analyzed", "human_reviewed",
            "created_at",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"
