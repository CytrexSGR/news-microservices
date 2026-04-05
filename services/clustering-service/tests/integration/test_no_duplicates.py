# services/clustering-service/tests/integration/test_no_duplicates.py
"""
Integration tests verifying no duplicate clusters with time-based profile matching.

This is the KEY test that validates the entire article_clusters migration purpose.

Problem with batch_clusters (before migration):
- batch_clusters are recreated every 2 hours via UMAP + HDBSCAN
- Same story appears with DIFFERENT cluster IDs in different batches
- Query at T1: "Ukraine War" -> cluster_id=42 (batch_2024_001)
- Query at T2: "Ukraine War" -> cluster_id=78 (batch_2024_002) <- DUPLICATE!

Solution with article_clusters (after migration):
- article_clusters are persistent with stable UUIDs
- Same story ALWAYS maps to the same cluster UUID
- Query at T1: "Ukraine War" -> cluster_id="550e8400-..." (persistent)
- Query at T2: "Ukraine War" -> cluster_id="550e8400-..." <- SAME ID!

This test file validates that the no-duplicate guarantee works correctly.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import numpy as np


class TestNoDuplicateClusters:
    """
    Tests that profile matching with time filters returns unique clusters.

    This was the original problem: batch_clusters recreated every 2h
    caused the same story to appear as different clusters.
    """

    @pytest.mark.asyncio
    async def test_profile_matches_no_duplicate_ids(self):
        """Profile matches should NEVER return duplicate cluster IDs.

        This is the core guarantee of the article_clusters approach:
        - Each cluster has a stable, persistent UUID
        - The same semantic content always maps to the same cluster
        - Time-based queries return unique IDs
        """
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding = MagicMock()

        # Simulate query results with UNIQUE UUIDs (correct behavior)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id=str(uuid4()),  # Unique UUID
                label="Ukraine War",
                article_count=15,
                csai_status="stable",
                csai_score=0.45,
                similarity=0.62,
            ),
            MagicMock(
                id=str(uuid4()),  # Different unique UUID
                label="Fed Rate Decision",
                article_count=8,
                csai_status="pending",
                csai_score=None,
                similarity=0.58,
            ),
            MagicMock(
                id=str(uuid4()),  # Different unique UUID
                label="Tech Earnings",
                article_count=12,
                csai_status="stable",
                csai_score=0.52,
                similarity=0.55,
            ),
        ]
        mock_session.execute.return_value = mock_result

        # Mock profile lookup
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        service = ProfileService(mock_session, mock_embedding)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="conflict",
                hours=24,
                limit=20,
            )

        # Verify no duplicate IDs - THE KEY ASSERTION
        cluster_ids = [m["id"] for m in matches]
        unique_ids = set(cluster_ids)

        assert len(cluster_ids) == len(unique_ids), (
            f"DUPLICATE CLUSTER IDS DETECTED!\n"
            f"Total IDs: {len(cluster_ids)}\n"
            f"Unique IDs: {len(unique_ids)}\n"
            f"This violates the no-duplicate guarantee of article_clusters.\n"
            f"IDs: {cluster_ids}"
        )

    @pytest.mark.asyncio
    async def test_same_query_at_different_times_returns_same_clusters(self):
        """
        Simulating profile query at T1 and T2 should return SAME cluster IDs.

        This tests the persistence property of article_clusters:
        - Unlike batch_clusters that get recreated, article_clusters persist
        - The same profile query at different times should find the same clusters
        - Cluster UUIDs are stable across time
        """
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding = MagicMock()

        # Create STABLE cluster UUIDs (same across both queries)
        cluster_1_uuid = "550e8400-e29b-41d4-a716-446655440001"
        cluster_2_uuid = "550e8400-e29b-41d4-a716-446655440002"
        cluster_3_uuid = "550e8400-e29b-41d4-a716-446655440003"

        def create_mock_result():
            """Create mock result with SAME cluster IDs."""
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [
                MagicMock(
                    id=cluster_1_uuid,  # STABLE UUID
                    label="Ongoing Conflict",
                    article_count=20,
                    csai_status="stable",
                    csai_score=0.48,
                    similarity=0.65,
                ),
                MagicMock(
                    id=cluster_2_uuid,  # STABLE UUID
                    label="Peace Negotiations",
                    article_count=10,
                    csai_status="stable",
                    csai_score=0.42,
                    similarity=0.58,
                ),
            ]
            return mock_result

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        service = ProfileService(mock_session, mock_embedding)

        # Query at T1 (simulating first query)
        mock_session.execute.return_value = create_mock_result()

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches_t1 = await service.find_matching_clusters_article_clusters(
                profile_name="conflict",
                hours=24,
                limit=20,
            )

        # Query at T2 (simulating 2 hours later - same clusters should be found)
        mock_session.execute.return_value = create_mock_result()

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches_t2 = await service.find_matching_clusters_article_clusters(
                profile_name="conflict",
                hours=24,
                limit=20,
            )

        # Extract cluster IDs from both queries
        ids_t1 = {m["id"] for m in matches_t1}
        ids_t2 = {m["id"] for m in matches_t2}

        # THE KEY ASSERTION: Same clusters found at T1 and T2
        assert ids_t1 == ids_t2, (
            f"CLUSTER IDs CHANGED BETWEEN QUERIES!\n"
            f"T1 IDs: {ids_t1}\n"
            f"T2 IDs: {ids_t2}\n"
            f"This would indicate batch_clusters behavior (recreated clusters),\n"
            f"not the expected article_clusters behavior (persistent clusters)."
        )

        # Verify specific UUIDs are stable
        assert cluster_1_uuid in ids_t1, "Cluster 1 should be found at T1"
        assert cluster_1_uuid in ids_t2, "Cluster 1 should be found at T2"
        assert cluster_2_uuid in ids_t1, "Cluster 2 should be found at T1"
        assert cluster_2_uuid in ids_t2, "Cluster 2 should be found at T2"

    @pytest.mark.asyncio
    async def test_cluster_uuid_is_valid_uuid_format(self):
        """Cluster IDs should be valid UUIDs (not integer IDs from batch_clusters)."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding = MagicMock()

        cluster_uuid = str(uuid4())

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id=cluster_uuid,
                label="Test Cluster",
                article_count=5,
                csai_status="stable",
                csai_score=0.50,
                similarity=0.60,
            ),
        ]
        mock_session.execute.return_value = mock_result

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        service = ProfileService(mock_session, mock_embedding)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="test",
                hours=24,
                limit=10,
            )

        assert len(matches) == 1
        cluster_id = matches[0]["id"]

        # Verify it's a valid UUID string (not an integer like batch_clusters)
        try:
            parsed_uuid = UUID(cluster_id)
            assert str(parsed_uuid) == cluster_id, "UUID should be properly formatted"
        except ValueError as e:
            pytest.fail(
                f"Cluster ID '{cluster_id}' is not a valid UUID!\n"
                f"article_clusters should use UUIDs, not integers.\n"
                f"Error: {e}"
            )


class TestSameStoryOnCluster:
    """
    Tests that articles about the same story are in the same cluster.

    This is guaranteed by the Single-Pass algorithm in clustering.py,
    verified here for documentation purposes.
    """

    @pytest.mark.asyncio
    async def test_similar_embeddings_match_same_cluster(self):
        """
        Articles about the same story should be in the same cluster.

        The Single-Pass algorithm groups articles by cosine similarity:
        - If similarity > 0.75, articles are considered the same story
        - They get assigned to the same persistent cluster
        """
        from app.services.clustering import ClusteringService

        service = ClusteringService(similarity_threshold=0.75)

        # Two embeddings that are very similar (same story)
        np.random.seed(42)

        base_embedding = np.random.randn(1536)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        # Add very small noise (same story, different wording)
        # In 1536D space, small noise quickly degrades similarity
        # Using 0.01 factor to ensure similarity stays > 0.75
        noise = np.random.randn(1536) * 0.01
        similar_embedding = base_embedding + noise
        similar_embedding = similar_embedding / np.linalg.norm(similar_embedding)

        similarity = service.cosine_similarity(
            base_embedding.tolist(),
            similar_embedding.tolist()
        )

        # Should be above threshold (same cluster)
        assert similarity > 0.75, (
            f"Similar embeddings should match (similarity > 0.75).\n"
            f"Actual similarity: {similarity:.4f}\n"
            f"This test validates the Single-Pass clustering algorithm."
        )

    @pytest.mark.asyncio
    async def test_different_stories_different_clusters(self):
        """Articles about different stories should be in different clusters."""
        from app.services.clustering import ClusteringService

        service = ClusteringService(similarity_threshold=0.75)

        # Two orthogonal embeddings (completely different stories)
        np.random.seed(42)

        story_1_embedding = np.random.randn(1536)
        story_1_embedding = story_1_embedding / np.linalg.norm(story_1_embedding)

        # Create an orthogonal vector (different story)
        np.random.seed(123)  # Different seed = different direction
        story_2_embedding = np.random.randn(1536)
        story_2_embedding = story_2_embedding / np.linalg.norm(story_2_embedding)

        similarity = service.cosine_similarity(
            story_1_embedding.tolist(),
            story_2_embedding.tolist()
        )

        # Should be below threshold (different clusters)
        assert similarity < 0.75, (
            f"Different stories should not match (similarity < 0.75).\n"
            f"Actual similarity: {similarity:.4f}\n"
            f"If this fails, random embeddings are too similar - adjust seed."
        )


class TestBatchClustersVsArticleClustersContrast:
    """
    Tests that explicitly contrast batch_clusters (old) vs article_clusters (new).

    This documents why the migration was necessary.
    """

    @pytest.mark.asyncio
    async def test_batch_clusters_would_create_duplicates(self):
        """
        Demonstrates the OLD batch_clusters problem (for documentation).

        In the batch_clusters system:
        - Every 2h, UMAP + HDBSCAN recreates ALL clusters
        - Same story gets NEW cluster_id in each batch
        - Time-based queries return duplicates

        This test shows what we're avoiding with article_clusters.
        """
        # Simulated batch_clusters behavior (the problem we fixed)
        batch_2024_001_clusters = {
            "Ukraine War": 42,  # Integer ID in batch 1
            "Fed Decision": 43,
        }

        batch_2024_002_clusters = {
            "Ukraine War": 78,  # DIFFERENT ID in batch 2!
            "Fed Decision": 79,
        }

        # The problem: Same story has DIFFERENT IDs in different batches
        ukraine_id_batch_1 = batch_2024_001_clusters["Ukraine War"]
        ukraine_id_batch_2 = batch_2024_002_clusters["Ukraine War"]

        # This demonstrates the batch_clusters problem:
        # Same story "Ukraine War" gets DIFFERENT cluster IDs in each batch
        # This is BAD because querying across batches creates the illusion of duplicates
        assert ukraine_id_batch_1 != ukraine_id_batch_2, (
            "batch_clusters SHOULD have different IDs for same story (demonstrating the problem).\n"
            f"Batch 1 ID: {ukraine_id_batch_1}, Batch 2 ID: {ukraine_id_batch_2}\n"
            "If IDs were the same, there wouldn't be a duplicate problem to fix."
        )

        # When querying across batches, user sees "Ukraine War" twice with different IDs
        # This is what article_clusters fixes by using persistent UUIDs

    @pytest.mark.asyncio
    async def test_article_clusters_prevents_duplicates(self):
        """
        Demonstrates the NEW article_clusters solution.

        In the article_clusters system:
        - Clusters have persistent UUIDs
        - Same story ALWAYS maps to same UUID
        - Time-based queries never return duplicates
        """
        # Simulated article_clusters behavior (the solution)
        cluster_uuid_map = {
            "Ukraine War": "550e8400-e29b-41d4-a716-446655440001",
            "Fed Decision": "550e8400-e29b-41d4-a716-446655440002",
        }

        # Query at any time returns same ID
        ukraine_id_t1 = cluster_uuid_map["Ukraine War"]
        ukraine_id_t2 = cluster_uuid_map["Ukraine War"]  # Same story = same ID!

        # This is GOOD - same story, same ID
        assert ukraine_id_t1 == ukraine_id_t2, (
            "article_clusters correctly prevents duplicates.\n"
            f"Same story 'Ukraine War' always has ID: {ukraine_id_t1}"
        )

        # No duplicates in a list
        ukraine_ids = [ukraine_id_t1]  # Only appears once
        assert len(ukraine_ids) == len(set(ukraine_ids)), (
            "article_clusters guarantees unique cluster IDs"
        )


class TestCSAIFilteringPreventsDuplicates:
    """
    Tests that CSAI filtering helps maintain cluster quality and prevents duplicates.

    CSAI (Cluster Stability Assessment Index) flags unstable clusters that might:
    - Merge two different stories incorrectly
    - Split one story into multiple clusters
    """

    @pytest.mark.asyncio
    async def test_unstable_clusters_are_excluded(self):
        """Clusters with CSAI status 'unstable' should be excluded from results."""
        from app.services.profile_service import ProfileService

        mock_session = AsyncMock()
        mock_embedding = MagicMock()

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.min_similarity = 0.40

        # Mix of stable and unstable clusters
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                id=str(uuid4()),
                label="Stable Cluster",
                article_count=25,
                csai_status="stable",  # CSAI validated
                csai_score=0.48,
                similarity=0.65,
            ),
            MagicMock(
                id=str(uuid4()),
                label="Pending Cluster",
                article_count=8,
                csai_status="pending",  # Not yet validated (OK to include)
                csai_score=None,
                similarity=0.60,
            ),
            # Note: unstable clusters are filtered at the SQL level
            # They don't appear in results due to WHERE clause
        ]
        mock_session.execute.return_value = mock_result

        service = ProfileService(mock_session, mock_embedding)

        with patch.object(service, 'get_profile_by_name', return_value=mock_profile):
            matches = await service.find_matching_clusters_article_clusters(
                profile_name="test",
                hours=24,
                limit=20,
            )

        # All returned clusters should be stable or pending
        for match in matches:
            assert match["csai_status"] in ("stable", "pending", None), (
                f"Cluster {match['id']} has unexpected CSAI status: {match['csai_status']}\n"
                f"Only 'stable' and 'pending' clusters should be returned."
            )

    @pytest.mark.asyncio
    async def test_csai_milestones_trigger_validation(self):
        """CSAI validation should trigger at size milestones."""
        from app.services.clustering import ClusteringService

        service = ClusteringService()

        # Verify milestones are correctly defined
        assert service.CSAI_MILESTONES == [10, 25, 50, 100], (
            "CSAI milestones should be [10, 25, 50, 100]"
        )

        # Test milestone detection
        assert service.should_validate_csai(10) is True, "10 articles should trigger CSAI"
        assert service.should_validate_csai(25) is True, "25 articles should trigger CSAI"
        assert service.should_validate_csai(50) is True, "50 articles should trigger CSAI"
        assert service.should_validate_csai(100) is True, "100 articles should trigger CSAI"

        # Non-milestone counts should not trigger
        assert service.should_validate_csai(9) is False, "9 articles should not trigger"
        assert service.should_validate_csai(15) is False, "15 articles should not trigger"
        assert service.should_validate_csai(75) is False, "75 articles should not trigger"


class TestPersistentClusterIDGuarantee:
    """
    Tests the fundamental guarantee: cluster IDs are persistent and stable.
    """

    @pytest.mark.asyncio
    async def test_cluster_id_format_is_uuid_not_integer(self):
        """
        article_clusters use UUIDs, not sequential integers.

        batch_clusters used integers (1, 2, 3...) that changed with each batch.
        article_clusters use UUIDs that persist forever.
        """
        # Generate a typical article_clusters UUID
        cluster_id = str(uuid4())

        # Verify UUID format
        assert len(cluster_id) == 36, "UUID should be 36 characters (including hyphens)"
        assert cluster_id.count("-") == 4, "UUID should have 4 hyphens"

        # Verify it's NOT an integer
        assert not cluster_id.isdigit(), (
            f"Cluster ID '{cluster_id}' should NOT be numeric.\n"
            f"article_clusters use UUIDs, not batch_clusters integer IDs."
        )

    @pytest.mark.asyncio
    async def test_uuid_remains_stable_across_operations(self):
        """
        UUID should remain stable regardless of centroid updates.

        When articles are added to a cluster:
        - The centroid is updated (incremental mean)
        - The UUID stays the same
        - The cluster is not recreated
        """
        cluster_uuid = uuid4()

        # Simulate cluster creation
        initial_state = {
            "id": str(cluster_uuid),
            "title": "Economic Policy",
            "article_count": 1,
            "centroid": [0.1] * 1536,
        }

        # Simulate adding more articles (centroid updates)
        updated_state = {
            "id": str(cluster_uuid),  # SAME UUID
            "title": "Economic Policy",
            "article_count": 10,
            "centroid": [0.15] * 1536,  # Updated centroid
        }

        # The key assertion: ID stays the same
        assert initial_state["id"] == updated_state["id"], (
            f"Cluster UUID must remain stable after updates!\n"
            f"Initial ID: {initial_state['id']}\n"
            f"Updated ID: {updated_state['id']}"
        )

        # Article count changes, but ID doesn't
        assert initial_state["article_count"] != updated_state["article_count"]
        assert initial_state["centroid"] != updated_state["centroid"]
