"""Integration tests for Clustering Service.

Tests API endpoints and event flow integration with mocked
database and RabbitMQ connections.

Uses httpx.AsyncClient with FastAPI TestClient pattern.
"""

import json
import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

# Import the main app
from app.main import app
from app.models.cluster import ArticleCluster
from app.schemas.cluster import ArticleClusterRequest, EntityRef
from app.schemas.events import AnalysisCompletedPayload
from app.services.cluster_repository import ClusterRepository
from app.services.clustering import ClusteringService
from app.services.event_publisher import ClusterEventPublisher
from app.api.dependencies import get_current_user_id


# -----------------------------------------------------------------------------
# Auth Override for Testing
# -----------------------------------------------------------------------------

async def override_get_current_user_id() -> str:
    """Mock auth dependency that returns a test user ID."""
    return "test-user-id"


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Override auth dependency for all tests in this module."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    yield
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_embedding() -> List[float]:
    """Generate a sample 384-dimensional embedding."""
    return [0.1] * 384


@pytest.fixture
def sample_embedding_similar() -> List[float]:
    """Generate a similar embedding (high cosine similarity)."""
    return [0.105] * 384


@pytest.fixture
def sample_embedding_different() -> List[float]:
    """Generate a different embedding (low cosine similarity)."""
    return [-0.1] * 192 + [0.3] * 192


@pytest.fixture
def sample_cluster_id() -> UUID:
    """Generate a sample cluster UUID."""
    return uuid4()


@pytest.fixture
def sample_article_id() -> UUID:
    """Generate a sample article UUID."""
    return uuid4()


@pytest.fixture
def sample_entities() -> List[Dict[str, Any]]:
    """Generate sample entities."""
    return [
        {"id": "1", "name": "Apple Inc.", "type": "ORGANIZATION"},
        {"id": "2", "name": "Tim Cook", "type": "PERSON"},
    ]


@pytest.fixture
def mock_cluster(sample_cluster_id: UUID) -> MagicMock:
    """Create a mock ArticleCluster object."""
    cluster = MagicMock(spec=ArticleCluster)
    cluster.id = sample_cluster_id
    cluster.title = "Test Cluster Title"
    cluster.article_count = 3
    cluster.status = "active"
    cluster.tension_score = 5.0
    cluster.is_breaking = False
    cluster.first_seen_at = datetime.now(timezone.utc)
    cluster.last_updated_at = datetime.now(timezone.utc)
    cluster.summary = "Test cluster summary"
    cluster.centroid_vector = [0.1] * 384
    cluster.primary_entities = [{"id": "1", "name": "Test Entity", "type": "ORGANIZATION"}]
    cluster.burst_detected_at = None
    return cluster


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_event_publisher() -> AsyncMock:
    """Create a mock event publisher."""
    publisher = AsyncMock(spec=ClusterEventPublisher)
    publisher.connect = AsyncMock()
    publisher.disconnect = AsyncMock()
    publisher.publish_cluster_created = AsyncMock(return_value=True)
    publisher.publish_cluster_updated = AsyncMock(return_value=True)
    publisher.publish_burst_detected = AsyncMock(return_value=True)
    return publisher


# -----------------------------------------------------------------------------
# API Endpoint Integration Tests
# -----------------------------------------------------------------------------

class TestAPIEndpointIntegration:
    """Tests for API endpoint integration."""

    @pytest.mark.asyncio
    async def test_post_articles_creates_new_cluster(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
    ):
        """Test POST /api/v1/clusters/articles creates new cluster when no match."""
        new_cluster_id = uuid4()

        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo

            # No active clusters -> will create new one
            mock_repo.get_active_clusters = AsyncMock(return_value=[])
            mock_repo.create_cluster = AsyncMock(return_value=new_cluster_id)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/clusters/articles",
                    json={
                        "article_id": str(sample_article_id),
                        "embedding": sample_embedding,
                        "title": "Test Article Title",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["cluster_id"] == str(new_cluster_id)
            assert data["is_new_cluster"] is True
            assert data["similarity_score"] == 1.0
            assert data["cluster_article_count"] == 1

            # Verify create_cluster was called
            mock_repo.create_cluster.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_articles_matches_existing_cluster(
        self,
        sample_embedding: List[float],
        sample_embedding_similar: List[float],
        sample_article_id: UUID,
        sample_cluster_id: UUID,
    ):
        """Test POST /api/v1/clusters/articles matches existing cluster."""
        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo

            # Return existing cluster with similar centroid
            active_clusters = [
                {
                    "id": sample_cluster_id,
                    "centroid": sample_embedding,  # Same as input embedding
                    "article_count": 2,
                    "title": "Existing Cluster",
                },
            ]
            mock_repo.get_active_clusters = AsyncMock(return_value=active_clusters)
            mock_repo.update_cluster = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/clusters/articles",
                    json={
                        "article_id": str(sample_article_id),
                        "embedding": sample_embedding_similar,  # Similar embedding
                        "title": "Test Article Title",
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["cluster_id"] == str(sample_cluster_id)
            assert data["is_new_cluster"] is False
            assert data["similarity_score"] > 0.75  # Above threshold
            assert data["cluster_article_count"] == 3  # Incremented from 2

            # Verify update_cluster was called
            mock_repo.update_cluster.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_articles_with_entities(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
        sample_entities: List[Dict[str, Any]],
    ):
        """Test POST /api/v1/clusters/articles with entities."""
        new_cluster_id = uuid4()

        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo
            mock_repo.get_active_clusters = AsyncMock(return_value=[])
            mock_repo.create_cluster = AsyncMock(return_value=new_cluster_id)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/clusters/articles",
                    json={
                        "article_id": str(sample_article_id),
                        "embedding": sample_embedding,
                        "title": "Test Article Title",
                        "entities": sample_entities,
                    },
                )

            assert response.status_code == 200

            # Verify entities were passed to create_cluster
            call_kwargs = mock_repo.create_cluster.call_args.kwargs
            assert call_kwargs["entities"] is not None
            assert len(call_kwargs["entities"]) == 2

    @pytest.mark.asyncio
    async def test_get_clusters_returns_list(self, mock_cluster: MagicMock):
        """Test GET /api/v1/clusters returns cluster list."""
        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo

            # Return paginated results
            mock_repo.get_clusters_paginated = AsyncMock(
                return_value=([mock_cluster], 1)
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/clusters")

            assert response.status_code == 200
            data = response.json()
            assert "clusters" in data
            assert "pagination" in data
            assert len(data["clusters"]) == 1
            assert data["clusters"][0]["id"] == str(mock_cluster.id)
            assert data["pagination"]["total"] == 1

    @pytest.mark.asyncio
    async def test_get_clusters_with_pagination(self, mock_cluster: MagicMock):
        """Test GET /api/v1/clusters with pagination parameters."""
        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo
            mock_repo.get_clusters_paginated = AsyncMock(
                return_value=([mock_cluster], 100)
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/clusters",
                    params={
                        "status": "active",
                        "min_articles": 5,
                        "hours": 48,
                        "limit": 10,
                        "offset": 20,
                    },
                )

            assert response.status_code == 200

            # Verify pagination parameters were passed
            call_kwargs = mock_repo.get_clusters_paginated.call_args.kwargs
            assert call_kwargs["status"] == "active"
            assert call_kwargs["min_articles"] == 5
            assert call_kwargs["hours"] == 48
            assert call_kwargs["limit"] == 10
            assert call_kwargs["offset"] == 20

    @pytest.mark.asyncio
    async def test_get_cluster_by_id_returns_detail(
        self,
        mock_cluster: MagicMock,
        sample_cluster_id: UUID,
    ):
        """Test GET /api/v1/clusters/{cluster_id} returns cluster detail."""
        mock_cluster.id = sample_cluster_id

        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo
            mock_repo.get_cluster_by_id = AsyncMock(return_value=mock_cluster)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/clusters/{sample_cluster_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(sample_cluster_id)
            assert data["title"] == mock_cluster.title
            assert data["article_count"] == mock_cluster.article_count
            assert "centroid_vector" in data
            assert "primary_entities" in data

    @pytest.mark.asyncio
    async def test_get_cluster_by_id_not_found(self):
        """Test GET /api/v1/clusters/{cluster_id} returns 404 when not found."""
        non_existent_id = uuid4()

        with patch("app.api.v1.clusters.ClusterRepository") as MockRepo:
            mock_repo = AsyncMock()
            MockRepo.return_value = mock_repo
            mock_repo.get_cluster_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/v1/clusters/{non_existent_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestAPIValidation:
    """Tests for API input validation."""

    @pytest.mark.asyncio
    async def test_post_articles_requires_embedding(self):
        """Test POST /api/v1/clusters/articles requires embedding."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/clusters/articles",
                json={
                    "article_id": str(uuid4()),
                    "title": "Test Article",
                    # Missing embedding
                },
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_post_articles_requires_title(
        self,
        sample_embedding: List[float],
    ):
        """Test POST /api/v1/clusters/articles requires title."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/clusters/articles",
                json={
                    "article_id": str(uuid4()),
                    "embedding": sample_embedding,
                    # Missing title
                },
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_clusters_invalid_status(self):
        """Test GET /api/v1/clusters with invalid status parameter."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/clusters",
                params={"status": "invalid_status"},
            )

        assert response.status_code == 422


# -----------------------------------------------------------------------------
# Event Flow Integration Tests
# -----------------------------------------------------------------------------

class TestEventFlowIntegration:
    """Tests for event processing integration."""

    @pytest.mark.asyncio
    async def test_analysis_completed_event_processing(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
        sample_entities: List[Dict[str, Any]],
    ):
        """Test analysis.v3.completed event triggers clustering."""
        from app.workers.analysis_consumer import AnalysisConsumer

        consumer = AnalysisConsumer()
        consumer.clustering_service = ClusteringService()

        # Mock event publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_cluster_created = AsyncMock(return_value=True)
        consumer.event_publisher = mock_publisher

        # Create payload
        payload = AnalysisCompletedPayload(
            article_id=sample_article_id,
            title="Test Article Title",
            embedding=sample_embedding,
            entities=sample_entities,
            tension_level=5.5,
        )

        # Mock database session
        with patch("app.workers.analysis_consumer.async_session") as mock_session_maker:
            mock_session = AsyncMock()

            # Mock repository methods
            mock_repo = AsyncMock()
            mock_repo.get_active_clusters = AsyncMock(return_value=[])
            mock_repo.create_cluster = AsyncMock(return_value=uuid4())

            with patch(
                "app.workers.analysis_consumer.ClusterRepository",
                return_value=mock_repo
            ):
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_maker.return_value = mock_session

                # Call the internal method directly
                await consumer._assign_to_cluster(
                    session=mock_session,
                    payload=payload,
                    correlation_id="test-correlation-id",
                )

        # Verify cluster creation was triggered
        mock_repo.create_cluster.assert_called_once()

        # Verify event was published
        mock_publisher.publish_cluster_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_cluster_created_event_emission(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
    ):
        """Test cluster.created event is emitted for new cluster."""
        from app.workers.analysis_consumer import AnalysisConsumer

        consumer = AnalysisConsumer()
        consumer.clustering_service = ClusteringService()

        new_cluster_id = uuid4()

        # Mock event publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_cluster_created = AsyncMock(return_value=True)
        consumer.event_publisher = mock_publisher

        payload = AnalysisCompletedPayload(
            article_id=sample_article_id,
            title="Breaking News Article",
            embedding=sample_embedding,
        )

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_active_clusters = AsyncMock(return_value=[])
        mock_repo.create_cluster = AsyncMock(return_value=new_cluster_id)

        with patch(
            "app.workers.analysis_consumer.ClusterRepository",
            return_value=mock_repo
        ):
            await consumer._assign_to_cluster(
                session=mock_session,
                payload=payload,
            )

        # Verify cluster.created event was published
        mock_publisher.publish_cluster_created.assert_called_once_with(
            cluster_id=str(new_cluster_id),
            title="Breaking News Article",
            article_id=str(sample_article_id),
            correlation_id=None,
        )

    @pytest.mark.asyncio
    async def test_cluster_updated_event_emission(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
        sample_cluster_id: UUID,
    ):
        """Test cluster.updated event is emitted when article added to cluster."""
        from app.workers.analysis_consumer import AnalysisConsumer

        consumer = AnalysisConsumer()
        consumer.clustering_service = ClusteringService()

        # Mock event publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_cluster_updated = AsyncMock(return_value=True)
        consumer.event_publisher = mock_publisher

        payload = AnalysisCompletedPayload(
            article_id=sample_article_id,
            title="Related Article",
            embedding=sample_embedding,
            tension_level=6.0,
        )

        # Existing cluster with similar centroid
        active_clusters = [
            {
                "id": sample_cluster_id,
                "centroid": sample_embedding,
                "article_count": 2,
                "title": "Existing Cluster",
            },
        ]

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_active_clusters = AsyncMock(return_value=active_clusters)
        mock_repo.update_cluster = AsyncMock(return_value=MagicMock())

        with patch(
            "app.workers.analysis_consumer.ClusterRepository",
            return_value=mock_repo
        ):
            await consumer._assign_to_cluster(
                session=mock_session,
                payload=payload,
                correlation_id="test-correlation-123",
            )

        # Verify cluster.updated event was published
        mock_publisher.publish_cluster_updated.assert_called_once()
        call_kwargs = mock_publisher.publish_cluster_updated.call_args.kwargs
        assert call_kwargs["cluster_id"] == str(sample_cluster_id)
        assert call_kwargs["article_id"] == str(sample_article_id)
        assert call_kwargs["article_count"] == 3
        assert call_kwargs["tension_score"] == 6.0

    @pytest.mark.asyncio
    async def test_burst_detection_triggers_event(
        self,
        sample_embedding: List[float],
        sample_article_id: UUID,
        sample_cluster_id: UUID,
    ):
        """Test cluster.burst_detected event is emitted when burst threshold reached."""
        from app.workers.analysis_consumer import AnalysisConsumer
        from app.config import settings

        consumer = AnalysisConsumer()
        consumer.clustering_service = ClusteringService()

        # Mock event publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_cluster_updated = AsyncMock(return_value=True)
        mock_publisher.publish_burst_detected = AsyncMock(return_value=True)
        consumer.event_publisher = mock_publisher

        payload = AnalysisCompletedPayload(
            article_id=sample_article_id,
            title="Viral Article",
            embedding=sample_embedding,
            entities=[{"id": "1", "name": "Test Entity", "type": "ORGANIZATION"}],
            tension_level=8.0,
        )

        # Cluster at threshold - 1 (adding this article will trigger burst)
        threshold = settings.BURST_ARTICLE_THRESHOLD
        active_clusters = [
            {
                "id": sample_cluster_id,
                "centroid": sample_embedding,
                "article_count": threshold - 1,
                "title": "Trending Cluster",
            },
        ]

        mock_cluster = MagicMock()
        mock_cluster.title = "Trending Cluster"

        mock_session = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_active_clusters = AsyncMock(return_value=active_clusters)
        mock_repo.update_cluster = AsyncMock(return_value=mock_cluster)

        with patch(
            "app.workers.analysis_consumer.ClusterRepository",
            return_value=mock_repo
        ):
            await consumer._assign_to_cluster(
                session=mock_session,
                payload=payload,
            )

        # Verify burst detection event was published
        mock_publisher.publish_burst_detected.assert_called_once()
        call_kwargs = mock_publisher.publish_burst_detected.call_args.kwargs
        assert call_kwargs["cluster_id"] == str(sample_cluster_id)
        assert call_kwargs["article_count"] == threshold

    @pytest.mark.asyncio
    async def test_skips_article_without_embedding(self):
        """Test consumer skips articles without embeddings."""
        from app.workers.analysis_consumer import AnalysisConsumer

        consumer = AnalysisConsumer()

        # Mock publisher - should not be called
        mock_publisher = AsyncMock()
        consumer.event_publisher = mock_publisher

        # Create a mock message with empty embedding
        mock_message = MagicMock()
        mock_message.body = json.dumps({
            "article_id": str(uuid4()),
            "title": "Test Article",
            "embedding": [],  # Empty embedding
        }).encode()

        # process() context manager mock
        mock_message.process = MagicMock()
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()

        # Process should complete without calling event publisher
        await consumer._process_message(mock_message)

        # No cluster events should be published
        mock_publisher.publish_cluster_created.assert_not_called()
        mock_publisher.publish_cluster_updated.assert_not_called()


class TestEventPublisher:
    """Tests for event publisher functionality."""

    @pytest.mark.asyncio
    async def test_publish_cluster_created_event_format(self):
        """Test cluster.created event has correct format."""
        from app.services.event_publisher import ClusterEventPublisher

        with patch(
            "app.services.event_publisher.ResilientRabbitMQPublisher"
        ) as MockPublisher:
            mock_publisher = AsyncMock()
            mock_publisher.connect = AsyncMock()
            mock_publisher.publish = AsyncMock(return_value=True)
            MockPublisher.return_value = mock_publisher

            publisher = ClusterEventPublisher()
            await publisher.connect()

            cluster_id = str(uuid4())
            article_id = str(uuid4())

            await publisher.publish_cluster_created(
                cluster_id=cluster_id,
                title="New Cluster",
                article_id=article_id,
                correlation_id="test-corr-123",
            )

            # Verify publish was called with correct routing key
            mock_publisher.publish.assert_called_once()
            call_kwargs = mock_publisher.publish.call_args.kwargs
            assert call_kwargs["routing_key"] == "cluster.created"

    @pytest.mark.asyncio
    async def test_publish_cluster_updated_event_format(self):
        """Test cluster.updated event has correct format."""
        from app.services.event_publisher import ClusterEventPublisher

        with patch(
            "app.services.event_publisher.ResilientRabbitMQPublisher"
        ) as MockPublisher:
            mock_publisher = AsyncMock()
            mock_publisher.connect = AsyncMock()
            mock_publisher.publish = AsyncMock(return_value=True)
            MockPublisher.return_value = mock_publisher

            publisher = ClusterEventPublisher()
            await publisher.connect()

            await publisher.publish_cluster_updated(
                cluster_id=str(uuid4()),
                article_id=str(uuid4()),
                article_count=5,
                similarity_score=0.85,
                tension_score=6.5,
                is_breaking=False,
            )

            call_kwargs = mock_publisher.publish.call_args.kwargs
            assert call_kwargs["routing_key"] == "cluster.updated"

    @pytest.mark.asyncio
    async def test_publish_burst_detected_event_format(self):
        """Test cluster.burst_detected event has correct format."""
        from app.services.event_publisher import ClusterEventPublisher

        with patch(
            "app.services.event_publisher.ResilientRabbitMQPublisher"
        ) as MockPublisher:
            mock_publisher = AsyncMock()
            mock_publisher.connect = AsyncMock()
            mock_publisher.publish = AsyncMock(return_value=True)
            MockPublisher.return_value = mock_publisher

            publisher = ClusterEventPublisher()
            await publisher.connect()

            await publisher.publish_burst_detected(
                cluster_id=str(uuid4()),
                title="Breaking News Cluster",
                article_count=10,
                growth_rate=2.0,
                tension_score=9.0,
                top_entities=["Entity1", "Entity2"],
            )

            call_kwargs = mock_publisher.publish.call_args.kwargs
            assert call_kwargs["routing_key"] == "cluster.burst_detected"


# -----------------------------------------------------------------------------
# Health Check Tests
# -----------------------------------------------------------------------------

class TestHealthEndpoints:
    """Tests for health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /health endpoint returns healthy status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "clustering-service"

    @pytest.mark.asyncio
    async def test_ready_endpoint(self):
        """Test /ready endpoint returns ready status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
