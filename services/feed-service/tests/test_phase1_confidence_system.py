"""
Phase 1 Unit Tests: Enhanced 4-Tier Confidence System

Tests Phase 1.3: Enhanced confidence indicators with 4-tier granularity.

Simplified approach: Test the _calculate_confidence_level() helper method
which contains the core logic for the 4-tier confidence system.

Usage:
    pytest tests/test_phase1_confidence_system.py -v
"""
import pytest
from app.services.feed_quality_v2 import FeedQualityScorerV2


class TestFourTierConfidenceSystem:
    """Test Phase 1.3: 4-tier confidence level calculation."""

    def test_insufficient_data_under_10_percent_coverage(self):
        """Test insufficient_data confidence with < 10% coverage."""
        service = FeedQualityScorerV2()

        # Test case: 2 out of 25 articles (8% coverage)
        result = service._calculate_confidence_level(
            coverage_fraction=0.08,
            articles_count=2
        )

        assert result == "insufficient_data", \
            "Should return insufficient_data with 8% coverage"

    def test_insufficient_data_under_5_articles(self):
        """Test insufficient_data confidence with < 5 articles regardless of coverage."""
        service = FeedQualityScorerV2()

        # Test case: 3 out of 5 articles (60% coverage, but < 5 articles)
        result = service._calculate_confidence_level(
            coverage_fraction=0.60,
            articles_count=3
        )

        assert result == "insufficient_data", \
            "Should return insufficient_data with < 5 articles despite 60% coverage"

    def test_low_confidence_10_to_50_percent_coverage(self):
        """Test low confidence with 10-50% coverage."""
        service = FeedQualityScorerV2()

        test_cases = [
            (0.10, 10, "low"),  # Exactly 10%
            (0.25, 25, "low"),  # 25%
            (0.32, 32, "low"),  # 32%
            (0.49, 49, "low"),  # Just below 50%
        ]

        for coverage, count, expected in test_cases:
            result = service._calculate_confidence_level(
                coverage_fraction=coverage,
                articles_count=count
            )
            assert result == expected, \
                f"Coverage={coverage*100}%, count={count} should be '{expected}'"

    def test_medium_confidence_50_to_80_percent_coverage(self):
        """Test medium confidence with 50-80% coverage."""
        service = FeedQualityScorerV2()

        test_cases = [
            (0.50, 50, "medium"),  # Exactly 50%
            (0.60, 60, "medium"),  # 60%
            (0.70, 70, "medium"),  # 70%
            (0.79, 79, "medium"),  # Just below 80%
        ]

        for coverage, count, expected in test_cases:
            result = service._calculate_confidence_level(
                coverage_fraction=coverage,
                articles_count=count
            )
            assert result == expected, \
                f"Coverage={coverage*100}%, count={count} should be '{expected}'"

    def test_high_confidence_over_80_percent_coverage(self):
        """Test high confidence with >= 80% coverage."""
        service = FeedQualityScorerV2()

        test_cases = [
            (0.80, 80, "high"),   # Exactly 80%
            (0.85, 85, "high"),   # 85%
            (0.92, 92, "high"),   # 92%
            (1.00, 100, "high"),  # Perfect coverage
        ]

        for coverage, count, expected in test_cases:
            result = service._calculate_confidence_level(
                coverage_fraction=coverage,
                articles_count=count
            )
            assert result == expected, \
                f"Coverage={coverage*100}%, count={count} should be '{expected}'"

    def test_edge_case_exactly_5_articles_50_percent_coverage(self):
        """Test edge case: exactly 5 articles with 50% coverage."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=0.50,
            articles_count=5
        )

        # 5 articles meets minimum, 50% coverage = medium
        assert result == "medium", \
            "5 articles with 50% coverage should be medium (not insufficient_data)"

    def test_edge_case_4_articles_high_coverage(self):
        """Test edge case: 4 articles with high coverage."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=0.90,
            articles_count=4
        )

        # < 5 articles always insufficient_data
        assert result == "insufficient_data", \
            "< 5 articles should always be insufficient_data"

    def test_edge_case_exactly_10_percent_coverage(self):
        """Test edge case: exactly 10% coverage."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=0.10,
            articles_count=10
        )

        # 10% is the threshold for low (not insufficient_data)
        assert result == "low", \
            "Exactly 10% coverage should be low (not insufficient_data)"

    def test_edge_case_exactly_50_percent_coverage(self):
        """Test edge case: exactly 50% coverage."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=0.50,
            articles_count=50
        )

        # 50% is the threshold for medium (not low)
        assert result == "medium", \
            "Exactly 50% coverage should be medium (not low)"

    def test_edge_case_exactly_80_percent_coverage(self):
        """Test edge case: exactly 80% coverage."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=0.80,
            articles_count=80
        )

        # 80% is the threshold for high (not medium)
        assert result == "high", \
            "Exactly 80% coverage should be high (not medium)"

    @pytest.mark.parametrize("coverage,count,expected", [
        # Comprehensive test cases for all boundaries
        (0.05, 5, "insufficient_data"),   # Just below 10%
        (0.09, 9, "insufficient_data"),   # Just below 10%
        (0.10, 10, "low"),                # Exactly 10%
        (0.11, 11, "low"),                # Just above 10%
        (0.49, 49, "low"),                # Just below 50%
        (0.50, 50, "medium"),             # Exactly 50%
        (0.51, 51, "medium"),             # Just above 50%
        (0.79, 79, "medium"),             # Just below 80%
        (0.80, 80, "high"),               # Exactly 80%
        (0.81, 81, "high"),               # Just above 80%
    ])
    def test_confidence_thresholds_comprehensive(self, coverage, count, expected):
        """Comprehensive test of all confidence level thresholds."""
        service = FeedQualityScorerV2()

        result = service._calculate_confidence_level(
            coverage_fraction=coverage,
            articles_count=count
        )

        assert result == expected, \
            f"Coverage={coverage*100:.0f}%, count={count} should be '{expected}', got '{result}'"


class TestBackwardCompatibility:
    """Test that new 4-tier system maintains backward compatibility."""

    def test_old_confidence_values_still_valid(self):
        """Test that the 3 old confidence values (low/medium/high) still exist in new system."""
        service = FeedQualityScorerV2()

        # Map new 4-tier to old 3-tier
        # insufficient_data → low (backward compatible)
        # low → low
        # medium → medium
        # high → high

        test_cases = [
            (0.05, 5, "insufficient_data"),  # Maps to "low" in old system
            (0.30, 30, "low"),               # Maps to "low" in old system
            (0.65, 65, "medium"),            # Maps to "medium" in old system
            (0.90, 90, "high"),              # Maps to "high" in old system
        ]

        for coverage, count, expected_new in test_cases:
            result = service._calculate_confidence_level(
                coverage_fraction=coverage,
                articles_count=count
            )

            # Verify new 4-tier system works
            assert result == expected_new

            # Verify old 3-tier mapping
            if result == "insufficient_data":
                old_confidence = "low"  # Backward compatible mapping
            else:
                old_confidence = result

            assert old_confidence in ["low", "medium", "high"], \
                f"Old confidence '{old_confidence}' should be one of: low, medium, high"
