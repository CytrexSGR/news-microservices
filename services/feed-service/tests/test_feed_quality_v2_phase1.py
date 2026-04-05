"""
Phase 1 Unit Tests: Feed Quality V2 Quick Wins

Tests the Phase 1 changes to FeedQualityV2Service:
1. Default score handling (None instead of 50.0)
2. Coverage-aware dimension scoring with penalties
3. Weight normalization for missing dimensions
4. Enhanced 4-tier confidence system

Usage:
    pytest tests/test_feed_quality_v2_phase1.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.feed_quality_v2 import FeedQualityScorerV2


class TestDefaultScoreHandling:
    """Test Phase 1.1: Default score refactoring."""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none_score(self):
        """Test that insufficient data (< 5 articles) returns score=None."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock database session with only 3 analyzed articles
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (80.0, 60.0, 70.0, None, None),  # Only 3 dimensions have data
            (75.0, 65.0, 75.0, None, None),
            (70.0, 55.0, 65.0, None, None),
        ]
        mock_session.execute.return_value = mock_result

        # Mock confidence calculation
        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "low",
            "confidence_level": "insufficient_data",
            "confidence_score": 15.0,
            "data_stats": {
                "articles_analyzed": 3,
                "total_articles": 20,
                "coverage_percentage": 15.0,
                "coverage_fraction": 0.15,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Assertions
        assert result["score"] is None, "Score should be None with insufficient data"
        assert result["weight"] == 0.10, "Weight should be minimal (0.10) with insufficient data"
        assert result["red_flags"]["insufficient_data"] is True
        assert result["confidence_level"] == "insufficient_data"
        assert result["articles_analyzed"] == 3

    @pytest.mark.asyncio
    async def test_sufficient_data_returns_numeric_score(self):
        """Test that sufficient data (>= 5 articles) returns valid score."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock database session with 10 analyzed articles
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [
            (80.0, 60.0, 70.0, 75.0, 65.0),
            (75.0, 65.0, 75.0, 70.0, 60.0),
            (70.0, 55.0, 65.0, 72.0, 68.0),
            (85.0, 70.0, 80.0, 78.0, 72.0),
            (78.0, 62.0, 68.0, 75.0, 70.0),
            (72.0, 58.0, 72.0, 68.0, 65.0),
            (88.0, 75.0, 85.0, 80.0, 75.0),
            (76.0, 64.0, 70.0, 72.0, 68.0),
            (82.0, 68.0, 78.0, 76.0, 72.0),
            (74.0, 60.0, 70.0, 70.0, 66.0),
        ]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        # Mock confidence calculation
        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "medium",
            "confidence_level": "medium",
            "confidence_score": 50.0,
            "data_stats": {
                "articles_analyzed": 10,
                "total_articles": 20,
                "coverage_percentage": 50.0,
                "coverage_fraction": 0.50,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Assertions
        assert result["score"] is not None, "Score should not be None with sufficient data"
        assert isinstance(result["score"], float), "Score should be numeric"
        assert 0 <= result["score"] <= 100, "Score should be in range 0-100"
        assert result["confidence_level"] in ["low", "medium", "high"]
        assert result["articles_analyzed"] == 10


class TestCoverageAwareDimensionScoring:
    """Test Phase 1.1: Coverage-aware dimension scoring with penalties."""

    @pytest.mark.asyncio
    async def test_low_coverage_dimension_marked_as_none(self):
        """Test that dimensions with < 10% coverage are marked as None."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 20 articles, but only 1 has credibility score (5% coverage)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [(80.0 if i == 0 else None, 70.0, 75.0, 72.0, 68.0) for i in range(20)]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "high",
            "confidence_level": "high",
            "confidence_score": 100.0,
            "data_stats": {
                "articles_analyzed": 20,
                "total_articles": 20,
                "coverage_percentage": 100.0,
                "coverage_fraction": 1.0,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Credibility dimension should be None due to < 10% coverage
        assert result["breakdown"]["credibility"] is None, \
            "Credibility should be None with < 10% coverage"

        # Other dimensions with 100% coverage should have scores
        assert result["breakdown"]["objectivity"] is not None
        assert result["breakdown"]["depth"] is not None

    @pytest.mark.asyncio
    async def test_medium_coverage_dimension_penalized(self):
        """Test that dimensions with 10-50% coverage get penalty."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 20 articles, 8 have credibility scores (40% coverage)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [
            (80.0 if i < 8 else None, 70.0, 75.0, 72.0, 68.0)
            for i in range(20)
        ]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "high",
            "confidence_level": "high",
            "confidence_score": 100.0,
            "data_stats": {
                "articles_analyzed": 20,
                "total_articles": 20,
                "coverage_percentage": 100.0,
                "coverage_fraction": 1.0,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Credibility should be penalized (weighted towards 50.0)
        # Formula: score * 0.7 + 50.0 * 0.3 = 80 * 0.7 + 50 * 0.3 = 56 + 15 = 71
        credibility_score = result["breakdown"]["credibility"]
        assert credibility_score is not None, "Should have score with 40% coverage"
        assert credibility_score < 80.0, "Should be penalized below raw average"
        assert credibility_score > 50.0, "Should be above neutral score"

    @pytest.mark.asyncio
    async def test_high_coverage_dimension_no_penalty(self):
        """Test that dimensions with >= 50% coverage get no penalty."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 20 articles, 15 have credibility scores (75% coverage)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [
            (80.0 if i < 15 else None, 70.0, 75.0, 72.0, 68.0)
            for i in range(20)
        ]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "high",
            "confidence_level": "high",
            "confidence_score": 100.0,
            "data_stats": {
                "articles_analyzed": 20,
                "total_articles": 20,
                "coverage_percentage": 100.0,
                "coverage_fraction": 1.0,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Credibility should NOT be penalized with 75% coverage
        assert result["breakdown"]["credibility"] == 80.0, \
            "Should be exact average with >= 50% coverage"


class TestWeightNormalization:
    """Test Phase 1.1: Weight normalization when dimensions are missing."""

    @pytest.mark.asyncio
    async def test_weight_normalization_with_missing_dimensions(self):
        """Test that weights are normalized when some dimensions are None."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: credibility and timeliness are None (< 10% coverage)
        # Only objectivity, depth, factuality have data
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [
            (None, 70.0, 75.0, 72.0, None),  # credibility, timeliness = None
            (None, 65.0, 72.0, 70.0, None),
            (None, 68.0, 78.0, 75.0, None),
            (None, 72.0, 70.0, 68.0, None),
            (None, 66.0, 74.0, 72.0, None),
        ]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "medium",
            "confidence_level": "medium",
            "confidence_score": 50.0,
            "data_stats": {
                "articles_analyzed": 5,
                "total_articles": 10,
                "coverage_percentage": 50.0,
                "coverage_fraction": 0.50,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Verify breakdown shows None for missing dimensions
        assert result["breakdown"]["credibility"] is None
        assert result["breakdown"]["timeliness"] is None
        assert result["breakdown"]["objectivity"] is not None
        assert result["breakdown"]["depth"] is not None
        assert result["breakdown"]["factuality"] is not None

        # Verify final score exists despite missing dimensions
        assert result["score"] is not None, \
            "Should still calculate score with subset of dimensions"

    @pytest.mark.asyncio
    async def test_all_dimensions_none_returns_none_score(self):
        """Test that if ALL dimensions are None, score is None."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: All dimensions have < 10% coverage
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        rows = [
            (None, None, None, None, None),
            (None, None, None, None, None),
            (None, None, None, None, None),
            (None, None, None, None, None),
            (None, None, None, None, None),
        ]
        mock_result.fetchall.return_value = rows
        mock_session.execute.return_value = mock_result

        service._calculate_confidence = AsyncMock(return_value={
            "confidence": "low",
            "confidence_level": "low",
            "confidence_score": 25.0,
            "data_stats": {
                "articles_analyzed": 5,
                "total_articles": 20,
                "coverage_percentage": 25.0,
                "coverage_fraction": 0.25,
                "date_range_days": 30
            }
        })

        result = await service.calculate_feed_quality(
            feed_id=feed_id,
            session=mock_session,
            days=30
        )

        # Should return None score when no valid dimensions
        assert result["score"] is None, \
            "Score should be None when all dimensions are None"
        assert result["confidence_level"] in ["insufficient_data", "low"]


class TestEnhancedConfidenceSystem:
    """Test Phase 1.3: 4-tier confidence system."""

    @pytest.mark.asyncio
    async def test_insufficient_data_confidence_under_10_percent_coverage(self):
        """Test insufficient_data confidence with < 10% coverage."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 2 analyzed out of 25 total articles (8% coverage)
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock total articles query
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 25

        # Mock analyzed articles query
        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 2

        # Mock execute to return different results for different queries
        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Assertions
        assert result["confidence_level"] == "insufficient_data", \
            "Should be insufficient_data with < 10% coverage"
        assert result["data_stats"]["coverage_percentage"] < 10.0
        assert result["data_stats"]["articles_analyzed"] < 5

    @pytest.mark.asyncio
    async def test_insufficient_data_confidence_under_5_articles(self):
        """Test insufficient_data confidence with < 5 articles."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 3 analyzed out of 5 total articles (60% coverage, but < 5 articles)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 5

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 3

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Should be insufficient_data despite 60% coverage (< 5 articles)
        assert result["confidence_level"] == "insufficient_data", \
            "Should be insufficient_data with < 5 articles"
        assert result["data_stats"]["articles_analyzed"] < 5

    @pytest.mark.asyncio
    async def test_low_confidence_10_to_50_percent_coverage(self):
        """Test low confidence with 10-50% coverage."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 8 analyzed out of 25 total articles (32% coverage)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 25

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 8

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Assertions
        assert result["confidence_level"] == "low", \
            "Should be low with 32% coverage"
        assert 10.0 <= result["data_stats"]["coverage_percentage"] < 50.0
        assert result["confidence"] == "low"  # Backward compatible

    @pytest.mark.asyncio
    async def test_medium_confidence_50_to_80_percent_coverage(self):
        """Test medium confidence with 50-80% coverage."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 35 analyzed out of 50 total articles (70% coverage)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 50

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 35

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Assertions
        assert result["confidence_level"] == "medium", \
            "Should be medium with 70% coverage"
        assert 50.0 <= result["data_stats"]["coverage_percentage"] < 80.0
        assert result["confidence"] == "medium"  # Backward compatible

    @pytest.mark.asyncio
    async def test_high_confidence_over_80_percent_coverage(self):
        """Test high confidence with > 80% coverage."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 92 analyzed out of 100 total articles (92% coverage)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 100

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 92

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Assertions
        assert result["confidence_level"] == "high", \
            "Should be high with 92% coverage"
        assert result["data_stats"]["coverage_percentage"] >= 80.0
        assert result["confidence"] == "high"  # Backward compatible

    @pytest.mark.asyncio
    async def test_confidence_score_equals_coverage_percentage(self):
        """Test that confidence_score matches coverage_percentage."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 60 analyzed out of 80 total articles (75% coverage)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 80

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 60

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # confidence_score should equal coverage_percentage
        assert result["confidence_score"] == result["data_stats"]["coverage_percentage"], \
            "confidence_score should match coverage_percentage"
        assert result["confidence_score"] == 75.0

    @pytest.mark.asyncio
    async def test_backward_compatibility_three_tier_system(self):
        """Test that old 3-tier confidence field still works."""
        service = FeedQualityScorerV2()
        feed_id = uuid4()

        # Mock: 45 analyzed out of 50 total articles (90% coverage, high)
        mock_session = AsyncMock(spec=AsyncSession)

        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 50

        mock_analyzed_result = MagicMock()
        mock_analyzed_result.scalar.return_value = 45

        mock_session.execute = AsyncMock(side_effect=[
            mock_total_result,
            mock_analyzed_result
        ])

        result = await service._calculate_confidence(
            session=mock_session,
            feed_id=feed_id,
            days=30
        )

        # Both confidence and confidence_level should exist
        assert "confidence" in result, "Old confidence field should exist"
        assert "confidence_level" in result, "New confidence_level field should exist"
        assert result["confidence"] == "high"  # Old 3-tier system
        assert result["confidence_level"] == "high"  # New 4-tier system

        # For this case (90% coverage, >= 50 articles), both should be "high"
        assert result["confidence"] == result["confidence_level"]
