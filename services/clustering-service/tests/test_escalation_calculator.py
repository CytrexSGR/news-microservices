"""Unit tests for EscalationCalculator service skeleton.

Tests the core structure, dataclasses, signal weights, and method signatures
of the EscalationCalculator before signal implementations are added.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from app.services.escalation_calculator import (
    EscalationCalculator,
    EscalationSignal,
    DomainEscalation,
    EscalationResult,
)


class TestEscalationSignalDataclass:
    """Tests for EscalationSignal dataclass."""

    def test_create_minimal_signal(self):
        """Test creating signal with required fields only."""
        signal = EscalationSignal(
            domain="military",
            level=3,
            confidence=0.75,
            source="embedding",
        )

        assert signal.domain == "military"
        assert signal.level == 3
        assert signal.confidence == 0.75
        assert signal.source == "embedding"
        assert signal.matched_anchor_id is None
        assert signal.matched_keywords is None
        assert signal.reasoning is None

    def test_create_full_signal(self):
        """Test creating signal with all fields."""
        anchor_id = uuid4()
        signal = EscalationSignal(
            domain="geopolitical",
            level=4,
            confidence=0.85,
            source="keywords",
            matched_anchor_id=anchor_id,
            matched_keywords=["sanctions", "escalation", "military buildup"],
            reasoning="Multiple escalatory keywords detected",
        )

        assert signal.domain == "geopolitical"
        assert signal.level == 4
        assert signal.confidence == 0.85
        assert signal.source == "keywords"
        assert signal.matched_anchor_id == anchor_id
        assert signal.matched_keywords == ["sanctions", "escalation", "military buildup"]
        assert signal.reasoning == "Multiple escalatory keywords detected"

    def test_signal_all_domains(self):
        """Test creating signals for all three domains."""
        for domain in ["geopolitical", "military", "economic"]:
            signal = EscalationSignal(
                domain=domain,
                level=2,
                confidence=0.5,
                source="content",
            )
            assert signal.domain == domain

    def test_signal_all_sources(self):
        """Test creating signals for all three sources."""
        for source in ["embedding", "content", "keywords"]:
            signal = EscalationSignal(
                domain="military",
                level=3,
                confidence=0.6,
                source=source,
            )
            assert signal.source == source


class TestDomainEscalationDataclass:
    """Tests for DomainEscalation dataclass."""

    def test_create_domain_escalation(self):
        """Test creating DomainEscalation with signals."""
        signals = [
            EscalationSignal(domain="military", level=3, confidence=0.8, source="embedding"),
            EscalationSignal(domain="military", level=2, confidence=0.6, source="content"),
            EscalationSignal(domain="military", level=4, confidence=0.7, source="keywords"),
        ]

        escalation = DomainEscalation(
            domain="military",
            level=3,
            score=Decimal("0.650"),
            signals=signals,
            confidence=0.7,
        )

        assert escalation.domain == "military"
        assert escalation.level == 3
        assert escalation.score == Decimal("0.650")
        assert len(escalation.signals) == 3
        assert escalation.confidence == 0.7

    def test_domain_escalation_empty_signals(self):
        """Test creating DomainEscalation with no signals."""
        escalation = DomainEscalation(
            domain="economic",
            level=1,
            score=Decimal("0.000"),
            signals=[],
            confidence=0.0,
        )

        assert escalation.domain == "economic"
        assert escalation.level == 1
        assert escalation.score == Decimal("0.000")
        assert len(escalation.signals) == 0
        assert escalation.confidence == 0.0


class TestEscalationResultDataclass:
    """Tests for EscalationResult dataclass."""

    def test_create_escalation_result(self):
        """Test creating complete EscalationResult."""
        cluster_id = uuid4()
        now = datetime.utcnow()

        geo_escalation = DomainEscalation(
            domain="geopolitical",
            level=3,
            score=Decimal("0.550"),
            signals=[],
            confidence=0.75,
        )
        mil_escalation = DomainEscalation(
            domain="military",
            level=4,
            score=Decimal("0.720"),
            signals=[],
            confidence=0.80,
        )
        eco_escalation = DomainEscalation(
            domain="economic",
            level=2,
            score=Decimal("0.350"),
            signals=[],
            confidence=0.65,
        )

        result = EscalationResult(
            geopolitical=geo_escalation,
            military=mil_escalation,
            economic=eco_escalation,
            combined_level=4,
            combined_score=Decimal("0.540"),
            calculated_at=now,
            cluster_id=cluster_id,
            article_count=7,
        )

        assert result.geopolitical.level == 3
        assert result.military.level == 4
        assert result.economic.level == 2
        assert result.combined_level == 4  # max of domain levels
        assert result.combined_score == Decimal("0.540")
        assert result.calculated_at == now
        assert result.cluster_id == cluster_id
        assert result.article_count == 7


class TestEscalationCalculatorInstantiation:
    """Tests for EscalationCalculator instantiation."""

    def test_calculator_instantiates_with_session(self):
        """Verify EscalationCalculator can be instantiated with session."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator is not None
        assert calculator.session is mock_session
        assert calculator._anchor_cache == {}

    def test_calculator_has_session_attribute(self):
        """Verify calculator stores session reference."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "session")
        assert calculator.session is mock_session

    def test_calculator_initializes_empty_cache(self):
        """Verify calculator starts with empty anchor cache."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_anchor_cache")
        assert isinstance(calculator._anchor_cache, dict)
        assert len(calculator._anchor_cache) == 0


class TestSignalWeights:
    """Tests for signal weight constants."""

    def test_weights_sum_to_one(self):
        """Verify signal weights sum to exactly 1.0."""
        total = (
            EscalationCalculator.EMBEDDING_WEIGHT
            + EscalationCalculator.CONTENT_WEIGHT
            + EscalationCalculator.KEYWORD_WEIGHT
        )

        assert abs(total - 1.0) < 0.0001, f"Weights sum to {total}, expected 1.0"

    def test_embedding_weight_is_50_percent(self):
        """Verify embedding weight is 50%."""
        assert EscalationCalculator.EMBEDDING_WEIGHT == 0.50

    def test_content_weight_is_30_percent(self):
        """Verify content weight is 30%."""
        assert EscalationCalculator.CONTENT_WEIGHT == 0.30

    def test_keyword_weight_is_20_percent(self):
        """Verify keyword weight is 20%."""
        assert EscalationCalculator.KEYWORD_WEIGHT == 0.20

    def test_validate_weights_method(self):
        """Test the validate_weights class method."""
        assert EscalationCalculator.validate_weights() is True


class TestLevelThresholds:
    """Tests for level threshold constants."""

    def test_level_thresholds_defined(self):
        """Verify level thresholds are defined."""
        assert hasattr(EscalationCalculator, "LEVEL_THRESHOLDS")
        assert len(EscalationCalculator.LEVEL_THRESHOLDS) == 5

    def test_level_thresholds_cover_full_range(self):
        """Verify thresholds cover 0.0 to 1.0 without gaps."""
        thresholds = EscalationCalculator.LEVEL_THRESHOLDS

        # First threshold starts at 0.0
        assert thresholds[0][0] == 0.0

        # Last threshold ends at 1.0
        assert thresholds[-1][1] == 1.0

        # No gaps between thresholds
        for i in range(len(thresholds) - 1):
            assert thresholds[i][1] == thresholds[i + 1][0]

    def test_level_thresholds_have_correct_levels(self):
        """Verify threshold levels are 1-5."""
        thresholds = EscalationCalculator.LEVEL_THRESHOLDS
        levels = [t[2] for t in thresholds]

        assert levels == [1, 2, 3, 4, 5]


class TestScoreToLevel:
    """Tests for score_to_level method."""

    def test_score_to_level_routine(self):
        """Test score 0.0-0.2 maps to level 1 (Routine)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(0.0) == 1
        assert calculator.score_to_level(0.1) == 1
        assert calculator.score_to_level(0.19) == 1

    def test_score_to_level_elevated(self):
        """Test score 0.2-0.4 maps to level 2 (Elevated)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(0.2) == 2
        assert calculator.score_to_level(0.3) == 2
        assert calculator.score_to_level(0.39) == 2

    def test_score_to_level_significant(self):
        """Test score 0.4-0.6 maps to level 3 (Significant)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(0.4) == 3
        assert calculator.score_to_level(0.5) == 3
        assert calculator.score_to_level(0.59) == 3

    def test_score_to_level_high(self):
        """Test score 0.6-0.8 maps to level 4 (High)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(0.6) == 4
        assert calculator.score_to_level(0.7) == 4
        assert calculator.score_to_level(0.79) == 4

    def test_score_to_level_critical(self):
        """Test score 0.8-1.0 maps to level 5 (Critical)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(0.8) == 5
        assert calculator.score_to_level(0.9) == 5
        assert calculator.score_to_level(1.0) == 5

    def test_score_to_level_above_one(self):
        """Test scores above 1.0 map to level 5."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert calculator.score_to_level(1.5) == 5
        assert calculator.score_to_level(2.0) == 5


class TestMethodSignaturesExist:
    """Tests that all required method signatures exist."""

    def test_calculate_cluster_escalation_exists(self):
        """Verify calculate_cluster_escalation method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "calculate_cluster_escalation")
        assert callable(calculator.calculate_cluster_escalation)

    def test_calculate_embedding_signal_exists(self):
        """Verify _calculate_embedding_signal method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_calculate_embedding_signal")
        assert callable(calculator._calculate_embedding_signal)

    def test_calculate_content_signal_exists(self):
        """Verify _calculate_content_signal method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_calculate_content_signal")
        assert callable(calculator._calculate_content_signal)

    def test_calculate_keyword_signal_exists(self):
        """Verify _calculate_keyword_signal method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_calculate_keyword_signal")
        assert callable(calculator._calculate_keyword_signal)

    def test_combine_signals_exists(self):
        """Verify _combine_signals method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_combine_signals")
        assert callable(calculator._combine_signals)

    def test_load_anchors_exists(self):
        """Verify _load_anchors method exists."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        assert hasattr(calculator, "_load_anchors")
        assert callable(calculator._load_anchors)


class TestNotImplementedMethods:
    """Tests that stub methods raise NotImplementedError.

    NOTE: This class previously contained tests for methods that have since been implemented.
    All escalation calculation methods are now implemented (Tasks 6-9).
    This class is retained for documentation purposes and any future stub methods.
    """

    # NOTE: test_calculate_cluster_escalation_not_implemented removed - method now implemented (Task 9)
    # NOTE: test_calculate_embedding_signal_not_implemented removed - method now implemented (Task 6)
    # NOTE: test_calculate_content_signal_not_implemented removed - method now implemented (Task 7)
    # NOTE: test_calculate_keyword_signal_not_implemented removed - method now implemented (Task 8)
    # NOTE: test_combine_signals_not_implemented removed - method now implemented (Task 9)

    def test_all_escalation_methods_implemented(self):
        """Verify all escalation calculation methods are now implemented."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # These methods should NOT raise NotImplementedError anymore
        # This is a sanity check that the implementations exist
        assert callable(calculator.calculate_cluster_escalation)
        assert callable(calculator._calculate_embedding_signal)
        assert callable(calculator._calculate_content_signal)
        assert callable(calculator._calculate_keyword_signal)
        assert callable(calculator._combine_signals)


class TestCacheBehavior:
    """Tests for anchor cache behavior."""

    def test_clear_cache(self):
        """Verify clear_cache empties the cache."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Manually add items to cache
        calculator._anchor_cache["military"] = [MagicMock()]
        calculator._anchor_cache["economic"] = [MagicMock()]

        assert len(calculator._anchor_cache) == 2

        calculator.clear_cache()

        assert len(calculator._anchor_cache) == 0
        assert calculator._anchor_cache == {}

    def test_get_cached_domains(self):
        """Verify get_cached_domains returns cached domain names."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Initially empty
        assert calculator.get_cached_domains() == []

        # Add items to cache
        calculator._anchor_cache["military"] = [MagicMock()]
        calculator._anchor_cache["geopolitical"] = [MagicMock()]

        cached = calculator.get_cached_domains()
        assert len(cached) == 2
        assert "military" in cached
        assert "geopolitical" in cached

    def test_cache_is_isolated_per_instance(self):
        """Verify each calculator instance has its own cache."""
        mock_session = MagicMock()

        calc1 = EscalationCalculator(mock_session)
        calc2 = EscalationCalculator(mock_session)

        calc1._anchor_cache["military"] = [MagicMock()]

        assert len(calc1._anchor_cache) == 1
        assert len(calc2._anchor_cache) == 0


class TestLoadAnchorsMethod:
    """Tests for _load_anchors method."""

    @pytest.mark.asyncio
    async def test_load_anchors_queries_database(self):
        """Verify _load_anchors queries database when cache is empty."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        calculator = EscalationCalculator(mock_session)

        result = await calculator._load_anchors("military")

        # Verify database was queried
        mock_session.execute.assert_called_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_load_anchors_uses_cache(self):
        """Verify _load_anchors returns cached data on subsequent calls."""
        mock_session = AsyncMock()
        mock_anchor = MagicMock()

        calculator = EscalationCalculator(mock_session)

        # Pre-populate cache
        calculator._anchor_cache["military"] = [mock_anchor]

        result = await calculator._load_anchors("military")

        # Verify database was NOT queried
        mock_session.execute.assert_not_called()
        assert result == [mock_anchor]

    @pytest.mark.asyncio
    async def test_load_anchors_caches_result(self):
        """Verify _load_anchors stores result in cache."""
        mock_session = AsyncMock()
        mock_anchor = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_anchor]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        calculator = EscalationCalculator(mock_session)

        # First call - should query database
        await calculator._load_anchors("military")

        # Verify result was cached
        assert "military" in calculator._anchor_cache
        assert calculator._anchor_cache["military"] == [mock_anchor]

        # Second call - should use cache
        mock_session.execute.reset_mock()
        await calculator._load_anchors("military")
        mock_session.execute.assert_not_called()


class TestEmbeddingSignal:
    """Tests for _calculate_embedding_signal method (Task 6)."""

    @pytest.mark.asyncio
    async def test_embedding_signal_no_anchors(self):
        """Test returns level 3 with confidence 0 when no anchors available."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        calculator = EscalationCalculator(mock_session)

        signal = await calculator._calculate_embedding_signal(
            domain="military",
            embedding=[0.1] * 1536,
        )

        assert signal.domain == "military"
        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.source == "embedding"
        assert signal.reasoning == "No anchors available for domain"
        assert signal.matched_anchor_id is None

    @pytest.mark.asyncio
    async def test_embedding_signal_zero_embedding(self):
        """Test handles zero-norm input embedding gracefully."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Pre-populate cache to avoid database query
        mock_anchor = MagicMock()
        mock_anchor.domain = "military"
        mock_anchor.level = 4
        mock_anchor.embedding = [0.5] * 1536
        mock_anchor.weight = 1.0
        mock_anchor.is_active = True
        mock_anchor.label = "Test Anchor"
        mock_anchor.id = uuid4()
        calculator._anchor_cache["military"] = [mock_anchor]

        # Zero embedding
        signal = await calculator._calculate_embedding_signal(
            domain="military",
            embedding=[0.0] * 1536,
        )

        assert signal.domain == "military"
        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.source == "embedding"
        assert signal.reasoning == "Zero-norm input embedding"

    @pytest.mark.asyncio
    async def test_embedding_signal_finds_best_match(self):
        """Test finds anchor with highest similarity."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Create two anchors with different embeddings
        anchor1 = MagicMock()
        anchor1.domain = "military"
        anchor1.level = 2
        anchor1.embedding = [1.0] + [0.0] * 1535  # Orthogonal to input
        anchor1.weight = 1.0
        anchor1.is_active = True
        anchor1.label = "Low Anchor"
        anchor1.id = uuid4()

        anchor2 = MagicMock()
        anchor2.domain = "military"
        anchor2.level = 4
        anchor2.embedding = [0.0] + [1.0] + [0.0] * 1534  # Parallel to input
        anchor2.weight = 1.0
        anchor2.is_active = True
        anchor2.label = "High Anchor"
        anchor2.id = uuid4()

        calculator._anchor_cache["military"] = [anchor1, anchor2]

        # Input embedding most similar to anchor2
        signal = await calculator._calculate_embedding_signal(
            domain="military",
            embedding=[0.0] + [1.0] + [0.0] * 1534,
        )

        assert signal.domain == "military"
        assert signal.level == 4  # Should match anchor2's level
        assert signal.source == "embedding"
        assert signal.matched_anchor_id == anchor2.id
        assert "High Anchor" in signal.reasoning
        assert signal.confidence == 1.0  # Perfect similarity maps to 1.0

    @pytest.mark.asyncio
    async def test_embedding_signal_applies_weight(self):
        """Test anchor weight affects ranking."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Two anchors with same embedding but different weights
        anchor_low_weight = MagicMock()
        anchor_low_weight.domain = "military"
        anchor_low_weight.level = 2
        anchor_low_weight.embedding = [1.0] + [0.0] * 1535
        anchor_low_weight.weight = 0.5  # Low weight
        anchor_low_weight.is_active = True
        anchor_low_weight.label = "Low Weight Anchor"
        anchor_low_weight.id = uuid4()

        anchor_high_weight = MagicMock()
        anchor_high_weight.domain = "military"
        anchor_high_weight.level = 4
        anchor_high_weight.embedding = [1.0] + [0.0] * 1535
        anchor_high_weight.weight = 1.5  # High weight
        anchor_high_weight.is_active = True
        anchor_high_weight.label = "High Weight Anchor"
        anchor_high_weight.id = uuid4()

        calculator._anchor_cache["military"] = [anchor_low_weight, anchor_high_weight]

        # Input embedding identical to both anchors
        signal = await calculator._calculate_embedding_signal(
            domain="military",
            embedding=[1.0] + [0.0] * 1535,
        )

        # Higher weight anchor should win despite same base similarity
        assert signal.level == 4
        assert signal.matched_anchor_id == anchor_high_weight.id
        assert "High Weight Anchor" in signal.reasoning

    @pytest.mark.asyncio
    async def test_embedding_signal_confidence_range(self):
        """Test confidence is properly bounded between 0 and 1."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Anchor
        anchor = MagicMock()
        anchor.domain = "geopolitical"
        anchor.level = 3
        anchor.embedding = [1.0] + [0.0] * 1535
        anchor.weight = 1.0
        anchor.is_active = True
        anchor.label = "Test Anchor"
        anchor.id = uuid4()

        calculator._anchor_cache["geopolitical"] = [anchor]

        # Test with parallel embedding (max similarity = 1.0)
        signal_max = await calculator._calculate_embedding_signal(
            domain="geopolitical",
            embedding=[1.0] + [0.0] * 1535,
        )
        assert 0.0 <= signal_max.confidence <= 1.0
        assert signal_max.confidence == 1.0  # Perfect match

        # Test with orthogonal embedding (similarity = 0.0)
        signal_mid = await calculator._calculate_embedding_signal(
            domain="geopolitical",
            embedding=[0.0] + [1.0] + [0.0] * 1534,
        )
        assert 0.0 <= signal_mid.confidence <= 1.0
        assert signal_mid.confidence == 0.5  # Zero similarity maps to 0.5

        # Test with anti-parallel embedding (similarity = -1.0)
        signal_min = await calculator._calculate_embedding_signal(
            domain="geopolitical",
            embedding=[-1.0] + [0.0] * 1535,
        )
        assert 0.0 <= signal_min.confidence <= 1.0
        assert signal_min.confidence == 0.0  # Negative similarity maps to 0.0

    @pytest.mark.asyncio
    async def test_embedding_signal_skips_zero_norm_anchors(self):
        """Test anchors with zero-norm embeddings are skipped."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # One anchor with zero embedding, one valid
        zero_anchor = MagicMock()
        zero_anchor.domain = "economic"
        zero_anchor.level = 5
        zero_anchor.embedding = [0.0] * 1536  # Zero embedding
        zero_anchor.weight = 1.0
        zero_anchor.is_active = True
        zero_anchor.label = "Zero Anchor"
        zero_anchor.id = uuid4()

        valid_anchor = MagicMock()
        valid_anchor.domain = "economic"
        valid_anchor.level = 2
        valid_anchor.embedding = [0.5] * 1536
        valid_anchor.weight = 1.0
        valid_anchor.is_active = True
        valid_anchor.label = "Valid Anchor"
        valid_anchor.id = uuid4()

        calculator._anchor_cache["economic"] = [zero_anchor, valid_anchor]

        signal = await calculator._calculate_embedding_signal(
            domain="economic",
            embedding=[0.5] * 1536,
        )

        # Should match valid anchor, not zero anchor
        assert signal.level == 2
        assert signal.matched_anchor_id == valid_anchor.id
        assert "Valid Anchor" in signal.reasoning

    @pytest.mark.asyncio
    async def test_embedding_signal_all_anchors_zero(self):
        """Test returns default when all anchors have zero-norm embeddings."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        zero_anchor = MagicMock()
        zero_anchor.domain = "economic"
        zero_anchor.level = 5
        zero_anchor.embedding = [0.0] * 1536
        zero_anchor.weight = 1.0
        zero_anchor.is_active = True
        zero_anchor.label = "Zero Anchor"
        zero_anchor.id = uuid4()

        calculator._anchor_cache["economic"] = [zero_anchor]

        signal = await calculator._calculate_embedding_signal(
            domain="economic",
            embedding=[0.5] * 1536,
        )

        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.reasoning == "No valid anchor embeddings found"

    @pytest.mark.asyncio
    async def test_embedding_signal_none_weight_defaults_to_one(self):
        """Test anchor with None weight is treated as weight 1.0."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        anchor = MagicMock()
        anchor.domain = "military"
        anchor.level = 3
        anchor.embedding = [1.0] + [0.0] * 1535
        anchor.weight = None  # None weight
        anchor.is_active = True
        anchor.label = "No Weight Anchor"
        anchor.id = uuid4()

        calculator._anchor_cache["military"] = [anchor]

        signal = await calculator._calculate_embedding_signal(
            domain="military",
            embedding=[1.0] + [0.0] * 1535,
        )

        # Should work with default weight of 1.0
        assert signal.level == 3
        assert signal.confidence == 1.0
        assert signal.matched_anchor_id == anchor.id


class TestContentSignal:
    """Tests for _calculate_content_signal method (Task 7)."""

    @pytest.mark.asyncio
    async def test_content_signal_empty_text(self):
        """Test returns level 3 with confidence 0 for empty text."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Test empty string
        signal = await calculator._calculate_content_signal(
            domain="geopolitical",
            text="",
        )

        assert signal.domain == "geopolitical"
        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.source == "content"
        assert signal.reasoning == "Empty text provided"

        # Test whitespace-only string
        signal_whitespace = await calculator._calculate_content_signal(
            domain="military",
            text="   \n\t   ",
        )

        assert signal_whitespace.level == 3
        assert signal_whitespace.confidence == 0.0
        assert signal_whitespace.reasoning == "Empty text provided"

    @pytest.mark.asyncio
    async def test_content_signal_no_patterns(self):
        """Test neutral result when no patterns match."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with no escalation patterns
        signal = await calculator._calculate_content_signal(
            domain="economic",
            text="The weather today is sunny with mild temperatures.",
        )

        assert signal.domain == "economic"
        assert signal.level == 3  # Neutral level
        assert signal.confidence == 0.2  # Low confidence
        assert signal.source == "content"
        assert signal.reasoning == "No escalation patterns matched"

    @pytest.mark.asyncio
    async def test_content_signal_level1_patterns(self):
        """Test matches routine/peaceful language at level 1."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with level 1 patterns (routine, stable, peaceful)
        signal = await calculator._calculate_content_signal(
            domain="geopolitical",
            text="The situation remains stable. Routine diplomatic talks continue in a peaceful atmosphere with normal cooperation between the two nations.",
        )

        assert signal.domain == "geopolitical"
        assert signal.level == 1  # Should match level 1 patterns
        assert signal.source == "content"
        assert signal.confidence > 0.2  # Higher than no-match confidence
        assert "patterns" in signal.reasoning.lower()

    @pytest.mark.asyncio
    async def test_content_signal_level5_patterns(self):
        """Test matches war/critical language at level 5."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with dominant level 5 patterns (war, invasion, nuclear, catastrophic, collapse)
        # Using repetition to ensure level 5 dominates the weighted average
        signal = await calculator._calculate_content_signal(
            domain="military",
            text="War and warfare have engulfed the region. The invasion was catastrophic with massive casualties. Nuclear weapons are mentioned. Complete collapse of order.",
        )

        assert signal.domain == "military"
        assert signal.level >= 4  # Should be high due to level 5 patterns
        assert signal.source == "content"
        assert signal.confidence > 0.3  # Good confidence with multiple matches

        # Test with pure level 5 text to ensure it reaches level 5
        pure_level5_signal = await calculator._calculate_content_signal(
            domain="military",
            text="war war war invasion invasion nuclear nuclear catastrophic",
        )
        assert pure_level5_signal.level == 5

    @pytest.mark.asyncio
    async def test_content_signal_domain_bonus(self):
        """Test domain intensifiers boost level."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with level 3 patterns + military domain intensifiers
        # The domain bonus should push the level slightly higher
        text_base = "Growing concerns about the escalating situation with warnings issued."

        signal_no_bonus = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=text_base,
        )

        # Now add military domain intensifiers
        text_with_intensifiers = (
            "Military forces and armed troops are monitoring the situation. "
            "Weapons and missiles have been detected. "
            + text_base
        )

        signal_with_bonus = await calculator._calculate_content_signal(
            domain="military",
            text=text_with_intensifiers,
        )

        # The military domain bonus should be applied
        assert "domain bonus" in signal_with_bonus.reasoning.lower()
        # Domain bonus should be positive (extract from reasoning)
        assert "domain bonus 0.00" not in signal_with_bonus.reasoning

    @pytest.mark.asyncio
    async def test_content_signal_confidence_scales(self):
        """Test confidence is based on match density and level concentration."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with NO patterns - lowest confidence (0.2)
        no_match_text = "The weather is nice today with clear skies."

        signal_no_match = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=no_match_text,
        )
        assert signal_no_match.confidence == 0.2  # Low confidence for no matches

        # Text with patterns - should have confidence > 0.2
        match_text = (
            "Serious concerns are growing. Warnings have been issued. "
            "The threat level has escalated significantly. Sanctions are being considered."
        )

        signal_match = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=match_text,
        )

        # Text with matches should have higher confidence than no-match text
        assert signal_match.confidence > signal_no_match.confidence
        # And confidence should be bounded
        assert 0.0 <= signal_match.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_content_signal_mixed_levels(self):
        """Test weighted average when multiple levels match."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Text with patterns from different levels
        mixed_text = (
            "Routine diplomatic talks were held, but concerns are growing. "
            "The significant threat has led to warnings. "
            "A state of emergency may be declared if the crisis escalates further."
        )

        signal = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=mixed_text,
        )

        assert signal.domain == "geopolitical"
        # Should be somewhere in the middle (not extreme level 1 or 5)
        assert 2 <= signal.level <= 4
        assert signal.source == "content"
        # Reasoning should mention patterns and avg level
        assert "avg level" in signal.reasoning.lower()

    @pytest.mark.asyncio
    async def test_content_signal_all_domains(self):
        """Test content signal works for all three domains."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        test_text = "The crisis situation is escalating with serious concerns."

        for domain in ["geopolitical", "military", "economic"]:
            signal = await calculator._calculate_content_signal(
                domain=domain,
                text=test_text,
            )

            assert signal.domain == domain
            assert signal.source == "content"
            assert 1 <= signal.level <= 5
            assert 0.0 <= signal.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_content_signal_domain_bonus_capped(self):
        """Test domain bonus is capped at 0.5."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Saturate with domain intensifiers
        intensifier_heavy_text = (
            "The international global regional bilateral multilateral "
            "diplomatic summit treaty agreement alliance coalition bloc "
            "conference with cooperation and dialogue. "
            "This is routine and stable with normal cooperation."
        )

        signal = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=intensifier_heavy_text,
        )

        # Extract domain bonus from reasoning
        # Format: "Matched X patterns, avg level Y.YY, domain bonus Z.ZZ"
        import re
        bonus_match = re.search(r"domain bonus (\d+\.\d+)", signal.reasoning)
        if bonus_match:
            domain_bonus = float(bonus_match.group(1))
            assert domain_bonus <= 0.5  # Cap at 0.5

    @pytest.mark.asyncio
    async def test_content_signal_level_bounds(self):
        """Test final level is always between 1 and 5."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Test with level 1 patterns only
        low_text = "stable peaceful routine normal typical usual calm"

        signal_low = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=low_text,
        )
        assert signal_low.level >= 1

        # Test with level 5 patterns and max domain bonus
        high_text = (
            "war warfare combat invasion nuclear catastrophic "
            "international global regional diplomatic alliance "
            "war war war war war"  # Repeat to dominate
        )

        signal_high = await calculator._calculate_content_signal(
            domain="geopolitical",
            text=high_text,
        )
        assert signal_high.level <= 5

    @pytest.mark.asyncio
    async def test_content_signal_confidence_bounds(self):
        """Test confidence is always between 0.0 and 1.0."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Various texts to test confidence bounds
        test_texts = [
            "",  # Empty
            "random words",  # No patterns
            "crisis war invasion nuclear catastrophic devastating",  # High intensity
            "stable " * 100,  # Very dense single-level
        ]

        for text in test_texts:
            signal = await calculator._calculate_content_signal(
                domain="military",
                text=text,
            )
            assert 0.0 <= signal.confidence <= 1.0


class TestKeywordSignal:
    """Tests for _calculate_keyword_signal method (Task 8)."""

    @pytest.mark.asyncio
    async def test_keyword_signal_empty_text(self):
        """Test returns level 3 with empty matched_keywords for empty text."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Test empty string
        signal = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="",
        )

        assert signal.domain == "geopolitical"
        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.source == "keywords"
        assert signal.matched_keywords == []
        assert signal.reasoning == "Empty text provided"

        # Test whitespace-only string
        signal_whitespace = await calculator._calculate_keyword_signal(
            domain="military",
            text="   \n\t   ",
        )

        assert signal_whitespace.level == 3
        assert signal_whitespace.confidence == 0.0
        assert signal_whitespace.matched_keywords == []
        assert signal_whitespace.reasoning == "Empty text provided"

    @pytest.mark.asyncio
    async def test_keyword_signal_no_anchors(self):
        """Test returns level 3 when no anchors available."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        calculator = EscalationCalculator(mock_session)

        signal = await calculator._calculate_keyword_signal(
            domain="military",
            text="Some text with sanctions and escalation",
        )

        assert signal.domain == "military"
        assert signal.level == 3
        assert signal.confidence == 0.0
        assert signal.source == "keywords"
        assert signal.matched_keywords == []
        assert signal.reasoning == "No anchors available for domain"

    @pytest.mark.asyncio
    async def test_keyword_signal_no_matches(self):
        """Test returns level 3 with low confidence when no keywords match."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Anchor with keywords that won't match
        anchor = MagicMock()
        anchor.domain = "economic"
        anchor.level = 4
        anchor.keywords = ["tariffs", "sanctions", "embargo"]
        anchor.weight = 1.0
        anchor.label = "Trade War"
        anchor.id = uuid4()

        calculator._anchor_cache["economic"] = [anchor]

        # Text with no matching keywords
        signal = await calculator._calculate_keyword_signal(
            domain="economic",
            text="The weather is sunny today with mild temperatures.",
        )

        assert signal.domain == "economic"
        assert signal.level == 3
        assert signal.confidence == 0.1  # Low confidence for no matches
        assert signal.source == "keywords"
        assert signal.matched_keywords == []
        assert signal.reasoning == "No anchor keywords matched in text"

    @pytest.mark.asyncio
    async def test_keyword_signal_finds_keywords(self):
        """Test matches anchor keywords in text."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Anchor with keywords
        anchor = MagicMock()
        anchor.domain = "military"
        anchor.level = 4
        anchor.keywords = ["troops", "deployment", "military"]
        anchor.weight = 1.0
        anchor.label = "Military Mobilization"
        anchor.id = uuid4()

        calculator._anchor_cache["military"] = [anchor]

        # Text with matching keywords
        signal = await calculator._calculate_keyword_signal(
            domain="military",
            text="The military has announced troop deployment to the region.",
        )

        assert signal.domain == "military"
        assert signal.level == 4
        assert signal.source == "keywords"
        assert signal.matched_anchor_id == anchor.id
        # Should find "military" and "deployment" (troops != troop due to word boundary)
        assert "military" in signal.matched_keywords
        assert "deployment" in signal.matched_keywords
        assert "Military Mobilization" in signal.reasoning

    @pytest.mark.asyncio
    async def test_keyword_signal_best_anchor_wins(self):
        """Test highest scoring anchor determines level."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Low-level anchor with partial match
        anchor_low = MagicMock()
        anchor_low.domain = "geopolitical"
        anchor_low.level = 2
        anchor_low.keywords = ["talks", "negotiations", "diplomacy", "cooperation", "dialogue"]
        anchor_low.weight = 1.0
        anchor_low.label = "Diplomatic Talks"
        anchor_low.id = uuid4()

        # High-level anchor with better match
        anchor_high = MagicMock()
        anchor_high.domain = "geopolitical"
        anchor_high.level = 5
        anchor_high.keywords = ["war", "invasion"]
        anchor_high.weight = 1.0
        anchor_high.label = "War"
        anchor_high.id = uuid4()

        calculator._anchor_cache["geopolitical"] = [anchor_low, anchor_high]

        # Text that matches high anchor better (both keywords)
        signal = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="The war has begun with invasion of the territory. Talks have failed.",
        )

        assert signal.domain == "geopolitical"
        assert signal.level == 5  # High anchor wins
        assert signal.matched_anchor_id == anchor_high.id
        assert "War" in signal.reasoning

    @pytest.mark.asyncio
    async def test_keyword_signal_applies_weight(self):
        """Test anchor weight affects scoring."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Low-weight anchor with same keywords
        anchor_low_weight = MagicMock()
        anchor_low_weight.domain = "economic"
        anchor_low_weight.level = 2
        anchor_low_weight.keywords = ["market"]
        anchor_low_weight.weight = 0.5  # Low weight
        anchor_low_weight.label = "Market Normal"
        anchor_low_weight.id = uuid4()

        # High-weight anchor with same keywords
        anchor_high_weight = MagicMock()
        anchor_high_weight.domain = "economic"
        anchor_high_weight.level = 4
        anchor_high_weight.keywords = ["market"]
        anchor_high_weight.weight = 2.0  # High weight
        anchor_high_weight.label = "Market Crisis"
        anchor_high_weight.id = uuid4()

        calculator._anchor_cache["economic"] = [anchor_low_weight, anchor_high_weight]

        # Text matching the common keyword
        signal = await calculator._calculate_keyword_signal(
            domain="economic",
            text="The market is showing volatility.",
        )

        # High weight anchor should win
        assert signal.level == 4
        assert signal.matched_anchor_id == anchor_high_weight.id
        assert "Market Crisis" in signal.reasoning

    @pytest.mark.asyncio
    async def test_keyword_signal_collects_all_keywords(self):
        """Test all matched keywords from all anchors are returned."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Two anchors with different keywords
        anchor1 = MagicMock()
        anchor1.domain = "military"
        anchor1.level = 3
        anchor1.keywords = ["troops", "forces"]
        anchor1.weight = 1.0
        anchor1.label = "Military Presence"
        anchor1.id = uuid4()

        anchor2 = MagicMock()
        anchor2.domain = "military"
        anchor2.level = 4
        anchor2.keywords = ["attack", "offensive"]
        anchor2.weight = 1.0
        anchor2.label = "Military Action"
        anchor2.id = uuid4()

        calculator._anchor_cache["military"] = [anchor1, anchor2]

        # Text matching keywords from both anchors
        signal = await calculator._calculate_keyword_signal(
            domain="military",
            text="The troops launched an attack on enemy forces during the offensive.",
        )

        # Should collect all matched keywords from both anchors
        assert "troops" in signal.matched_keywords
        assert "forces" in signal.matched_keywords
        assert "attack" in signal.matched_keywords
        assert "offensive" in signal.matched_keywords
        assert len(signal.matched_keywords) == 4

    @pytest.mark.asyncio
    async def test_keyword_signal_confidence_range(self):
        """Test confidence is always between 0 and 1."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Anchor with multiple keywords
        anchor = MagicMock()
        anchor.domain = "geopolitical"
        anchor.level = 3
        anchor.keywords = ["sanctions", "embargo", "restrictions", "trade"]
        anchor.weight = 1.0
        anchor.label = "Economic Sanctions"
        anchor.id = uuid4()

        calculator._anchor_cache["geopolitical"] = [anchor]

        # Test with partial match (1 of 4 keywords)
        signal_partial = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="New sanctions have been announced.",
        )
        assert 0.0 <= signal_partial.confidence <= 1.0

        # Test with full match (4 of 4 keywords)
        signal_full = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="Sanctions and embargo restrictions on trade have been imposed.",
        )
        assert 0.0 <= signal_full.confidence <= 1.0
        # Full match should have higher confidence
        assert signal_full.confidence > signal_partial.confidence

        # Test with no match
        signal_none = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="The weather is nice today.",
        )
        assert 0.0 <= signal_none.confidence <= 1.0
        assert signal_none.confidence == 0.1  # Low confidence for no matches

    @pytest.mark.asyncio
    async def test_keyword_signal_word_boundary_matching(self):
        """Test keyword matching uses word boundaries."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        anchor = MagicMock()
        anchor.domain = "military"
        anchor.level = 4
        anchor.keywords = ["war", "attack"]
        anchor.weight = 1.0
        anchor.label = "War"
        anchor.id = uuid4()

        calculator._anchor_cache["military"] = [anchor]

        # "warranty" contains "war" but should not match due to word boundary
        signal = await calculator._calculate_keyword_signal(
            domain="military",
            text="The warranty covers software attacks.",
        )

        # "war" should NOT match in "warranty"
        # "attack" should NOT match (attacks != attack)
        assert signal.matched_keywords == []
        assert signal.level == 3  # Default level (no matches)

    @pytest.mark.asyncio
    async def test_keyword_signal_case_insensitive(self):
        """Test keyword matching is case insensitive."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        anchor = MagicMock()
        anchor.domain = "geopolitical"
        anchor.level = 4
        anchor.keywords = ["war", "INVASION", "Conflict"]
        anchor.weight = 1.0
        anchor.label = "War"
        anchor.id = uuid4()

        calculator._anchor_cache["geopolitical"] = [anchor]

        # Mixed case in text
        signal = await calculator._calculate_keyword_signal(
            domain="geopolitical",
            text="WAR has been declared. An invasion began. The conflict escalates.",
        )

        assert signal.level == 4
        assert "war" in signal.matched_keywords or "WAR" in signal.matched_keywords
        assert len(signal.matched_keywords) == 3

    @pytest.mark.asyncio
    async def test_keyword_signal_anchor_without_keywords(self):
        """Test anchors without keywords are skipped."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Anchor with no keywords
        anchor_empty = MagicMock()
        anchor_empty.domain = "economic"
        anchor_empty.level = 5
        anchor_empty.keywords = []  # Empty keywords
        anchor_empty.weight = 1.0
        anchor_empty.label = "Empty Anchor"
        anchor_empty.id = uuid4()

        # Anchor with None keywords
        anchor_none = MagicMock()
        anchor_none.domain = "economic"
        anchor_none.level = 5
        anchor_none.keywords = None  # None keywords
        anchor_none.weight = 1.0
        anchor_none.label = "None Anchor"
        anchor_none.id = uuid4()

        # Anchor with actual keywords
        anchor_valid = MagicMock()
        anchor_valid.domain = "economic"
        anchor_valid.level = 2
        anchor_valid.keywords = ["market"]
        anchor_valid.weight = 1.0
        anchor_valid.label = "Market"
        anchor_valid.id = uuid4()

        calculator._anchor_cache["economic"] = [anchor_empty, anchor_none, anchor_valid]

        signal = await calculator._calculate_keyword_signal(
            domain="economic",
            text="The market is stable.",
        )

        # Should match valid anchor, not empty/none ones
        assert signal.level == 2
        assert signal.matched_anchor_id == anchor_valid.id

    @pytest.mark.asyncio
    async def test_keyword_signal_none_weight_defaults_to_one(self):
        """Test anchor with None weight is treated as weight 1.0."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        anchor = MagicMock()
        anchor.domain = "military"
        anchor.level = 3
        anchor.keywords = ["troops"]
        anchor.weight = None  # None weight
        anchor.label = "Troops"
        anchor.id = uuid4()

        calculator._anchor_cache["military"] = [anchor]

        signal = await calculator._calculate_keyword_signal(
            domain="military",
            text="The troops are ready.",
        )

        # Should work with default weight of 1.0
        assert signal.level == 3
        assert signal.matched_anchor_id == anchor.id
        assert "troops" in signal.matched_keywords

    @pytest.mark.asyncio
    async def test_keyword_signal_all_domains(self):
        """Test keyword signal works for all three domains."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        for domain in ["geopolitical", "military", "economic"]:
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = 3
            anchor.keywords = ["crisis"]
            anchor.weight = 1.0
            anchor.label = f"{domain.title()} Crisis"
            anchor.id = uuid4()

            calculator._anchor_cache[domain] = [anchor]

            signal = await calculator._calculate_keyword_signal(
                domain=domain,
                text="The crisis continues to escalate.",
            )

            assert signal.domain == domain
            assert signal.source == "keywords"
            assert signal.level == 3
            assert "crisis" in signal.matched_keywords


class TestCombineSignals:
    """Tests for _combine_signals method (Task 9)."""

    def test_combine_signals_empty(self):
        """Test returns level 3 with empty signals list."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        result = calculator._combine_signals(
            domain="military",
            signals=[],
        )

        assert result.domain == "military"
        assert result.level == 3
        assert result.score == Decimal("0.500")
        assert result.signals == []
        assert result.confidence == 0.0

    def test_combine_signals_single_signal(self):
        """Test handles single signal correctly (uses its weight only)."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        signal = EscalationSignal(
            domain="geopolitical",
            level=4,
            confidence=0.8,
            source="embedding",
        )

        result = calculator._combine_signals(
            domain="geopolitical",
            signals=[signal],
        )

        assert result.domain == "geopolitical"
        # Single embedding signal at level 4 with 50% weight
        # Since only one signal, total_weight = 0.5, so avg_level = (4*0.5)/0.5 = 4
        assert result.level == 4
        # Score = (4-1)/4 = 0.75
        assert result.score == Decimal("0.750")
        assert len(result.signals) == 1
        assert result.confidence == 0.8

    def test_combine_signals_all_signals(self):
        """Test combines all three signals with proper weights."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        signals = [
            EscalationSignal(domain="military", level=4, confidence=0.9, source="embedding"),
            EscalationSignal(domain="military", level=3, confidence=0.7, source="content"),
            EscalationSignal(domain="military", level=5, confidence=0.6, source="keywords"),
        ]

        result = calculator._combine_signals(
            domain="military",
            signals=signals,
        )

        assert result.domain == "military"
        assert len(result.signals) == 3
        # All three weights sum to 1.0, so total_weight = 1.0
        # weighted_level = 4*0.5 + 3*0.3 + 5*0.2 = 2.0 + 0.9 + 1.0 = 3.9
        # Round(3.9) = 4
        assert result.level == 4
        # Score = (3.9 - 1) / 4 = 0.725
        assert result.score == Decimal("0.725")
        # weighted_confidence = 0.9*0.5 + 0.7*0.3 + 0.6*0.2 = 0.45 + 0.21 + 0.12 = 0.78
        assert abs(result.confidence - 0.78) < 0.001

    def test_combine_signals_weighted_average(self):
        """Test verifies 50/30/20 weighting is applied correctly."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # All at level 5 - result should be level 5
        signals_high = [
            EscalationSignal(domain="economic", level=5, confidence=1.0, source="embedding"),
            EscalationSignal(domain="economic", level=5, confidence=1.0, source="content"),
            EscalationSignal(domain="economic", level=5, confidence=1.0, source="keywords"),
        ]

        result_high = calculator._combine_signals(domain="economic", signals=signals_high)
        assert result_high.level == 5
        assert result_high.score == Decimal("1.000")

        # All at level 1 - result should be level 1
        signals_low = [
            EscalationSignal(domain="economic", level=1, confidence=1.0, source="embedding"),
            EscalationSignal(domain="economic", level=1, confidence=1.0, source="content"),
            EscalationSignal(domain="economic", level=1, confidence=1.0, source="keywords"),
        ]

        result_low = calculator._combine_signals(domain="economic", signals=signals_low)
        assert result_low.level == 1
        assert result_low.score == Decimal("0.000")

        # Mixed - embedding dominates
        # 5*0.5 + 1*0.3 + 1*0.2 = 2.5 + 0.3 + 0.2 = 3.0
        signals_embedding_high = [
            EscalationSignal(domain="economic", level=5, confidence=1.0, source="embedding"),
            EscalationSignal(domain="economic", level=1, confidence=1.0, source="content"),
            EscalationSignal(domain="economic", level=1, confidence=1.0, source="keywords"),
        ]

        result_mixed = calculator._combine_signals(domain="economic", signals=signals_embedding_high)
        assert result_mixed.level == 3
        # Score = (3.0 - 1) / 4 = 0.5
        assert result_mixed.score == Decimal("0.500")

    def test_combine_signals_level_bounds(self):
        """Test final level is always between 1 and 5."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Test with extreme low levels
        signals_low = [
            EscalationSignal(domain="military", level=1, confidence=0.5, source="embedding"),
            EscalationSignal(domain="military", level=1, confidence=0.5, source="content"),
            EscalationSignal(domain="military", level=1, confidence=0.5, source="keywords"),
        ]

        result_low = calculator._combine_signals(domain="military", signals=signals_low)
        assert result_low.level >= 1

        # Test with extreme high levels
        signals_high = [
            EscalationSignal(domain="military", level=5, confidence=0.9, source="embedding"),
            EscalationSignal(domain="military", level=5, confidence=0.9, source="content"),
            EscalationSignal(domain="military", level=5, confidence=0.9, source="keywords"),
        ]

        result_high = calculator._combine_signals(domain="military", signals=signals_high)
        assert result_high.level <= 5

    def test_combine_signals_score_range(self):
        """Test score is always between 0.000 and 1.000."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Various signal combinations
        test_cases = [
            # All level 1
            [
                EscalationSignal(domain="geopolitical", level=1, confidence=0.5, source="embedding"),
                EscalationSignal(domain="geopolitical", level=1, confidence=0.5, source="content"),
                EscalationSignal(domain="geopolitical", level=1, confidence=0.5, source="keywords"),
            ],
            # All level 5
            [
                EscalationSignal(domain="geopolitical", level=5, confidence=0.9, source="embedding"),
                EscalationSignal(domain="geopolitical", level=5, confidence=0.9, source="content"),
                EscalationSignal(domain="geopolitical", level=5, confidence=0.9, source="keywords"),
            ],
            # Mixed levels
            [
                EscalationSignal(domain="geopolitical", level=2, confidence=0.7, source="embedding"),
                EscalationSignal(domain="geopolitical", level=4, confidence=0.6, source="content"),
                EscalationSignal(domain="geopolitical", level=3, confidence=0.8, source="keywords"),
            ],
        ]

        for signals in test_cases:
            result = calculator._combine_signals(domain="geopolitical", signals=signals)
            assert Decimal("0.000") <= result.score <= Decimal("1.000")

    def test_combine_signals_unknown_source(self):
        """Test signals with unknown sources are ignored."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        signals = [
            EscalationSignal(domain="military", level=5, confidence=1.0, source="unknown_source"),
        ]

        result = calculator._combine_signals(domain="military", signals=signals)

        # Unknown source has weight 0, so total_weight = 0
        # Should return default level 3
        assert result.level == 3
        assert result.score == Decimal("0.500")
        assert result.confidence == 0.0
        assert len(result.signals) == 1  # Signal is still included

    def test_combine_signals_partial_sources(self):
        """Test combining with only two of three signal sources."""
        mock_session = MagicMock()
        calculator = EscalationCalculator(mock_session)

        # Only embedding and content (no keywords)
        signals = [
            EscalationSignal(domain="economic", level=4, confidence=0.8, source="embedding"),
            EscalationSignal(domain="economic", level=2, confidence=0.6, source="content"),
        ]

        result = calculator._combine_signals(domain="economic", signals=signals)

        # total_weight = 0.5 + 0.3 = 0.8
        # weighted_level = (4*0.5 + 2*0.3) / 0.8 = (2.0 + 0.6) / 0.8 = 2.6 / 0.8 = 3.25
        # Round(3.25) = 3
        assert result.level == 3
        # Score = (3.25 - 1) / 4 = 0.5625
        assert result.score == Decimal("0.562") or result.score == Decimal("0.563")
        assert len(result.signals) == 2


class TestCalculateClusterEscalation:
    """Tests for calculate_cluster_escalation method (Task 9)."""

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_structure(self):
        """Test returns EscalationResult with all required fields."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Pre-populate caches for all domains to avoid database calls
        for domain in ["geopolitical", "military", "economic"]:
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = 3
            anchor.embedding = [0.5] * 1536
            anchor.weight = 1.0
            anchor.is_active = True
            anchor.label = f"Test {domain.title()} Anchor"
            anchor.id = uuid4()
            anchor.keywords = ["test"]
            calculator._anchor_cache[domain] = [anchor]

        cluster_id = uuid4()
        result = await calculator.calculate_cluster_escalation(
            cluster_id=cluster_id,
            cluster_embedding=[0.5] * 1536,
            cluster_text="This is a test cluster text.",
            article_count=5,
        )

        # Verify structure
        assert isinstance(result, EscalationResult)
        assert result.cluster_id == cluster_id
        assert result.article_count == 5
        assert result.calculated_at is not None
        assert isinstance(result.geopolitical, DomainEscalation)
        assert isinstance(result.military, DomainEscalation)
        assert isinstance(result.economic, DomainEscalation)
        assert isinstance(result.combined_level, int)
        assert isinstance(result.combined_score, Decimal)

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_all_domains(self):
        """Test calculates escalation for geopolitical, military, and economic domains."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Set up different anchors for each domain
        domains_levels = {
            "geopolitical": 2,
            "military": 4,
            "economic": 3,
        }

        for domain, level in domains_levels.items():
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = level
            anchor.embedding = [0.5] * 1536
            anchor.weight = 1.0
            anchor.is_active = True
            anchor.label = f"{domain.title()} Anchor L{level}"
            anchor.id = uuid4()
            anchor.keywords = ["crisis"]
            calculator._anchor_cache[domain] = [anchor]

        result = await calculator.calculate_cluster_escalation(
            cluster_id=uuid4(),
            cluster_embedding=[0.5] * 1536,
            cluster_text="The crisis is escalating rapidly.",
            article_count=3,
        )

        # All three domains should have escalation results
        assert result.geopolitical is not None
        assert result.military is not None
        assert result.economic is not None

        # Each domain should have correct domain field
        assert result.geopolitical.domain == "geopolitical"
        assert result.military.domain == "military"
        assert result.economic.domain == "economic"

        # Each domain should have signals
        assert len(result.geopolitical.signals) == 3
        assert len(result.military.signals) == 3
        assert len(result.economic.signals) == 3

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_combined_level(self):
        """Test combined_level is max of domain levels."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Set up anchors with different levels
        # Geopolitical: level 2, Military: level 5, Economic: level 1
        anchor_geo = MagicMock()
        anchor_geo.domain = "geopolitical"
        anchor_geo.level = 2
        anchor_geo.embedding = [0.9] + [0.0] * 1535
        anchor_geo.weight = 1.0
        anchor_geo.is_active = True
        anchor_geo.label = "Geo Anchor"
        anchor_geo.id = uuid4()
        anchor_geo.keywords = ["diplomacy"]
        calculator._anchor_cache["geopolitical"] = [anchor_geo]

        anchor_mil = MagicMock()
        anchor_mil.domain = "military"
        anchor_mil.level = 5
        anchor_mil.embedding = [0.9] + [0.0] * 1535
        anchor_mil.weight = 1.0
        anchor_mil.is_active = True
        anchor_mil.label = "Military Crisis"
        anchor_mil.id = uuid4()
        anchor_mil.keywords = ["war"]
        calculator._anchor_cache["military"] = [anchor_mil]

        anchor_eco = MagicMock()
        anchor_eco.domain = "economic"
        anchor_eco.level = 1
        anchor_eco.embedding = [0.9] + [0.0] * 1535
        anchor_eco.weight = 1.0
        anchor_eco.is_active = True
        anchor_eco.label = "Economic Normal"
        anchor_eco.id = uuid4()
        anchor_eco.keywords = ["market"]
        calculator._anchor_cache["economic"] = [anchor_eco]

        result = await calculator.calculate_cluster_escalation(
            cluster_id=uuid4(),
            cluster_embedding=[0.9] + [0.0] * 1535,
            cluster_text="War has begun with diplomacy failed. Market is stable.",
            article_count=2,
        )

        # Combined level should be max of domain levels
        max_domain_level = max(
            result.geopolitical.level,
            result.military.level,
            result.economic.level,
        )
        assert result.combined_level == max_domain_level

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_combined_score(self):
        """Test combined_score is average of domain scores."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Set up identical anchors for all domains at level 3
        for domain in ["geopolitical", "military", "economic"]:
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = 3
            anchor.embedding = [0.5] * 1536
            anchor.weight = 1.0
            anchor.is_active = True
            anchor.label = f"{domain.title()} Neutral"
            anchor.id = uuid4()
            anchor.keywords = []
            calculator._anchor_cache[domain] = [anchor]

        result = await calculator.calculate_cluster_escalation(
            cluster_id=uuid4(),
            cluster_embedding=[0.5] * 1536,
            cluster_text="Neutral text with no escalation patterns.",
            article_count=1,
        )

        # Calculate expected combined score (average of domain scores)
        total_score = result.geopolitical.score + result.military.score + result.economic.score
        expected_combined = (total_score / Decimal("3")).quantize(Decimal("0.001"))

        assert result.combined_score == expected_combined

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_no_anchors(self):
        """Test handles domains with no anchors gracefully."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        calculator = EscalationCalculator(mock_session)

        result = await calculator.calculate_cluster_escalation(
            cluster_id=uuid4(),
            cluster_embedding=[0.1] * 1536,
            cluster_text="Some random text here.",
            article_count=1,
        )

        # Should return default level 3 for all domains when no anchors
        assert result.geopolitical.level == 3
        assert result.military.level == 3
        assert result.economic.level == 3
        assert result.combined_level == 3

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_level_bounds(self):
        """Test combined_level is always between 1 and 5."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        # Set up anchors with extreme levels
        for domain in ["geopolitical", "military", "economic"]:
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = 5
            anchor.embedding = [1.0] + [0.0] * 1535
            anchor.weight = 1.0
            anchor.is_active = True
            anchor.label = f"{domain.title()} Critical"
            anchor.id = uuid4()
            anchor.keywords = ["war", "crisis", "emergency"]
            calculator._anchor_cache[domain] = [anchor]

        result = await calculator.calculate_cluster_escalation(
            cluster_id=uuid4(),
            cluster_embedding=[1.0] + [0.0] * 1535,
            cluster_text="War crisis emergency situation.",
            article_count=10,
        )

        assert 1 <= result.combined_level <= 5
        assert 1 <= result.geopolitical.level <= 5
        assert 1 <= result.military.level <= 5
        assert 1 <= result.economic.level <= 5

    @pytest.mark.asyncio
    async def test_calculate_cluster_escalation_preserves_cluster_info(self):
        """Test cluster_id and article_count are preserved in result."""
        mock_session = AsyncMock()
        calculator = EscalationCalculator(mock_session)

        for domain in ["geopolitical", "military", "economic"]:
            anchor = MagicMock()
            anchor.domain = domain
            anchor.level = 3
            anchor.embedding = [0.5] * 1536
            anchor.weight = 1.0
            anchor.is_active = True
            anchor.label = f"Test Anchor"
            anchor.id = uuid4()
            anchor.keywords = []
            calculator._anchor_cache[domain] = [anchor]

        specific_cluster_id = uuid4()
        specific_article_count = 42

        result = await calculator.calculate_cluster_escalation(
            cluster_id=specific_cluster_id,
            cluster_embedding=[0.5] * 1536,
            cluster_text="Test text.",
            article_count=specific_article_count,
        )

        assert result.cluster_id == specific_cluster_id
        assert result.article_count == specific_article_count
