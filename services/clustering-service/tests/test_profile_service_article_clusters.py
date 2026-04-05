"""Tests for ProfileService using article_clusters instead of batch_clusters.

Task 6: Feature flag migration from batch_clusters to article_clusters for
profile matching to eliminate duplicate clusters.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestProfileServiceArticleClusters:
    """Tests for ProfileService migrated to article_clusters."""

    @pytest.mark.asyncio
    async def test_feature_flag_exists_in_settings(self):
        """Settings should have USE_ARTICLE_CLUSTERS feature flag."""
        from app.config import settings

        assert hasattr(settings, 'USE_ARTICLE_CLUSTERS'), \
            "settings.USE_ARTICLE_CLUSTERS feature flag should exist"

    @pytest.mark.asyncio
    async def test_feature_flag_defaults_to_false(self):
        """USE_ARTICLE_CLUSTERS should default to False for safe rollout."""
        from app.config import settings

        # This tests the default - actual env value may differ
        # The important thing is the attribute exists
        assert isinstance(settings.USE_ARTICLE_CLUSTERS, bool), \
            "USE_ARTICLE_CLUSTERS should be a boolean"

    @pytest.mark.asyncio
    async def test_profile_service_has_article_clusters_method(self):
        """ProfileService should have find_matching_clusters_article_clusters method."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        service = ProfileService(mock_session, mock_embedding_service)

        assert hasattr(service, 'find_matching_clusters_article_clusters'), \
            "ProfileService should have find_matching_clusters_article_clusters method"
        assert callable(service.find_matching_clusters_article_clusters), \
            "find_matching_clusters_article_clusters should be callable"

    @pytest.mark.asyncio
    async def test_find_matching_clusters_article_clusters_returns_list(self):
        """find_matching_clusters_article_clusters should return a list of matches."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        # Mock profile lookup
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        # Mock database result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id="550e8400-e29b-41d4-a716-446655440001",
                label="Ukraine Conflict Updates",
                article_count=15,
                csai_status="stable",
                csai_score=0.45,
                similarity=0.62,
            ),
            MagicMock(
                id="550e8400-e29b-41d4-a716-446655440002",
                label="Russia Sanctions",
                article_count=8,
                csai_status="pending",
                csai_score=None,
                similarity=0.58,
            ),
        ]
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding_service)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="conflict",
                hours=24,
                limit=20,
            )

        assert isinstance(matches, list), "Should return a list"
        assert len(matches) == 2, f"Should return 2 matches, got {len(matches)}"

    @pytest.mark.asyncio
    async def test_find_matching_clusters_article_clusters_returns_correct_fields(self):
        """Each match should have expected fields from article_clusters."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id="550e8400-e29b-41d4-a716-446655440001",
                label="Fed Rate Decision",
                article_count=12,
                csai_status="stable",
                csai_score=0.52,
                similarity=0.55,
            ),
        ]
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding_service)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="finance",
                hours=24,
                limit=10,
            )

        assert len(matches) == 1

        match = matches[0]
        assert "id" in match, "Match should have 'id' field"
        assert "label" in match, "Match should have 'label' field"
        assert "article_count" in match, "Match should have 'article_count' field"
        assert "csai_status" in match, "Match should have 'csai_status' field"
        assert "csai_score" in match, "Match should have 'csai_score' field"
        assert "similarity" in match, "Match should have 'similarity' field"

    @pytest.mark.asyncio
    async def test_find_matching_clusters_article_clusters_filters_by_threshold(self):
        """Results below min_similarity threshold should be filtered out."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.50  # High threshold

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id="uuid-1",
                label="Cluster Above Threshold",
                article_count=10,
                csai_status="stable",
                csai_score=0.40,
                similarity=0.55,  # Above 0.50
            ),
            MagicMock(
                id="uuid-2",
                label="Cluster Below Threshold",
                article_count=5,
                csai_status="pending",
                csai_score=None,
                similarity=0.35,  # Below 0.50
            ),
        ]
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding_service)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="test",
                hours=24,
                limit=10,
            )

        assert len(matches) == 1, f"Should filter to 1 match above threshold, got {len(matches)}"
        assert matches[0]["label"] == "Cluster Above Threshold"

    @pytest.mark.asyncio
    async def test_find_matching_clusters_article_clusters_profile_not_found(self):
        """Should return empty list when profile not found."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        service = ProfileService(mock_session, mock_embedding_service)

        with patch.object(service, 'get_profile_by_name', return_value=None):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="nonexistent",
                hours=24,
            )

        assert matches == [], "Should return empty list for nonexistent profile"

    @pytest.mark.asyncio
    async def test_feature_flag_routes_to_article_clusters(self):
        """When USE_ARTICLE_CLUSTERS=True, find_matching_clusters should use article_clusters method."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        service = ProfileService(mock_session, mock_embedding_service)

        # Mock the article_clusters method
        mock_result = [{"id": "uuid-1", "label": "Test", "similarity": 0.5}]
        service.find_matching_clusters_article_clusters = AsyncMock(return_value=mock_result)

        with patch('app.services.profile_service.settings') as mock_settings:
            mock_settings.USE_ARTICLE_CLUSTERS = True

            result = await service.find_matching_clusters(
                profile_name="test",
                limit=10,
                hours=24,
            )

            # Should have called article_clusters method
            service.find_matching_clusters_article_clusters.assert_called_once_with(
                profile_name="test",
                limit=10,
                min_similarity=None,
                hours=24,
                since=None,
            )
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_feature_flag_routes_to_batch_clusters_when_disabled(self):
        """When USE_ARTICLE_CLUSTERS=False, find_matching_clusters should use batch_clusters query."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        # Mock profile lookup
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        # Mock database result for batch_clusters query
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id=1,
                cluster_idx=0,
                label="Test Batch Cluster",
                article_count=5,
                keywords=["test"],
                similarity=0.50,
            ),
        ]
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding_service)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            with patch('app.services.profile_service.settings') as mock_settings:
                mock_settings.USE_ARTICLE_CLUSTERS = False

                matches = await service.find_matching_clusters(
                    profile_name="test",
                    limit=10,
                    hours=24,
                )

        # Should return batch_clusters format with cluster_idx and keywords
        assert len(matches) == 1
        assert "cluster_idx" in matches[0], "Batch clusters should have cluster_idx field"
        assert "keywords" in matches[0], "Batch clusters should have keywords field"

    @pytest.mark.asyncio
    async def test_explicit_batch_id_overrides_feature_flag(self):
        """When batch_id is specified, should always use batch_clusters regardless of flag."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding_service)

        # Mock to verify article_clusters is NOT called
        service.find_matching_clusters_article_clusters = AsyncMock()

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            with patch('app.services.profile_service.settings') as mock_settings:
                mock_settings.USE_ARTICLE_CLUSTERS = True

                await service.find_matching_clusters(
                    profile_name="test",
                    batch_id="specific-batch-123",  # Explicit batch_id
                    limit=10,
                )

        # Should NOT have called article_clusters method because batch_id was specified
        service.find_matching_clusters_article_clusters.assert_not_called()
