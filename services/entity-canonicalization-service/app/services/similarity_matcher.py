"""Similarity matching for entity canonicalization."""
import logging
import asyncio
from typing import List, Optional, Tuple
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class SimilarityMatcher:
    """
    Similarity matching using fuzzy string matching and semantic embeddings.

    Uses:
    1. RapidFuzz for fast fuzzy string matching
    2. SentenceTransformers for semantic similarity
    """

    def __init__(self):
        self.fuzzy_threshold = settings.FUZZY_THRESHOLD
        self.semantic_threshold = settings.SEMANTIC_THRESHOLD

        # Load sentence transformer model
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")

    def fuzzy_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Find best fuzzy match from candidates.

        Args:
            query: Entity name to match
            candidates: List of candidate entity names
            threshold: Minimum similarity threshold (0-100)

        Returns:
            (best_match, score) if found, None otherwise
        """
        if not candidates:
            return None

        threshold = threshold or (self.fuzzy_threshold * 100)
        query_lower = query.lower()

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            # Use ratio for general similarity
            score = fuzz.ratio(query_lower, candidate.lower())

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold:
            logger.debug(
                f"Fuzzy match: '{query}' → '{best_match}' (score={best_score:.1f})"
            )
            return best_match, best_score / 100.0

        return None

    async def semantic_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Find best semantic match using sentence embeddings (async, non-blocking).

        Args:
            query: Entity name to match
            candidates: List of candidate entity names
            threshold: Minimum cosine similarity threshold (0-1)

        Returns:
            (best_match, score) if found, None otherwise
        """
        if not candidates:
            return None

        threshold = threshold or self.semantic_threshold

        try:
            # 🔧 Run model inference in thread pool (prevents event loop blocking)
            # The model.encode() calls use NumPy/PyTorch which are CPU-bound and synchronous
            query_embedding = await asyncio.to_thread(self.model.encode, [query])
            candidate_embeddings = await asyncio.to_thread(self.model.encode, candidates)

            # Calculate cosine similarities (fast, can run inline)
            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]

            # Find best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]

            if best_score >= threshold:
                best_match = candidates[best_idx]
                logger.debug(
                    f"Semantic match: '{query}' → '{best_match}' "
                    f"(similarity={best_score:.3f})"
                )
                return best_match, float(best_score)

            return None

        except Exception as e:
            logger.error(f"Error in semantic matching: {e}")
            return None

    async def find_best_match(
        self,
        query: str,
        candidates: List[str],
        prefer_fuzzy: bool = True
    ) -> Optional[Tuple[str, float, str]]:
        """
        Find best match using both fuzzy and semantic matching (async, non-blocking).

        Args:
            query: Entity name to match
            candidates: List of candidate entity names
            prefer_fuzzy: If True, prefer fuzzy matches over semantic

        Returns:
            (best_match, score, method) if found, None otherwise
            method: "fuzzy" or "semantic"
        """
        if not candidates:
            return None

        # Try fuzzy matching first (fast, synchronous)
        fuzzy_result = self.fuzzy_match(query, candidates)

        # Try semantic matching (slow, async in thread pool)
        semantic_result = await self.semantic_match(query, candidates)

        # Decide which to use
        if fuzzy_result and semantic_result:
            # Both found - compare scores
            fuzzy_match, fuzzy_score = fuzzy_result
            semantic_match, semantic_score = semantic_result

            if prefer_fuzzy:
                # Prefer fuzzy if score is close
                if fuzzy_score >= semantic_score * 0.95:
                    return fuzzy_match, fuzzy_score, "fuzzy"
                else:
                    return semantic_match, semantic_score, "semantic"
            else:
                # Prefer semantic if score is close
                if semantic_score >= fuzzy_score * 0.95:
                    return semantic_match, semantic_score, "semantic"
                else:
                    return fuzzy_match, fuzzy_score, "fuzzy"

        elif fuzzy_result:
            match, score = fuzzy_result
            return match, score, "fuzzy"

        elif semantic_result:
            match, score = semantic_result
            return match, score, "semantic"

        return None

    async def batch_match(
        self,
        queries: List[str],
        candidates: List[str]
    ) -> List[Optional[Tuple[str, float, str]]]:
        """
        Batch matching for multiple queries (async, non-blocking).

        More efficient than individual calls when using semantic matching.

        Args:
            queries: List of entity names to match
            candidates: List of candidate entity names

        Returns:
            List of (best_match, score, method) or None for each query
        """
        results = []

        for query in queries:
            result = await self.find_best_match(query, candidates)
            results.append(result)

        return results
