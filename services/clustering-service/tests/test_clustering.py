"""Tests for clustering service."""

import pytest
import numpy as np
from uuid import uuid4

from app.services.clustering import ClusteringService


class TestCosineSimialrity:
    """Tests for cosine similarity calculation."""

    def test_cosine_similarity_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        service = ClusteringService()
        vec = [0.5, 0.5, 0.5, 0.5]
        similarity = service.cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, rel=1e-6)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        service = ClusteringService()
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, rel=1e-6)

    def test_cosine_similarity_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        service = ClusteringService()
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0, rel=1e-6)

    def test_cosine_similarity_similar_vectors(self):
        """Similar vectors should have high similarity."""
        service = ClusteringService()
        vec1 = [0.9, 0.1, 0.0]
        vec2 = [0.85, 0.15, 0.05]
        similarity = service.cosine_similarity(vec1, vec2)
        assert similarity > 0.9

    def test_cosine_similarity_zero_vector(self):
        """Zero vector should return 0.0 similarity."""
        service = ClusteringService()
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_high_dimensional(self):
        """Should work with high-dimensional vectors (384-dim embeddings)."""
        service = ClusteringService()
        vec1 = [0.1] * 384
        vec2 = [0.1] * 384
        similarity = service.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, rel=1e-6)


class TestUpdateCentroid:
    """Tests for centroid update using incremental mean."""

    def test_update_centroid_first_article(self):
        """First article becomes the centroid."""
        service = ClusteringService()
        vec = [0.5, 0.5]
        new_centroid = service.update_centroid(None, vec, 1)
        assert new_centroid == [0.5, 0.5]

    def test_update_centroid_first_article_with_count_one(self):
        """With count=1, new vector replaces any existing centroid."""
        service = ClusteringService()
        current = [0.1, 0.1]
        new_vec = [0.9, 0.9]
        new_centroid = service.update_centroid(current, new_vec, 1)
        assert new_centroid == [0.9, 0.9]

    def test_update_centroid_running_average_two_articles(self):
        """Centroid should be average after 2 articles."""
        service = ClusteringService()
        current = [0.0, 1.0]
        new_vec = [1.0, 0.0]
        # After 2 articles, centroid should be average
        new_centroid = service.update_centroid(current, new_vec, 2)
        assert new_centroid == pytest.approx([0.5, 0.5], rel=1e-6)

    def test_update_centroid_running_average_three_articles(self):
        """Centroid should be weighted average after 3 articles."""
        service = ClusteringService()
        # Current centroid is average of [0.0, 1.0] and [1.0, 0.0] = [0.5, 0.5]
        current = [0.5, 0.5]
        new_vec = [0.5, 0.5]
        # After 3 articles, centroid stays [0.5, 0.5]
        new_centroid = service.update_centroid(current, new_vec, 3)
        assert new_centroid == pytest.approx([0.5, 0.5], rel=1e-6)

    def test_update_centroid_incremental_mean_formula(self):
        """Verify incremental mean formula: new = old + (val - old) / n."""
        service = ClusteringService()
        # Simulate adding 4th article
        current = [0.3, 0.6]
        new_vec = [0.7, 0.2]
        new_centroid = service.update_centroid(current, new_vec, 4)
        # Expected: [0.3 + (0.7-0.3)/4, 0.6 + (0.2-0.6)/4] = [0.4, 0.5]
        assert new_centroid == pytest.approx([0.4, 0.5], rel=1e-6)


class TestFindMatchingCluster:
    """Tests for finding matching clusters."""

    def test_find_matching_cluster_no_clusters(self):
        """No clusters returns None."""
        service = ClusteringService()
        result = service.find_matching_cluster([0.5, 0.5], [])
        assert result is None

    def test_find_matching_cluster_above_threshold(self):
        """Should find cluster above similarity threshold."""
        service = ClusteringService(similarity_threshold=0.75)
        embedding = [0.9, 0.1]
        cluster_id_1 = uuid4()
        cluster_id_2 = uuid4()
        clusters = [
            {"id": cluster_id_1, "centroid": [0.85, 0.15]},  # Similar
            {"id": cluster_id_2, "centroid": [0.1, 0.9]},    # Different
        ]
        result = service.find_matching_cluster(embedding, clusters)
        assert result is not None
        assert result["cluster_id"] == cluster_id_1
        assert result["similarity"] > 0.75

    def test_find_matching_cluster_below_threshold(self):
        """Should return None if no cluster above threshold."""
        service = ClusteringService(similarity_threshold=0.95)
        embedding = [0.5, 0.5]
        clusters = [
            {"id": uuid4(), "centroid": [0.7, 0.3]},
        ]
        result = service.find_matching_cluster(embedding, clusters)
        assert result is None

    def test_find_matching_cluster_selects_best_match(self):
        """Should select cluster with highest similarity."""
        service = ClusteringService(similarity_threshold=0.5)
        embedding = [1.0, 0.0, 0.0]
        cluster_id_best = uuid4()
        clusters = [
            {"id": uuid4(), "centroid": [0.7, 0.7, 0.0]},       # ~0.71 similarity
            {"id": cluster_id_best, "centroid": [0.95, 0.05, 0.0]},  # ~0.998 similarity
            {"id": uuid4(), "centroid": [0.5, 0.5, 0.5]},       # lower similarity
        ]
        result = service.find_matching_cluster(embedding, clusters)
        assert result is not None
        assert result["cluster_id"] == cluster_id_best

    def test_find_matching_cluster_skips_none_centroid(self):
        """Should skip clusters with None centroid."""
        service = ClusteringService(similarity_threshold=0.5)
        embedding = [1.0, 0.0]
        valid_cluster_id = uuid4()
        clusters = [
            {"id": uuid4(), "centroid": None},  # Should be skipped
            {"id": valid_cluster_id, "centroid": [0.9, 0.1]},
        ]
        result = service.find_matching_cluster(embedding, clusters)
        assert result is not None
        assert result["cluster_id"] == valid_cluster_id

    def test_find_matching_cluster_uses_default_threshold(self):
        """Should use default threshold from settings (0.75)."""
        service = ClusteringService()  # Uses default from settings
        embedding = [1.0, 0.0]

        # This cluster has similarity ~0.8, above default 0.75
        matching_cluster_id = uuid4()
        clusters = [
            {"id": matching_cluster_id, "centroid": [0.95, 0.31]},  # cos sim ~0.95
        ]
        result = service.find_matching_cluster(embedding, clusters)
        assert result is not None

        # This cluster would be below 0.75 threshold
        non_matching_clusters = [
            {"id": uuid4(), "centroid": [0.5, 0.87]},  # cos sim ~0.5
        ]
        result2 = service.find_matching_cluster(embedding, non_matching_clusters)
        assert result2 is None

    def test_find_matching_cluster_returns_correct_format(self):
        """Result should have cluster_id and similarity keys."""
        service = ClusteringService(similarity_threshold=0.5)
        embedding = [1.0, 0.0]
        cluster_id = uuid4()
        clusters = [{"id": cluster_id, "centroid": [0.9, 0.1]}]

        result = service.find_matching_cluster(embedding, clusters)

        assert "cluster_id" in result
        assert "similarity" in result
        assert isinstance(result["similarity"], float)
        assert 0.0 <= result["similarity"] <= 1.0


class TestClusteringServiceInit:
    """Tests for ClusteringService initialization."""

    def test_init_with_custom_threshold(self):
        """Should accept custom similarity threshold."""
        service = ClusteringService(similarity_threshold=0.9)
        assert service.similarity_threshold == 0.9

    def test_init_with_default_threshold(self):
        """Should use default threshold from settings."""
        service = ClusteringService()
        assert service.similarity_threshold == 0.75  # Default from config

    def test_init_with_zero_threshold(self):
        """Should accept zero threshold (match everything)."""
        service = ClusteringService(similarity_threshold=0.0)
        assert service.similarity_threshold == 0.0
