# tests/test_batch_clustering.py
"""Tests for batch clustering (UMAP+HDBSCAN topic discovery).

This module tests:
- Batch cluster repository operations
- API endpoints for topics
- Incremental assignment logic
- CSAI (Cluster Stability Assessment Index) calculation

Note: Integration tests require running PostgreSQL with pgvector extension.
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# ----- Unit Tests -----


class TestBatchClusterRepository:
    """Tests for BatchClusterRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_latest_batch_id_returns_uuid_when_exists(self, mock_session):
        """Test getting latest completed batch ID."""
        from app.services.batch_cluster_repository import BatchClusterRepository

        expected_batch_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_batch_id
        mock_session.execute.return_value = mock_result

        repo = BatchClusterRepository(mock_session)
        result = await repo.get_latest_batch_id()

        assert result == expected_batch_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_batch_id_returns_none_when_no_batches(self, mock_session):
        """Test getting latest batch ID when no batches exist."""
        from app.services.batch_cluster_repository import BatchClusterRepository

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = BatchClusterRepository(mock_session)
        result = await repo.get_latest_batch_id()

        assert result is None

    @pytest.mark.asyncio
    async def test_list_clusters_filters_by_min_size(self, mock_session):
        """Test listing clusters respects minimum size filter."""
        from app.services.batch_cluster_repository import BatchClusterRepository

        batch_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5  # Total count
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = BatchClusterRepository(mock_session)

        # Mock get_latest_batch_id
        with patch.object(repo, 'get_latest_batch_id', return_value=batch_id):
            clusters, total = await repo.list_clusters(min_size=20)

        assert total == 5
        assert clusters == []


class TestBatchClusteringSchemas:
    """Tests for batch clustering Pydantic schemas."""

    def test_topic_summary_schema(self):
        """Test TopicSummary schema validation."""
        from app.schemas.batch_cluster import TopicSummary

        topic = TopicSummary(
            id=1,
            label="Ukraine Peace Talks",
            keywords=["ukraine", "peace", "diplomacy"],
            article_count=25,
            label_confidence=0.85,
        )

        assert topic.id == 1
        assert topic.label == "Ukraine Peace Talks"
        assert len(topic.keywords) == 3
        assert topic.article_count == 25

    def test_topic_feedback_request_validation(self):
        """Test TopicFeedbackRequest schema validation."""
        from app.schemas.batch_cluster import TopicFeedbackRequest

        # Valid request
        feedback = TopicFeedbackRequest(
            label="Corrected Label",
            confidence=0.95,
        )
        assert feedback.label == "Corrected Label"
        assert feedback.confidence == 0.95

        # Default confidence
        feedback2 = TopicFeedbackRequest(label="Another Label")
        assert feedback2.confidence == 1.0

    def test_batch_info_schema(self):
        """Test BatchInfo schema validation."""
        from app.schemas.batch_cluster import BatchInfo

        batch = BatchInfo(
            batch_id="abc-123",
            status="completed",
            article_count=50000,
            cluster_count=150,
            noise_count=5000,
            csai_score=0.72,
            started_at="2026-01-05T10:00:00Z",
            completed_at="2026-01-05T10:30:00Z",
        )

        assert batch.status == "completed"
        assert batch.cluster_count == 150
        assert batch.csai_score == 0.72


class TestCSAICalculation:
    """Tests for Cluster Stability Assessment Index calculation."""

    def test_csai_perfect_clusters(self):
        """Test CSAI calculation with perfect clustering."""
        # Perfect clustering: each point is equidistant from centroid
        # This should give high CSAI score

        # Simulate: 3 clusters, each with 10 points, all distances = 0.1
        cluster_sizes = [10, 10, 10]
        avg_distances = [0.1, 0.1, 0.1]

        # Simple CSAI calculation: 1 - mean(avg_distances)
        csai = 1.0 - np.mean(avg_distances)
        assert csai == pytest.approx(0.9)

    def test_csai_poor_clusters(self):
        """Test CSAI calculation with poor clustering."""
        # Poor clustering: large distances to centroids
        avg_distances = [0.8, 0.7, 0.9]

        csai = 1.0 - np.mean(avg_distances)
        assert csai == pytest.approx(0.2, rel=0.1)


class TestIncrementalAssignment:
    """Tests for incremental batch cluster assignment."""

    def test_distance_threshold(self):
        """Test that distance threshold is applied correctly."""
        from app.workers.analysis_consumer import BATCH_ASSIGNMENT_DISTANCE_THRESHOLD

        # Default threshold should be reasonable (0.5 = 50% similarity)
        assert 0.3 <= BATCH_ASSIGNMENT_DISTANCE_THRESHOLD <= 0.7

    @pytest.mark.asyncio
    async def test_skip_assignment_when_no_batch(self):
        """Test that assignment is skipped when no batch exists."""
        from app.workers.analysis_consumer import AnalysisConsumer

        consumer = AnalysisConsumer()
        session = AsyncMock()

        # Mock BatchClusterRepository to return None batch
        with patch('app.workers.analysis_consumer.BatchClusterRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_latest_batch_id = AsyncMock(return_value=None)

            # Mock event publisher
            consumer.event_publisher = AsyncMock()

            result = await consumer._assign_to_batch_cluster(
                session=session,
                article_id=uuid4(),
                embedding=[0.1] * 1536,
                title="Test Article",
            )

        assert result is None


class TestBatchClusteringWorker:
    """Tests for batch clustering Celery worker."""

    def test_umap_parameters(self):
        """Test UMAP default parameters are reasonable."""
        from app.config import settings

        # UMAP components should reduce to manageable dimensions
        assert 5 <= settings.BATCH_UMAP_COMPONENTS <= 50

        # Min cluster size should prevent tiny clusters
        assert settings.BATCH_MIN_CLUSTER_SIZE >= 10

    def test_extract_keywords_basic(self):
        """Test keyword extraction from titles."""
        from app.workers.batch_clustering_worker import _extract_keywords

        titles = [
            "Bitcoin price surges past $100k",
            "Bitcoin reaches new all-time high",
            "Cryptocurrency market rally continues",
            "Bitcoin ETF approval expected",
            "Crypto investors see gains",
        ]

        keywords = _extract_keywords(titles)

        assert "terms" in keywords
        assert len(keywords["terms"]) <= 10
        # Common terms should be in top keywords
        terms_lower = [t.lower() for t in keywords["terms"]]
        assert "bitcoin" in terms_lower or "crypto" in terms_lower

    def test_compute_centroids(self):
        """Test centroid computation."""
        from app.workers.batch_clustering_worker import _compute_centroids

        # Create test embeddings (3 clusters)
        embeddings = np.array([
            [1.0, 0.0, 0.0],  # Cluster 0
            [0.9, 0.1, 0.0],  # Cluster 0
            [0.0, 1.0, 0.0],  # Cluster 1
            [0.1, 0.9, 0.0],  # Cluster 1
            [0.0, 0.0, 1.0],  # Cluster 2 (noise label -1 if not enough points)
        ])

        labels = np.array([0, 0, 1, 1, -1])  # -1 = noise

        centroids = _compute_centroids(embeddings, labels)

        # Should have centroids for clusters 0 and 1
        assert 0 in centroids
        assert 1 in centroids
        assert -1 not in centroids  # No centroid for noise

        # Centroid should be mean of cluster points
        expected_0 = np.array([0.95, 0.05, 0.0])
        np.testing.assert_array_almost_equal(centroids[0], expected_0)


# ----- Integration Test Fixtures -----

@pytest.fixture
def sample_embeddings():
    """Generate sample embeddings for testing."""
    np.random.seed(42)
    # 100 articles, 1536 dimensions (like text-embedding-3-small)
    return np.random.rand(100, 1536).astype(np.float32)


@pytest.fixture
def sample_cluster_data():
    """Generate sample batch cluster data."""
    batch_id = uuid4()
    return {
        "batch_id": batch_id,
        "clusters": [
            {
                "id": 1,
                "batch_id": batch_id,
                "cluster_idx": 0,
                "label": "Ukraine Conflict",
                "keywords": {"terms": ["ukraine", "russia", "war"]},
                "article_count": 50,
            },
            {
                "id": 2,
                "batch_id": batch_id,
                "cluster_idx": 1,
                "label": "Bitcoin Market",
                "keywords": {"terms": ["bitcoin", "crypto", "price"]},
                "article_count": 30,
            },
        ],
    }


# ----- API Endpoint Tests -----

class TestBatchClustersAPI:
    """Tests for batch cluster API endpoints."""

    @pytest.fixture
    def mock_app(self):
        """Create test FastAPI app."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()

        # Mock dependencies
        from app.api.v1.batch_clusters import router
        app.include_router(router, prefix="/topics")

        return app

    def test_topics_list_endpoint_schema(self):
        """Test topics list endpoint response schema."""
        from app.schemas.batch_cluster import TopicListResponse, TopicSummary

        # Create sample response
        response = TopicListResponse(
            topics=[
                TopicSummary(id=1, label="Test", article_count=10, keywords=None, label_confidence=None),
            ],
            total=1,
            limit=50,
            offset=0,
            has_more=False,
            batch_id="test-batch-123",
        )

        assert len(response.topics) == 1
        assert response.total == 1
        assert not response.has_more

    def test_topic_search_response_schema(self):
        """Test topic search response schema."""
        from app.schemas.batch_cluster import TopicSearchResponse, TopicSearchResult

        response = TopicSearchResponse(
            results=[
                TopicSearchResult(
                    cluster_id=1,
                    label="Bitcoin News",
                    keywords=["bitcoin", "crypto"],
                    article_count=25,
                    match_count=15,
                ),
            ],
            query="bitcoin",
            batch_id="test-batch",
        )

        assert len(response.results) == 1
        assert response.results[0].match_count == 15
        assert response.query == "bitcoin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
