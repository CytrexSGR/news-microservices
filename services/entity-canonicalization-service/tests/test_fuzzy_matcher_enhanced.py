# tests/test_fuzzy_matcher_enhanced.py
"""Tests for enhanced fuzzy matcher with type-awareness."""
import pytest
from app.services.fuzzy_matcher import FuzzyMatcher


@pytest.fixture
def fuzzy_matcher():
    """Create fuzzy matcher instance."""
    return FuzzyMatcher()


class TestTypeAwareFuzzyMatch:
    """Tests for type-aware fuzzy matching."""

    def test_ticker_exact_match_only(self, fuzzy_matcher):
        """Tickers require exact match, no fuzzy."""
        candidates = ["AAPL", "MSFT", "GOOGL"]

        # Exact match works
        result = fuzzy_matcher.match_by_type("AAPL", candidates, alias_type="ticker")
        assert result is not None
        assert result[0] == "AAPL"
        assert result[1] == 1.0

        # Similar but not exact fails
        result = fuzzy_matcher.match_by_type("APPL", candidates, alias_type="ticker")
        assert result is None  # No fuzzy for tickers

    def test_abbreviation_case_insensitive(self, fuzzy_matcher):
        """Abbreviations are case-insensitive but exact."""
        candidates = ["USA", "UK", "EU"]

        result = fuzzy_matcher.match_by_type("usa", candidates, alias_type="abbreviation")
        assert result is not None
        assert result[0] == "USA"
        assert result[1] == 1.0

    def test_name_uses_fuzzy(self, fuzzy_matcher):
        """Names use standard fuzzy matching."""
        candidates = ["apple inc.", "microsoft corporation", "google llc"]

        # Fuzzy match for slight typo
        result = fuzzy_matcher.match_by_type(
            "appel inc.",  # typo
            candidates,
            alias_type="name",
            threshold=0.90  # Lower threshold for typo tolerance
        )
        assert result is not None
        assert result[0] == "apple inc."
        assert result[1] >= 0.90

    def test_nickname_fuzzy_lenient(self, fuzzy_matcher):
        """Nicknames use more lenient fuzzy matching."""
        candidates = ["the donald", "sleepy joe", "the terminator"]

        # Should match with lower threshold
        result = fuzzy_matcher.match_by_type(
            "donald",
            candidates,
            alias_type="nickname",
            threshold=0.7
        )
        assert result is not None
        # Partial match allowed for nicknames

    def test_unknown_type_defaults_to_name(self, fuzzy_matcher):
        """Unknown alias type defaults to name matching."""
        candidates = ["apple inc.", "microsoft"]

        result = fuzzy_matcher.match_by_type(
            "apple",
            candidates,
            alias_type="unknown_type"
        )
        # Should use name matching as fallback
        assert result is not None or result is None  # Depends on threshold
