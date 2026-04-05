"""Tests for cluster repository."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.cluster_repository import ClusterRepository


class TestClusterRepository:
    """Tests for cluster database operations."""

    @pytest.mark.asyncio
    async def test_create_cluster_returns_uuid(self):
        """Creating a cluster should return its UUID."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        repo = ClusterRepository(mock_session)
        cluster_id = await repo.create_cluster(
            title="Test Cluster",
            centroid_vector=[0.1, 0.2, 0.3],
            first_article_id=uuid4()
        )

        assert cluster_id is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_clusters_returns_list(self):
        """Should return list of active clusters."""
        mock_session = AsyncMock()

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        clusters = await repo.get_active_clusters(max_age_hours=24)

        assert isinstance(clusters, list)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_cluster_increments_count(self):
        """Updating cluster should increment article count."""
        mock_session = AsyncMock()
        mock_cluster = MagicMock()
        mock_cluster.article_count = 1
        mock_cluster.centroid_vector = [0.1, 0.2]
        mock_cluster.is_breaking = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)
        await repo.update_cluster(
            cluster_id=uuid4(),
            new_centroid=[0.15, 0.25],
            new_article_count=2
        )

        assert mock_cluster.article_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_cluster_not_found_returns_none(self):
        """Updating non-existent cluster should return None."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        result = await repo.update_cluster(
            cluster_id=uuid4(),
            new_centroid=[0.15, 0.25],
            new_article_count=2
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cluster_by_id_returns_cluster(self):
        """Should return cluster when found."""
        mock_session = AsyncMock()
        mock_cluster = MagicMock()
        mock_cluster.id = uuid4()
        mock_cluster.title = "Test Cluster"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        result = await repo.get_cluster_by_id(mock_cluster.id)

        assert result is not None
        assert result.title == "Test Cluster"

    @pytest.mark.asyncio
    async def test_get_cluster_by_id_not_found(self):
        """Should return None when cluster not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        result = await repo.get_cluster_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_clusters_paginated_returns_tuple(self):
        """Should return tuple of clusters and total count."""
        mock_session = AsyncMock()

        # Mock for count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        # Mock for data query
        mock_data_result = MagicMock()
        mock_data_result.scalars.return_value.all.return_value = []

        # Return different results for each execute call
        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_data_result]
        )

        repo = ClusterRepository(mock_session)
        clusters, total = await repo.get_clusters_paginated(
            status="active",
            min_articles=2,
            hours=24,
            limit=10,
            offset=0
        )

        assert isinstance(clusters, list)
        assert total == 10

    @pytest.mark.asyncio
    async def test_update_cluster_sets_breaking_news(self):
        """Should set is_breaking and burst_detected_at when is_breaking=True."""
        mock_session = AsyncMock()
        mock_cluster = MagicMock()
        mock_cluster.article_count = 1
        mock_cluster.centroid_vector = [0.1, 0.2]
        mock_cluster.is_breaking = False
        mock_cluster.burst_detected_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)
        await repo.update_cluster(
            cluster_id=uuid4(),
            new_centroid=[0.15, 0.25],
            new_article_count=5,
            is_breaking=True
        )

        assert mock_cluster.is_breaking is True
        assert mock_cluster.burst_detected_at is not None

    @pytest.mark.asyncio
    async def test_update_cluster_updates_entities(self):
        """Should update primary_entities when provided."""
        mock_session = AsyncMock()
        mock_cluster = MagicMock()
        mock_cluster.article_count = 1
        mock_cluster.centroid_vector = [0.1, 0.2]
        mock_cluster.is_breaking = False
        mock_cluster.primary_entities = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        entities = [{"id": "1", "name": "Entity1", "type": "PERSON"}]

        repo = ClusterRepository(mock_session)
        await repo.update_cluster(
            cluster_id=uuid4(),
            new_centroid=[0.15, 0.25],
            new_article_count=2,
            entities=entities
        )

        assert mock_cluster.primary_entities == entities

    @pytest.mark.asyncio
    async def test_update_cluster_updates_tension_score(self):
        """Should update tension_score when provided."""
        mock_session = AsyncMock()
        mock_cluster = MagicMock()
        mock_cluster.article_count = 1
        mock_cluster.centroid_vector = [0.1, 0.2]
        mock_cluster.is_breaking = False
        mock_cluster.tension_score = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)
        await repo.update_cluster(
            cluster_id=uuid4(),
            new_centroid=[0.15, 0.25],
            new_article_count=2,
            tension_score=7.5
        )

        assert mock_cluster.tension_score == 7.5

    @pytest.mark.asyncio
    async def test_create_cluster_truncates_long_title(self):
        """Should truncate title to 500 characters."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        long_title = "A" * 600  # 600 characters

        repo = ClusterRepository(mock_session)
        cluster_id = await repo.create_cluster(
            title=long_title,
            centroid_vector=[0.1, 0.2, 0.3],
            first_article_id=uuid4()
        )

        # Verify cluster was added with truncated title
        assert cluster_id is not None
        add_call = mock_session.add.call_args[0][0]
        assert len(add_call.title) == 500

    @pytest.mark.asyncio
    async def test_get_active_clusters_filters_null_centroids(self):
        """Should filter out clusters with null centroid vectors."""
        mock_session = AsyncMock()

        # Create mock clusters - one with centroid, one without
        mock_cluster_with_centroid = MagicMock()
        mock_cluster_with_centroid.id = uuid4()
        mock_cluster_with_centroid.centroid_vector = [0.1, 0.2]
        mock_cluster_with_centroid.article_count = 5
        mock_cluster_with_centroid.title = "Valid Cluster"

        mock_cluster_without_centroid = MagicMock()
        mock_cluster_without_centroid.id = uuid4()
        mock_cluster_without_centroid.centroid_vector = None
        mock_cluster_without_centroid.article_count = 3
        mock_cluster_without_centroid.title = "Invalid Cluster"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_cluster_with_centroid,
            mock_cluster_without_centroid
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        clusters = await repo.get_active_clusters(max_age_hours=24)

        # Should only include the cluster with a centroid
        assert len(clusters) == 1
        assert clusters[0]["title"] == "Valid Cluster"
