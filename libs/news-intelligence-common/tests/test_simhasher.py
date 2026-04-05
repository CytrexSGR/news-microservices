# libs/news-intelligence-common/tests/test_simhasher.py
"""Tests for SimHasher class."""

import pytest
from news_intelligence_common.simhasher import SimHasher


class TestSimHasherTokenization:
    """Test tokenization behavior."""

    def test_tokenize_removes_punctuation(self) -> None:
        """Punctuation should be stripped from tokens."""
        tokens = SimHasher.tokenize("Hello, world! How are you?")
        assert "," not in "".join(tokens)
        assert "!" not in "".join(tokens)
        assert "?" not in "".join(tokens)

    def test_tokenize_lowercases(self) -> None:
        """All tokens should be lowercase."""
        tokens = SimHasher.tokenize("HELLO World MiXeD")
        assert all(t.islower() for t in tokens)

    def test_tokenize_filters_stopwords(self) -> None:
        """Common stopwords should be removed."""
        tokens = SimHasher.tokenize("the quick brown fox and the lazy dog")
        assert "the" not in tokens
        assert "and" not in tokens

    def test_tokenize_filters_short_tokens(self) -> None:
        """Tokens shorter than min_length should be removed."""
        tokens = SimHasher.tokenize("a ab abc abcd", min_length=3)
        assert "a" not in tokens
        assert "ab" not in tokens
        assert "abc" in tokens
        assert "abcd" in tokens

    def test_tokenize_empty_string(self) -> None:
        """Empty string should return empty list."""
        assert SimHasher.tokenize("") == []


class TestSimHasherFingerprint:
    """Test fingerprint computation."""

    def test_compute_fingerprint_returns_int(self) -> None:
        """Fingerprint should be an integer."""
        fp = SimHasher.compute_fingerprint("Test article content")
        assert isinstance(fp, int)

    def test_compute_fingerprint_64bit(self) -> None:
        """Fingerprint should be 64-bit (positive)."""
        fp = SimHasher.compute_fingerprint("Test article content")
        assert 0 <= fp < 2**64

    def test_compute_fingerprint_deterministic(self) -> None:
        """Same input should produce same fingerprint."""
        text = "Breaking news: Market reaches new high"
        fp1 = SimHasher.compute_fingerprint(text)
        fp2 = SimHasher.compute_fingerprint(text)
        assert fp1 == fp2

    def test_compute_fingerprint_different_for_different_text(self) -> None:
        """Different text should produce different fingerprints."""
        fp1 = SimHasher.compute_fingerprint("Article about technology")
        fp2 = SimHasher.compute_fingerprint("Article about sports")
        assert fp1 != fp2

    def test_compute_fingerprint_short_text(self) -> None:
        """Short text should still produce valid fingerprint."""
        fp = SimHasher.compute_fingerprint("Hi")
        assert isinstance(fp, int)


class TestSimHasherHammingDistance:
    """Test Hamming distance calculation."""

    def test_hamming_distance_identical(self) -> None:
        """Identical fingerprints should have distance 0."""
        fp = 0b1010101010101010
        assert SimHasher.hamming_distance(fp, fp) == 0

    def test_hamming_distance_one_bit(self) -> None:
        """One bit difference should return 1."""
        fp1 = 0b1010101010101010
        fp2 = 0b1010101010101011
        assert SimHasher.hamming_distance(fp1, fp2) == 1

    def test_hamming_distance_multiple_bits(self) -> None:
        """Multiple bit differences should be counted."""
        fp1 = 0b00000000
        fp2 = 0b11111111
        assert SimHasher.hamming_distance(fp1, fp2) == 8


class TestSimHasherDuplicateDetection:
    """Test duplicate and near-duplicate detection."""

    @pytest.fixture
    def hasher(self) -> SimHasher:
        """Create SimHasher instance."""
        return SimHasher()

    def test_is_duplicate_exact_match(self, hasher: SimHasher) -> None:
        """Identical fingerprints should be duplicates."""
        fp = SimHasher.compute_fingerprint("Same content")
        assert hasher.is_duplicate(fp, fp)

    def test_is_duplicate_within_threshold(self, hasher: SimHasher) -> None:
        """Fingerprints within threshold should be duplicates."""
        # Create two fingerprints with Hamming distance 3
        fp1 = 0b0000000000000000
        fp2 = 0b0000000000000111  # 3 bits different
        assert hasher.is_duplicate(fp1, fp2)

    def test_is_duplicate_beyond_threshold(self, hasher: SimHasher) -> None:
        """Fingerprints beyond threshold should not be duplicates."""
        fp1 = 0b0000000000000000
        fp2 = 0b0000000000001111  # 4 bits different
        assert not hasher.is_duplicate(fp1, fp2)

    def test_is_near_duplicate(self, hasher: SimHasher) -> None:
        """Near-duplicates should be detected."""
        fp1 = 0b0000000000000000
        fp2 = 0b0000000001111111  # 7 bits different
        assert hasher.is_near_duplicate(fp1, fp2)

    def test_is_near_duplicate_not_duplicate(self, hasher: SimHasher) -> None:
        """Exact duplicates should not be near-duplicates."""
        fp = SimHasher.compute_fingerprint("Same content")
        assert not hasher.is_near_duplicate(fp, fp)

    def test_find_duplicates_empty_list(self, hasher: SimHasher) -> None:
        """Empty list should return empty list."""
        fp = SimHasher.compute_fingerprint("Test")
        assert hasher.find_duplicates(fp, []) == []

    def test_find_duplicates_finds_matches(self, hasher: SimHasher) -> None:
        """Should find all duplicates in list."""
        fp = 0b0000000000000000
        existing = [
            0b0000000000000001,  # 1 bit diff - duplicate
            0b0000000000001111,  # 4 bits diff - not duplicate
            0b0000000000000011,  # 2 bits diff - duplicate
        ]
        duplicates = hasher.find_duplicates(fp, existing)
        assert len(duplicates) == 2
        assert 0b0000000000000001 in duplicates
        assert 0b0000000000000011 in duplicates


class TestSimHasherConstants:
    """Test class constants."""

    def test_duplicate_threshold(self) -> None:
        """DUPLICATE_THRESHOLD should be 3."""
        assert SimHasher.DUPLICATE_THRESHOLD == 3

    def test_near_duplicate_threshold(self) -> None:
        """NEAR_DUPLICATE_THRESHOLD should be 7."""
        assert SimHasher.NEAR_DUPLICATE_THRESHOLD == 7

    def test_stop_words_populated(self) -> None:
        """STOP_WORDS should contain common words."""
        assert "the" in SimHasher.STOP_WORDS
        assert "and" in SimHasher.STOP_WORDS
        assert "is" in SimHasher.STOP_WORDS
