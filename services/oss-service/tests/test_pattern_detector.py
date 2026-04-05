"""
Unit Tests for PatternDetector.

Tests entity and relationship pattern detection with mock Neo4j data.
"""
import pytest
from unittest.mock import MagicMock

from app.analyzers.pattern_detector import PatternDetector
from app.models.proposal import ChangeType, Severity
from tests.conftest import assert_valid_proposal, assert_proposal_count


class TestPatternDetector:
    """Tests for PatternDetector class."""

    # ========================================================================
    # Entity Pattern Detection Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_entity_patterns_with_results(
        self, pattern_detector, mock_neo4j, entity_pattern_data
    ):
        """Test entity pattern detection with valid data."""
        mock_neo4j.execute_read.return_value = entity_pattern_data

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 3)
        for proposal in proposals:
            assert_valid_proposal(proposal)
            assert proposal.change_type == ChangeType.NEW_ENTITY_TYPE

    @pytest.mark.asyncio
    async def test_detect_entity_patterns_empty_results(
        self, pattern_detector, mock_neo4j
    ):
        """Test entity pattern detection with no results."""
        mock_neo4j.execute_read.return_value = []

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 0)

    @pytest.mark.asyncio
    async def test_entity_pattern_confidence_calculation(
        self, pattern_detector, mock_neo4j
    ):
        """Test confidence calculation for entity patterns."""
        # High count should give higher confidence
        mock_neo4j.execute_read.return_value = [
            {"type": "PERSON", "count": 200, "sample_ids": [1, 2, 3]}
        ]

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 1)
        # confidence = min(0.5 + (count/100) * 0.4, 0.95)
        # For count=200: min(0.5 + 2*0.4, 0.95) = min(1.3, 0.95) = 0.95
        assert proposals[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_entity_pattern_low_count_confidence(
        self, pattern_detector, mock_neo4j
    ):
        """Test confidence calculation for low count patterns."""
        mock_neo4j.execute_read.return_value = [
            {"type": "RARE_TYPE", "count": 25, "sample_ids": [1]}
        ]

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 1)
        # For count=25: min(0.5 + 0.25*0.4, 0.95) = min(0.6, 0.95) = 0.6
        assert proposals[0].confidence == 0.6

    @pytest.mark.asyncio
    async def test_entity_pattern_severity_high_count(
        self, pattern_detector, mock_neo4j
    ):
        """Test severity is HIGH for count > 50."""
        mock_neo4j.execute_read.return_value = [
            {"type": "IMPORTANT_TYPE", "count": 100, "sample_ids": [1, 2]}
        ]

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 1)
        assert proposals[0].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_entity_pattern_severity_medium_count(
        self, pattern_detector, mock_neo4j
    ):
        """Test severity is MEDIUM for count <= 50."""
        mock_neo4j.execute_read.return_value = [
            {"type": "MINOR_TYPE", "count": 30, "sample_ids": [1]}
        ]

        proposals = await pattern_detector.detect_entity_patterns()

        assert_proposal_count(proposals, 1)
        assert proposals[0].severity == Severity.MEDIUM

    @pytest.mark.asyncio
    async def test_entity_pattern_skips_empty_type(
        self, pattern_detector, mock_neo4j
    ):
        """Test that empty type values are skipped."""
        mock_neo4j.execute_read.return_value = [
            {"type": "", "count": 50, "sample_ids": [1]},
            {"type": None, "count": 30, "sample_ids": [2]},
            {"type": "VALID_TYPE", "count": 40, "sample_ids": [3]},
        ]

        proposals = await pattern_detector.detect_entity_patterns()

        # Only VALID_TYPE should generate a proposal
        assert_proposal_count(proposals, 1)
        assert "VALID_TYPE" in proposals[0].title

    @pytest.mark.asyncio
    async def test_entity_pattern_database_error(
        self, pattern_detector, mock_neo4j
    ):
        """Test graceful handling of database errors."""
        mock_neo4j.execute_read.side_effect = Exception("Database connection lost")

        proposals = await pattern_detector.detect_entity_patterns()

        # Should return empty list on error, not raise
        assert_proposal_count(proposals, 0)

    # ========================================================================
    # Relationship Pattern Detection Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_relationship_patterns_with_results(
        self, pattern_detector, mock_neo4j, relationship_pattern_data
    ):
        """Test relationship pattern detection with valid data."""
        mock_neo4j.execute_read.return_value = relationship_pattern_data

        proposals = await pattern_detector.detect_relationship_patterns()

        assert_proposal_count(proposals, 3)
        for proposal in proposals:
            assert_valid_proposal(proposal)
            assert proposal.change_type == ChangeType.NEW_RELATIONSHIP_TYPE

    @pytest.mark.asyncio
    async def test_detect_relationship_patterns_empty_results(
        self, pattern_detector, mock_neo4j
    ):
        """Test relationship pattern detection with no results."""
        mock_neo4j.execute_read.return_value = []

        proposals = await pattern_detector.detect_relationship_patterns()

        assert_proposal_count(proposals, 0)

    @pytest.mark.asyncio
    async def test_relationship_pattern_confidence_calculation(
        self, pattern_detector, mock_neo4j
    ):
        """Test confidence calculation for relationship patterns."""
        mock_neo4j.execute_read.return_value = [
            {"source_type": "PERSON", "target_type": "ORG", "count": 100}
        ]

        proposals = await pattern_detector.detect_relationship_patterns()

        assert_proposal_count(proposals, 1)
        # confidence = min(0.5 + (count/50) * 0.3, 0.90)
        # For count=100: min(0.5 + 2*0.3, 0.90) = min(1.1, 0.90) = 0.90
        assert proposals[0].confidence == 0.90

    @pytest.mark.asyncio
    async def test_relationship_pattern_skips_null_types(
        self, pattern_detector, mock_neo4j
    ):
        """Test that null source/target types are skipped."""
        mock_neo4j.execute_read.return_value = [
            {"source_type": None, "target_type": "ORG", "count": 50},
            {"source_type": "PERSON", "target_type": None, "count": 30},
            {"source_type": "VALID_A", "target_type": "VALID_B", "count": 40},
        ]

        proposals = await pattern_detector.detect_relationship_patterns()

        assert_proposal_count(proposals, 1)
        assert "VALID_A" in proposals[0].title

    @pytest.mark.asyncio
    async def test_relationship_pattern_database_error(
        self, pattern_detector, mock_neo4j
    ):
        """Test graceful handling of database errors."""
        mock_neo4j.execute_read.side_effect = Exception("Query timeout")

        proposals = await pattern_detector.detect_relationship_patterns()

        assert_proposal_count(proposals, 0)

    # ========================================================================
    # Proposal Creation Tests
    # ========================================================================

    def test_create_entity_type_proposal_structure(self, pattern_detector):
        """Test entity type proposal has correct structure."""
        proposal = pattern_detector._create_entity_type_proposal(
            type_value="TEST_TYPE",
            count=100,
            sample_ids=[1, 2, 3]
        )

        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.NEW_ENTITY_TYPE
        assert "TEST_TYPE" in proposal.title
        assert proposal.occurrence_count == 100
        assert len(proposal.evidence) == 3
        assert proposal.pattern_query is not None
        assert "test_type" in proposal.tags

    def test_create_relationship_type_proposal_structure(self, pattern_detector):
        """Test relationship type proposal has correct structure."""
        proposal = pattern_detector._create_relationship_type_proposal(
            source_type="SOURCE",
            target_type="TARGET",
            count=50
        )

        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.NEW_RELATIONSHIP_TYPE
        assert "SOURCE" in proposal.title
        assert "TARGET" in proposal.title
        assert proposal.occurrence_count == 50
        assert proposal.pattern_query is not None

    def test_proposal_id_format(self, pattern_detector):
        """Test proposal ID follows expected format."""
        proposal = pattern_detector._create_entity_type_proposal(
            type_value="TEST",
            count=10,
            sample_ids=[1]
        )

        assert proposal.proposal_id.startswith("OSS_")
        # Format: OSS_YYYYMMDD_HHMMSS_UUID8
        parts = proposal.proposal_id.split("_")
        assert len(parts) == 4
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 8  # UUID short


class TestPatternDetectorIntegration:
    """Integration-style tests for PatternDetector."""

    @pytest.mark.asyncio
    async def test_full_analysis_cycle(self, pattern_detector, mock_neo4j):
        """Test complete analysis with both entity and relationship patterns."""
        # First call returns entity patterns
        # Second call returns relationship patterns
        mock_neo4j.execute_read.side_effect = [
            [{"type": "PERSON", "count": 100, "sample_ids": [1, 2]}],
            [{"source_type": "PERSON", "target_type": "ORG", "count": 50}],
        ]

        entity_proposals = await pattern_detector.detect_entity_patterns()
        rel_proposals = await pattern_detector.detect_relationship_patterns()

        assert len(entity_proposals) == 1
        assert len(rel_proposals) == 1
        assert entity_proposals[0].change_type == ChangeType.NEW_ENTITY_TYPE
        assert rel_proposals[0].change_type == ChangeType.NEW_RELATIONSHIP_TYPE
