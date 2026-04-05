"""Single-Pass Clustering algorithm implementation."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class ClusteringService:
    """
    Single-Pass Clustering for news articles.

    Algorithm:
    1. For each new article with embedding
    2. Find best matching cluster (cosine similarity > threshold)
    3. If found: add to cluster, update centroid
    4. If not found: create new cluster with article as centroid

    Centroid update uses incremental mean:
    new_centroid = old_centroid + (new_vec - old_centroid) / n
    """

    def __init__(self, similarity_threshold: float = None):
        """
        Initialize clustering service.

        Args:
            similarity_threshold: Minimum cosine similarity for cluster match.
                                  Default from settings.SIMILARITY_THRESHOLD (0.75)
        """
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SIMILARITY_THRESHOLD
        )

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Cosine similarity measures the cosine of the angle between two vectors.
        It ranges from -1 (opposite direction) to 1 (same direction), with 0
        indicating orthogonality (no similarity).

        For normalized embeddings, this is equivalent to the dot product.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity in range [-1, 1], typically [0, 1] for embeddings
        """
        a = np.array(vec1)
        b = np.array(vec2)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        # Handle zero vectors to avoid division by zero
        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    @staticmethod
    def update_centroid(
        current_centroid: Optional[List[float]],
        new_vector: List[float],
        article_count: int
    ) -> List[float]:
        """
        Update cluster centroid with incremental mean.

        Uses Welford's online algorithm for numerical stability:
        new_mean = old_mean + (new_value - old_mean) / n

        This approach:
        - Avoids storing all vectors in memory
        - Provides O(1) space complexity
        - Is numerically stable for large n

        Args:
            current_centroid: Current centroid vector (None for first article)
            new_vector: New article's embedding
            article_count: Total articles after adding this one

        Returns:
            Updated centroid vector
        """
        # First article: the new vector becomes the centroid
        if current_centroid is None or article_count == 1:
            return list(new_vector)

        current = np.array(current_centroid)
        new_vec = np.array(new_vector)

        # Incremental mean update: new = old + (val - old) / n
        updated = current + (new_vec - current) / article_count

        return updated.tolist()

    def find_matching_cluster(
        self,
        embedding: List[float],
        active_clusters: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching cluster for an embedding.

        Iterates through all active clusters and finds the one with the
        highest cosine similarity to the given embedding. Returns the match
        only if similarity exceeds the threshold.

        Args:
            embedding: Article embedding vector
            active_clusters: List of dicts with 'id' and 'centroid' keys

        Returns:
            Dict with 'cluster_id' and 'similarity' if match found, None otherwise
        """
        if not active_clusters:
            return None

        best_match = None
        best_similarity = 0.0

        for cluster in active_clusters:
            # Skip clusters without a valid centroid
            if cluster.get("centroid") is None:
                continue

            similarity = self.cosine_similarity(embedding, cluster["centroid"])

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cluster

        # Return match only if above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            return {
                "cluster_id": best_match["id"],
                "similarity": best_similarity,
            }

        return None

    # CSAI (Cluster Stability Assessment Index) configuration
    CSAI_MILESTONES = [10, 25, 50, 100]
    CSAI_STABLE_THRESHOLD = 0.35

    def calculate_csai(self, centroid: List[float]) -> float:
        """
        Calculate CSAI using Matryoshka slice correlation.

        Measures semantic consistency across embedding dimensions.
        OpenAI text-embedding-3-small has hierarchical information:
        - First 256D: Core semantics
        - First 512D: More detail
        - Full 1536D: Maximum detail

        A stable cluster should have consistent semantics at all scales.

        Args:
            centroid: 1536D embedding vector

        Returns:
            CSAI score between 0 and 1. >= 0.35 indicates stable cluster.
        """
        if len(centroid) < 512:
            # Can't compute CSAI for small embeddings
            return 1.0

        # Extract Matryoshka slices
        slice_256 = np.array(centroid[:256])
        slice_512 = np.array(centroid[:512])
        full = np.array(centroid)

        # Normalize slices (with epsilon to avoid division by zero)
        norm_256 = np.linalg.norm(slice_256)
        norm_512 = np.linalg.norm(slice_512)
        norm_full = np.linalg.norm(full)

        # Handle zero vectors gracefully
        if norm_256 == 0 or norm_512 == 0 or norm_full == 0:
            return 0.0

        slice_256 = slice_256 / norm_256
        slice_512 = slice_512 / norm_512
        full = full / norm_full

        # Compare 256D slice to first 256D of 512D slice (normalized)
        sim_256_512 = self.cosine_similarity(
            slice_256.tolist(),
            (slice_512[:256] / (np.linalg.norm(slice_512[:256]) + 1e-10)).tolist()
        )

        # Compare 512D slice to first 512D of full embedding (normalized)
        sim_512_full = self.cosine_similarity(
            slice_512.tolist(),
            (full[:512] / (np.linalg.norm(full[:512]) + 1e-10)).tolist()
        )

        # CSAI = average correlation across slices
        return (sim_256_512 + sim_512_full) / 2

    def should_validate_csai(self, article_count: int) -> bool:
        """
        Check if CSAI should be validated at this article count.

        Args:
            article_count: Current number of articles in cluster

        Returns:
            True if this is a CSAI milestone
        """
        return article_count in self.CSAI_MILESTONES

    def get_csai_status(self, csai_score: float) -> str:
        """
        Determine CSAI status based on score.

        Args:
            csai_score: CSAI score from calculate_csai()

        Returns:
            'stable' if >= threshold, 'unstable' otherwise
        """
        return 'stable' if csai_score >= self.CSAI_STABLE_THRESHOLD else 'unstable'
