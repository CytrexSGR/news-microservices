"""Tests for pgvector-based cluster search methods.

Task 4: Add pgvector search to ClusterRepository.
Tests for find_matching_cluster_pgvector, update_cluster_pgvector,
update_csai_status, and create_cluster_with_pgvector methods.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.cluster_repository import ClusterRepository


class TestPgvectorSearchMethods:
    """Tests for pgvector-based cluster search methods."""

    @pytest.mark.asyncio
    async def test_find_matching_cluster_pgvector_method_exists(self):
        """Method find_matching_cluster_pgvector should exist on ClusterRepository."""
        mock_session = AsyncMock()
        repo = ClusterRepository(mock_session)

        assert hasattr(repo, 'find_matching_cluster_pgvector')
        assert callable(repo.find_matching_cluster_pgvector)

    @pytest.mark.asyncio
    async def test_find_matching_cluster_pgvector_no_match(self):
        """Returns None when no cluster matches the similarity threshold."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        embedding = [0.1] * 1536
        result = await repo.find_matching_cluster_pgvector(embedding)

        assert result is None

    @pytest.mark.asyncio
    async def test_find_matching_cluster_pgvector_returns_match(self):
        """Returns cluster dict when a match is found above threshold."""
        mock_session = AsyncMock()
        cluster_id = uuid4()

        # Mock a matching cluster row
        mock_row = MagicMock()
        mock_row.id = cluster_id
        mock_row.title = "Ukraine War Updates"
        mock_row.article_count = 15
        mock_row.csai_status = "stable"
        mock_row.similarity = 0.82

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        embedding = [0.1] * 1536
        result = await repo.find_matching_cluster_pgvector(embedding, similarity_threshold=0.75)

        assert result is not None
        assert result["id"] == cluster_id
        assert result["title"] == "Ukraine War Updates"
        assert result["article_count"] == 15
        assert result["csai_status"] == "stable"
        assert result["similarity"] == 0.82

    @pytest.mark.asyncio
    async def test_find_matching_cluster_pgvector_uses_threshold(self):
        """Should pass threshold to the query."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        embedding = [0.1] * 1536
        await repo.find_matching_cluster_pgvector(embedding, similarity_threshold=0.85)

        # Verify execute was called with threshold parameter
        call_args = mock_session.execute.call_args
        assert call_args is not None
        params = call_args[0][1]  # Second positional arg is the params dict
        assert params["threshold"] == 0.85


class TestUpdateClusterPgvector:
    """Tests for update_cluster_pgvector method."""

    @pytest.mark.asyncio
    async def test_update_cluster_pgvector_method_exists(self):
        """Method update_cluster_pgvector should exist."""
        mock_session = AsyncMock()
        repo = ClusterRepository(mock_session)

        assert hasattr(repo, 'update_cluster_pgvector')
        assert callable(repo.update_cluster_pgvector)

    @pytest.mark.asyncio
    async def test_update_cluster_pgvector_returns_true_on_success(self):
        """Returns True when cluster is updated successfully."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        cluster_id = uuid4()
        new_centroid = [0.2] * 1536
        result = await repo.update_cluster_pgvector(
            cluster_id=cluster_id,
            new_centroid=new_centroid,
            new_article_count=5
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_cluster_pgvector_returns_false_when_not_found(self):
        """Returns False when cluster is not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        cluster_id = uuid4()
        new_centroid = [0.2] * 1536
        result = await repo.update_cluster_pgvector(
            cluster_id=cluster_id,
            new_centroid=new_centroid,
            new_article_count=5
        )

        assert result is False


class TestUpdateCsaiStatus:
    """Tests for update_csai_status method."""

    @pytest.mark.asyncio
    async def test_update_csai_status_method_exists(self):
        """Method update_csai_status should exist."""
        mock_session = AsyncMock()
        repo = ClusterRepository(mock_session)

        assert hasattr(repo, 'update_csai_status')
        assert callable(repo.update_csai_status)

    @pytest.mark.asyncio
    async def test_update_csai_status_returns_true_on_success(self):
        """Returns True when CSAI status is updated successfully."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        cluster_id = uuid4()
        result = await repo.update_csai_status(
            cluster_id=cluster_id,
            csai_score=0.42,
            csai_status="stable"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_csai_status_returns_false_when_not_found(self):
        """Returns False when cluster is not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        cluster_id = uuid4()
        result = await repo.update_csai_status(
            cluster_id=cluster_id,
            csai_score=0.25,
            csai_status="unstable"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_csai_status_accepts_valid_statuses(self):
        """Should accept 'stable', 'unstable', and 'pending' statuses."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)
        cluster_id = uuid4()

        # Test all valid statuses
        for status in ["stable", "unstable", "pending"]:
            result = await repo.update_csai_status(
                cluster_id=cluster_id,
                csai_score=0.35,
                csai_status=status
            )
            assert result is True


class TestCreateClusterWithPgvector:
    """Tests for create_cluster_with_pgvector method."""

    @pytest.mark.asyncio
    async def test_create_cluster_with_pgvector_method_exists(self):
        """Method create_cluster_with_pgvector should exist."""
        mock_session = AsyncMock()
        repo = ClusterRepository(mock_session)

        assert hasattr(repo, 'create_cluster_with_pgvector')
        assert callable(repo.create_cluster_with_pgvector)

    @pytest.mark.asyncio
    async def test_create_cluster_with_pgvector_returns_uuid(self):
        """Should return a UUID for the created cluster."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)

        centroid = [0.1] * 1536
        cluster_id = await repo.create_cluster_with_pgvector(
            title="New Story Cluster",
            centroid_vector=centroid,
            first_article_id=uuid4()
        )

        assert cluster_id is not None
        # Should be a UUID
        from uuid import UUID
        assert isinstance(cluster_id, UUID)

    @pytest.mark.asyncio
    async def test_create_cluster_with_pgvector_commits_transaction(self):
        """Should commit the transaction after creating cluster."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)

        centroid = [0.1] * 1536
        await repo.create_cluster_with_pgvector(
            title="New Story",
            centroid_vector=centroid,
            first_article_id=uuid4()
        )

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_cluster_with_pgvector_truncates_long_title(self):
        """Should truncate title to 500 characters."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        repo = ClusterRepository(mock_session)

        long_title = "A" * 600
        centroid = [0.1] * 1536

        await repo.create_cluster_with_pgvector(
            title=long_title,
            centroid_vector=centroid,
            first_article_id=uuid4()
        )

        # Verify execute was called with truncated title
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert len(params["title"]) == 500


class TestPgvectorQueryFormat:
    """Tests for correct pgvector query format."""

    @pytest.mark.asyncio
    async def test_embedding_format_for_pgvector(self):
        """Embedding should be formatted as '[0.1,0.2,...]' for pgvector."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        # Small embedding for testing format
        embedding = [0.1, 0.2, 0.3]
        await repo.find_matching_cluster_pgvector(embedding)

        # Get the embedding parameter passed to execute
        call_args = mock_session.execute.call_args
        params = call_args[0][1]

        # Should be formatted as "[0.1,0.2,0.3]"
        expected = "[0.1,0.2,0.3]"
        assert params["embedding"] == expected

    @pytest.mark.asyncio
    async def test_max_age_hours_parameter(self):
        """Should pass max_age_hours as interval to query."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClusterRepository(mock_session)

        embedding = [0.1] * 1536
        await repo.find_matching_cluster_pgvector(embedding, max_age_hours=48)

        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["hours"] == "48 hours"
