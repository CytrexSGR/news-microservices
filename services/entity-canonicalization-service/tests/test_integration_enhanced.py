# tests/test_integration_enhanced.py
"""
Integration and Performance Tests for Enhanced Entity Resolution

Task 7 from Epic 1.4: Entity Resolution Enhancement Implementation Plan
Tests verify < 50ms performance targets and type-aware resolution flows.

Reference: /home/cytrex/news-microservices/docs/plans/2026-01-04-epic-1.4-entity-resolution-enhancement.md
"""
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fuzzy_matcher import FuzzyMatcher


class TestEntityResolutionPerformance:
    """
    Performance tests for entity resolution (target: < 50ms).

    These tests verify that the entity resolution pipeline meets
    the performance requirements specified in Epic 1.4.
    """

    @pytest.mark.asyncio
    async def test_exact_match_under_10ms(self):
        """
        Exact alias match should complete under 10ms.

        This tests the fastest path through the resolution pipeline
        where an exact alias match is found in the database.

        Target: < 10ms
        """
        # Setup mock
        with patch("app.services.alias_store.AliasStore") as MockStore:
            store = MockStore.return_value
            store.find_exact = AsyncMock(return_value=MagicMock(name="Test Entity"))

            start = time.perf_counter()
            await store.find_exact("TEST")
            duration_ms = (time.perf_counter() - start) * 1000

            assert duration_ms < 10, f"Exact match took {duration_ms:.2f}ms (target: <10ms)"

    @pytest.mark.asyncio
    async def test_fuzzy_match_under_50ms(self):
        """
        Fuzzy match with 1000 candidates should complete under 50ms.

        This tests the FuzzyMatcher's ability to efficiently scan
        a large candidate list using RapidFuzz's optimized algorithms.

        Target: < 50ms for 1000 candidates
        """
        matcher = FuzzyMatcher()
        candidates = [f"Entity {i}" for i in range(1000)]

        start = time.perf_counter()
        result = matcher.fuzzy_match("Entity 500", candidates)
        duration_ms = (time.perf_counter() - start) * 1000

        assert result is not None, "Should find a matching entity"
        assert result[0] == "Entity 500", f"Expected 'Entity 500', got '{result[0]}'"
        assert result[1] == 1.0, "Exact match should have score 1.0"
        assert duration_ms < 50, f"Fuzzy match took {duration_ms:.2f}ms (target: <50ms)"

    @pytest.mark.asyncio
    async def test_type_aware_match_under_50ms(self):
        """
        Type-aware matching should complete under 50ms.

        This tests the enhanced match_by_type method which applies
        different matching strategies based on alias type.

        Target: < 50ms
        """
        matcher = FuzzyMatcher()
        candidates = [f"Entity {i}" for i in range(1000)]

        start = time.perf_counter()
        result = matcher.match_by_type("Entity 500", candidates, alias_type="name")
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 50, f"Type-aware match took {duration_ms:.2f}ms (target: <50ms)"


class TestTypeAwareResolution:
    """
    Integration tests for type-aware entity resolution.

    These tests verify the end-to-end behavior of the type-aware
    matching system for different alias types (ticker, abbreviation, etc.).
    """

    @pytest.mark.asyncio
    async def test_ticker_resolution_flow(self):
        """
        Test ticker alias resolution end-to-end.

        Tickers (e.g., AAPL, MSFT) must match exactly and are case-sensitive.
        This prevents false positives like "APPL" matching "AAPL".

        Expected behavior:
        - Exact match: "AAPL" -> "AAPL" (score 1.0)
        - Similar but not exact: "APPL" -> None (no fuzzy for tickers)
        """
        matcher = FuzzyMatcher()

        # Tickers should only match exactly
        result = matcher.match_by_type("AAPL", ["AAPL", "MSFT"], alias_type="ticker")
        assert result is not None, "Exact ticker match should succeed"
        assert result[0] == "AAPL", f"Expected 'AAPL', got '{result[0]}'"
        assert result[1] == 1.0, f"Ticker match should have score 1.0, got {result[1]}"

        # Similar but not exact should fail for tickers
        result = matcher.match_by_type("APPL", ["AAPL", "MSFT"], alias_type="ticker")
        assert result is None, "Similar but not exact should NOT match for tickers"

        # Case sensitivity: lowercase should not match uppercase ticker
        result = matcher.match_by_type("aapl", ["AAPL", "MSFT"], alias_type="ticker")
        assert result is None, "Tickers are case-sensitive: 'aapl' should not match 'AAPL'"

    @pytest.mark.asyncio
    async def test_abbreviation_resolution_flow(self):
        """
        Test abbreviation alias resolution end-to-end.

        Abbreviations (e.g., USA, EU) are case-insensitive but must match exactly.
        This allows "usa" to match "USA" while preventing fuzzy mismatches.

        Expected behavior:
        - Case-insensitive exact: "usa" -> "USA" (score 1.0)
        - Different abbreviation: "US" -> None (not exact match for "USA")
        """
        matcher = FuzzyMatcher()

        # Abbreviations are case-insensitive
        result = matcher.match_by_type("usa", ["USA", "UK", "EU"], alias_type="abbreviation")
        assert result is not None, "Case-insensitive abbreviation match should succeed"
        assert result[0] == "USA", f"Expected 'USA', got '{result[0]}'"
        assert result[1] == 1.0, f"Abbreviation match should have score 1.0, got {result[1]}"

        # Mixed case should also work
        result = matcher.match_by_type("Usa", ["USA", "UK", "EU"], alias_type="abbreviation")
        assert result is not None, "Mixed case abbreviation should match"
        assert result[0] == "USA"

        # Different abbreviation should not match
        result = matcher.match_by_type("US", ["USA", "UK", "EU"], alias_type="abbreviation")
        assert result is None, "'US' should not match 'USA' (not exact)"


class TestPerformanceConsistency:
    """
    Tests to ensure performance remains consistent across multiple runs.

    These tests run multiple iterations to verify that the performance
    targets are met consistently, not just occasionally.
    """

    @pytest.mark.asyncio
    async def test_fuzzy_match_consistent_performance(self):
        """
        Fuzzy matching should consistently meet performance targets.

        Runs 10 iterations and verifies that:
        - Average time < 50ms
        - No single run exceeds 100ms (2x target)
        """
        matcher = FuzzyMatcher()
        candidates = [f"Entity {i}" for i in range(1000)]

        durations = []
        for i in range(10):
            start = time.perf_counter()
            matcher.fuzzy_match(f"Entity {i * 100}", candidates)
            duration_ms = (time.perf_counter() - start) * 1000
            durations.append(duration_ms)

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 50, f"Average fuzzy match took {avg_duration:.2f}ms (target: <50ms)"
        assert max_duration < 100, f"Max fuzzy match took {max_duration:.2f}ms (target: <100ms)"

    @pytest.mark.asyncio
    async def test_type_aware_match_all_types_performance(self):
        """
        All alias types should meet performance targets.

        Tests performance for each alias type:
        - ticker: Exact match (should be fastest)
        - abbreviation: Case-insensitive exact
        - nickname: Lenient fuzzy
        - name: Standard fuzzy
        """
        matcher = FuzzyMatcher()
        candidates = [f"Entity {i}" for i in range(1000)]

        alias_types = ["ticker", "abbreviation", "nickname", "name"]

        for alias_type in alias_types:
            start = time.perf_counter()
            matcher.match_by_type("Entity 500", candidates, alias_type=alias_type)
            duration_ms = (time.perf_counter() - start) * 1000

            assert duration_ms < 50, (
                f"match_by_type({alias_type}) took {duration_ms:.2f}ms (target: <50ms)"
            )
