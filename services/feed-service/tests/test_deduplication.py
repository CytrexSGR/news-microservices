# services/feed-service/tests/test_deduplication.py
"""Tests for SimHash deduplication service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.deduplication import DeduplicationService, DeduplicationResult


class TestDeduplicationService:
    """Test suite for DeduplicationService."""

    @pytest.fixture
    def service(self):
        return DeduplicationService()

    def test_check_duplicate_no_existing_fingerprints(self, service):
        """Should allow article when no existing fingerprints."""
        result = service.check_duplicate(
            fingerprint=12345678,
            existing_fingerprints=[],
        )

        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is False
        assert result.matching_fingerprint is None

    def test_check_duplicate_exact_duplicate(self, service):
        """Should reject exact duplicate (Hamming = 0)."""
        fingerprint = 12345678
        result = service.check_duplicate(
            fingerprint=fingerprint,
            existing_fingerprints=[(uuid4(), fingerprint)],
        )

        assert result.is_allowed is False
        assert result.is_duplicate is True
        assert result.hamming_distance == 0

    def test_check_duplicate_within_threshold(self, service):
        """Should reject duplicate within threshold (Hamming <= 3)."""
        fingerprint = 0b1111111111111111111111111111111111111111111111111111111111111111
        # Flip 3 bits - still duplicate
        similar = 0b1111111111111111111111111111111111111111111111111111111111111000

        result = service.check_duplicate(
            fingerprint=fingerprint,
            existing_fingerprints=[(uuid4(), similar)],
        )

        assert result.is_allowed is False
        assert result.is_duplicate is True
        assert result.hamming_distance == 3

    def test_check_near_duplicate(self, service):
        """Should flag near-duplicate (Hamming 4-7) for review."""
        fingerprint = 0b1111111111111111111111111111111111111111111111111111111111111111
        # Flip 5 bits - near duplicate
        similar = 0b1111111111111111111111111111111111111111111111111111111111100000

        result = service.check_duplicate(
            fingerprint=fingerprint,
            existing_fingerprints=[(uuid4(), similar)],
        )

        assert result.is_allowed is True  # Still allowed but flagged
        assert result.is_duplicate is False
        assert result.is_near_duplicate is True
        assert result.hamming_distance == 5

    def test_check_different_content(self, service):
        """Should allow different content (Hamming > 7)."""
        fingerprint = 0b1111111111111111111111111111111111111111111111111111111111111111
        # Flip 10 bits - different content
        different = 0b1111111111111111111111111111111111111111111111111111110000000000

        result = service.check_duplicate(
            fingerprint=fingerprint,
            existing_fingerprints=[(uuid4(), different)],
        )

        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is False

    def test_check_multiple_candidates(self, service):
        """Should find closest match among multiple candidates."""
        fingerprint = 0b1111111111111111111111111111111111111111111111111111111111111111

        candidates = [
            (uuid4(), 0b1111111111111111111111111111111111111111111111111111110000000000),  # 10 bits
            (uuid4(), 0b1111111111111111111111111111111111111111111111111111111111100000),  # 5 bits
            (uuid4(), 0b1111111111111111111111111111111111111111111111111111111100000000),  # 8 bits
        ]

        result = service.check_duplicate(
            fingerprint=fingerprint,
            existing_fingerprints=candidates,
        )

        assert result.hamming_distance == 5  # Closest match
        assert result.is_near_duplicate is True
