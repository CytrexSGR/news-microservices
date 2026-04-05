# libs/news-intelligence-common/src/news_intelligence_common/simhasher.py
"""SimHash implementation for near-duplicate detection."""

import re
from typing import List, Set

from simhash import Simhash  # type: ignore[import-untyped]


class SimHasher:
    """
    SimHash implementation for near-duplicate detection.

    Hamming distance thresholds:
    - 0-3: Duplicate (same content)
    - 4-7: Near-duplicate (minor edits)
    - 8+: Different content

    Example:
        >>> hasher = SimHasher()
        >>> fp1 = SimHasher.compute_fingerprint("Breaking news article")
        >>> fp2 = SimHasher.compute_fingerprint("Breaking news article updated")
        >>> hasher.is_near_duplicate(fp1, fp2)
        True
    """

    DUPLICATE_THRESHOLD: int = 3
    NEAR_DUPLICATE_THRESHOLD: int = 7

    STOP_WORDS: Set[str] = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "has", "have", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "that", "this", "these", "those",
        "it", "its", "as", "if", "not", "no", "so", "up", "out", "about",
        "said", "says", "according", "also", "than", "just", "more", "been",
    }

    @classmethod
    def tokenize(cls, text: str, min_length: int = 3) -> List[str]:
        """
        Tokenize text with cleaning suitable for SimHash.

        Args:
            text: Input text to tokenize
            min_length: Minimum token length (default 3)

        Returns:
            List of cleaned tokens
        """
        if not text:
            return []

        # Remove punctuation and normalize whitespace
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = cleaned.split()

        # Filter stopwords and short tokens
        return [
            token
            for token in tokens
            if token not in cls.STOP_WORDS and len(token) >= min_length
        ]

    # PostgreSQL BIGINT max value (signed 64-bit)
    MAX_SIGNED_INT64: int = (1 << 63) - 1

    @classmethod
    def compute_fingerprint(cls, text: str) -> int:
        """
        Compute 64-bit SimHash fingerprint as signed integer.

        The simhash library returns unsigned 64-bit integers (0 to 2^64-1),
        but PostgreSQL BIGINT is signed (-2^63 to 2^63-1).
        This method converts the unsigned value to a signed representation.

        Args:
            text: Input text to fingerprint

        Returns:
            Signed 64-bit integer fingerprint (compatible with PostgreSQL BIGINT)
        """
        tokens = cls.tokenize(text)
        if not tokens:
            # Fallback for very short text
            unsigned_value = int(Simhash([text.lower()]).value)
        else:
            unsigned_value = int(Simhash(tokens).value)

        # Convert unsigned 64-bit to signed for PostgreSQL BIGINT compatibility
        if unsigned_value > cls.MAX_SIGNED_INT64:
            return unsigned_value - (1 << 64)
        return unsigned_value

    @staticmethod
    def hamming_distance(fp1: int, fp2: int) -> int:
        """
        Calculate Hamming distance between two fingerprints.

        Handles both signed and unsigned 64-bit integers correctly.

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            Number of differing bits
        """
        # XOR works correctly for signed integers in Python
        # bin() for negative numbers prefixes with '-', so we mask to 64 bits
        xor_result = (fp1 ^ fp2) & 0xFFFFFFFFFFFFFFFF
        return bin(xor_result).count("1")

    def is_duplicate(self, fp1: int, fp2: int) -> bool:
        """
        Check if two fingerprints are duplicates.

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            True if Hamming distance <= DUPLICATE_THRESHOLD
        """
        return self.hamming_distance(fp1, fp2) <= self.DUPLICATE_THRESHOLD

    def is_near_duplicate(self, fp1: int, fp2: int) -> bool:
        """
        Check if two fingerprints are near-duplicates.

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            True if DUPLICATE_THRESHOLD < Hamming distance <= NEAR_DUPLICATE_THRESHOLD
        """
        distance = self.hamming_distance(fp1, fp2)
        return self.DUPLICATE_THRESHOLD < distance <= self.NEAR_DUPLICATE_THRESHOLD

    def find_duplicates(self, fingerprint: int, existing: List[int]) -> List[int]:
        """
        Find all duplicates in existing fingerprints.

        Args:
            fingerprint: Fingerprint to check
            existing: List of existing fingerprints

        Returns:
            List of fingerprints that are duplicates
        """
        return [
            fp
            for fp in existing
            if self.hamming_distance(fingerprint, fp) <= self.DUPLICATE_THRESHOLD
        ]
