"""
Fuzzy String Matching for Entity Canonicalization

Lightweight fuzzy matching using RapidFuzz (no ML dependencies).
Replaces semantic matching from SentenceTransformers (removed in OpenAI migration).

Reference: /home/cytrex/userdocs/system-ontology/ENTITY_CANONICALIZATION_OPENAI_MIGRATION.md (Phase 3.2)
"""

import logging
from typing import List, Optional, Tuple

from rapidfuzz import fuzz

from app.config import settings

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """
    Fuzzy string matching using RapidFuzz (no machine learning).

    Features:
    - RapidFuzz ratio scoring (Levenshtein distance)
    - Configurable threshold (default: 95%)
    - Lightweight (no model loading, <1MB memory)

    Usage:
        matcher = FuzzyMatcher()
        result = matcher.fuzzy_match("Tесла", ["Tesla", "SpaceX"])
        # result = ("Tesla", 0.95)
    """

    def __init__(self):
        """Initialize fuzzy matcher with threshold from config."""
        self.fuzzy_threshold = settings.FUZZY_THRESHOLD
        logger.info(
            f"FuzzyMatcher initialized (threshold={self.fuzzy_threshold:.2f})"
        )

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
            threshold: Minimum similarity threshold (0.0-1.0), defaults to config

        Returns:
            (best_match, score) if found, None otherwise

        Example:
            result = matcher.fuzzy_match("Tесла", ["Tesla", "SpaceX", "Apple"])
            # result = ("Tesla", 0.95) - Cyrillic 'е' vs Latin 'e'
        """
        if not candidates:
            return None

        threshold = threshold if threshold is not None else self.fuzzy_threshold
        threshold_percent = threshold * 100  # RapidFuzz uses 0-100 scale

        query_lower = query.lower()
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            # Use ratio for general similarity (Levenshtein distance)
            score = fuzz.ratio(query_lower, candidate.lower())

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold_percent:
            normalized_score = best_score / 100.0
            logger.debug(
                f"Fuzzy match: '{query}' → '{best_match}' (score={normalized_score:.3f})"
            )
            return best_match, normalized_score

        return None

    def fuzzy_match_partial(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Find best partial fuzzy match (substring matching).

        Useful for matching entity names that appear within longer strings.

        Args:
            query: Entity name to match
            candidates: List of candidate entity names
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            (best_match, score) if found, None otherwise

        Example:
            result = matcher.fuzzy_match_partial("Tesla", ["Tesla Inc.", "SpaceX Corp"])
            # result = ("Tesla Inc.", 0.98)
        """
        if not candidates:
            return None

        threshold = threshold if threshold is not None else self.fuzzy_threshold
        threshold_percent = threshold * 100

        query_lower = query.lower()
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            # Use partial_ratio for substring matching
            score = fuzz.partial_ratio(query_lower, candidate.lower())

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold_percent:
            normalized_score = best_score / 100.0
            logger.debug(
                f"Partial fuzzy match: '{query}' → '{best_match}' (score={normalized_score:.3f})"
            )
            return best_match, normalized_score

        return None

    def get_top_matches(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        Get top-k fuzzy matches sorted by score.

        Args:
            query: Entity name to match
            candidates: List of candidate entity names
            top_k: Number of top matches to return
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of (candidate, score) tuples, sorted by score descending

        Example:
            matches = matcher.get_top_matches("Tesla", candidates, top_k=5)
            # matches = [("Tesla Inc.", 0.98), ("Tesla Motors", 0.95), ...]
        """
        if not candidates:
            return []

        threshold = threshold if threshold is not None else self.fuzzy_threshold
        threshold_percent = threshold * 100

        query_lower = query.lower()
        scores = []

        for candidate in candidates:
            score = fuzz.ratio(query_lower, candidate.lower())
            if score >= threshold_percent:
                scores.append((candidate, score / 100.0))

        # Sort by score descending, take top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def match_by_type(
        self,
        query: str,
        candidates: List[str],
        alias_type: str = "name",
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Type-aware fuzzy matching with different strategies per alias type.

        Matching strategies:
        - ticker: Exact match only (case-sensitive) - returns 1.0 or None
        - abbreviation: Case-insensitive exact match - returns 1.0 or None
        - nickname: Lenient fuzzy (partial_ratio) with lower threshold
        - name: Standard fuzzy matching (ratio)

        Args:
            query: Entity name/alias to match
            candidates: List of candidate strings
            alias_type: Type of alias (ticker, abbreviation, nickname, name)
            threshold: Override threshold (default varies by type)

        Returns:
            (best_match, score) if found, None otherwise
        """
        if not candidates:
            return None

        # Type-specific matching strategies
        if alias_type == "ticker":
            # Tickers: exact match only (case-sensitive)
            query_stripped = query.strip()
            for candidate in candidates:
                if candidate.strip() == query_stripped:
                    return candidate, 1.0
            return None

        elif alias_type == "abbreviation":
            # Abbreviations: case-insensitive exact match
            query_lower = query.lower().strip()
            for candidate in candidates:
                if candidate.lower().strip() == query_lower:
                    return candidate, 1.0
            return None

        elif alias_type == "nickname":
            # Nicknames: lenient partial matching
            default_threshold = 0.70  # Lower threshold for nicknames
            effective_threshold = threshold if threshold is not None else default_threshold

            return self.fuzzy_match_partial(
                query,
                candidates,
                threshold=effective_threshold
            )

        else:
            # Default (name): standard fuzzy matching
            effective_threshold = threshold if threshold is not None else self.fuzzy_threshold

            return self.fuzzy_match(
                query,
                candidates,
                threshold=effective_threshold
            )


# Singleton instance
_fuzzy_matcher: Optional[FuzzyMatcher] = None


def get_fuzzy_matcher() -> FuzzyMatcher:
    """
    Get or create singleton FuzzyMatcher instance.

    Returns:
        FuzzyMatcher singleton
    """
    global _fuzzy_matcher

    if _fuzzy_matcher is None:
        _fuzzy_matcher = FuzzyMatcher()

    return _fuzzy_matcher
