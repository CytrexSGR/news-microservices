"""
Unit Tests for InconsistencyDetector.

Tests data quality issue detection with mock Neo4j data.
"""
import pytest
from unittest.mock import MagicMock

from app.analyzers.inconsistency_detector import InconsistencyDetector
from app.models.proposal import ChangeType, Severity
from tests.conftest import assert_valid_proposal, assert_proposal_count


class TestInconsistencyDetector:
    """Tests for InconsistencyDetector class."""

    # ========================================================================
    # ISO Code Violation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_iso_code_violations_with_results(
        self, inconsistency_detector, mock_neo4j, iso_violation_data
    ):
        """Test ISO code violation detection with valid data."""
        mock_neo4j.execute_read.return_value = iso_violation_data

        proposals = await inconsistency_detector.detect_iso_code_violations()

        assert_proposal_count(proposals, 1)
        proposal = proposals[0]
        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.FLAG_INCONSISTENCY
        assert proposal.severity == Severity.CRITICAL
        assert proposal.confidence == 1.0

    @pytest.mark.asyncio
    async def test_detect_iso_code_violations_empty_results(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test ISO code violation detection with no results."""
        mock_neo4j.execute_read.return_value = []

        proposals = await inconsistency_detector.detect_iso_code_violations()

        assert_proposal_count(proposals, 0)

    @pytest.mark.asyncio
    async def test_iso_code_violation_database_error(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test graceful handling of database errors."""
        mock_neo4j.execute_read.side_effect = Exception("Neo4j timeout")

        proposals = await inconsistency_detector.detect_iso_code_violations()

        assert_proposal_count(proposals, 0)

    # ========================================================================
    # Duplicate Entity Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_duplicate_entities_with_results(
        self, inconsistency_detector, mock_neo4j, duplicate_entity_data
    ):
        """Test duplicate entity detection with valid data."""
        mock_neo4j.execute_read.return_value = duplicate_entity_data

        proposals = await inconsistency_detector.detect_duplicate_entities()

        assert_proposal_count(proposals, 2)
        for proposal in proposals:
            assert_valid_proposal(proposal)
            assert proposal.change_type == ChangeType.FLAG_INCONSISTENCY
            assert proposal.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_duplicate_entities_empty_results(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test duplicate entity detection with no results."""
        mock_neo4j.execute_read.return_value = []

        proposals = await inconsistency_detector.detect_duplicate_entities()

        assert_proposal_count(proposals, 0)

    @pytest.mark.asyncio
    async def test_duplicate_entity_proposal_content(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test duplicate entity proposal contains correct data."""
        mock_neo4j.execute_read.return_value = [
            {"id": "TEST_ID", "duplicate_count": 5, "sample_node_ids": [1, 2, 3, 4, 5]}
        ]

        proposals = await inconsistency_detector.detect_duplicate_entities()

        assert_proposal_count(proposals, 1)
        proposal = proposals[0]
        assert "TEST_ID" in proposal.title
        assert proposal.occurrence_count == 5
        assert len(proposal.evidence) == 3  # Max 3 evidence items

    # ========================================================================
    # Missing Properties Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_missing_properties_with_results(
        self, inconsistency_detector, mock_neo4j, missing_properties_data
    ):
        """Test missing properties detection with valid data."""
        mock_neo4j.execute_read.return_value = missing_properties_data

        proposals = await inconsistency_detector.detect_missing_required_properties()

        assert_proposal_count(proposals, 1)
        proposal = proposals[0]
        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.FLAG_INCONSISTENCY
        assert proposal.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_missing_properties_filters_low_quality(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test that low-quality entity names are filtered out."""
        mock_neo4j.execute_read.return_value = [
            {"node_id": 1, "labels": ["Entity"], "entity_id": None, "entity_type": "PERSON", "name": "Article 123"},
            {"node_id": 2, "labels": ["Entity"], "entity_id": None, "entity_type": "ORG", "name": "Valid Name"},
            {"node_id": 3, "labels": ["Entity"], "entity_id": None, "entity_type": "PERSON", "name": "masterarbeit"},
        ]

        proposals = await inconsistency_detector.detect_missing_required_properties()

        # Only "Valid Name" should pass filtering
        assert_proposal_count(proposals, 1)

    @pytest.mark.asyncio
    async def test_detect_missing_properties_empty_after_filter(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test that no proposal is created if all entities are filtered out."""
        mock_neo4j.execute_read.return_value = [
            {"node_id": 1, "labels": ["Entity"], "entity_id": None, "entity_type": "PERSON", "name": "bullish"},
            {"node_id": 2, "labels": ["Entity"], "entity_id": None, "entity_type": "ORG", "name": "ab"},  # Too short
        ]

        proposals = await inconsistency_detector.detect_missing_required_properties()

        assert_proposal_count(proposals, 0)

    # ========================================================================
    # UNKNOWN Entity Type Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_unknown_entity_types_with_results(
        self, inconsistency_detector, mock_neo4j, unknown_entity_data
    ):
        """Test UNKNOWN entity type detection with valid data."""
        mock_neo4j.execute_read.return_value = unknown_entity_data

        proposals = await inconsistency_detector.detect_unknown_entity_types()

        assert_proposal_count(proposals, 1)
        proposal = proposals[0]
        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.FLAG_INCONSISTENCY
        assert proposal.severity == Severity.CRITICAL
        assert proposal.occurrence_count == 38000

    @pytest.mark.asyncio
    async def test_detect_unknown_entity_types_zero_count(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test UNKNOWN entity type detection with zero count."""
        mock_neo4j.execute_read.return_value = [{"unknown_count": 0, "sample_ids": []}]

        proposals = await inconsistency_detector.detect_unknown_entity_types()

        assert_proposal_count(proposals, 0)

    @pytest.mark.asyncio
    async def test_detect_unknown_entity_types_empty_results(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test UNKNOWN entity type detection with empty results."""
        mock_neo4j.execute_read.return_value = []

        proposals = await inconsistency_detector.detect_unknown_entity_types()

        assert_proposal_count(proposals, 0)

    # ========================================================================
    # ARTICLE Entity Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_article_entities_with_results(
        self, inconsistency_detector, mock_neo4j, article_entity_data
    ):
        """Test ARTICLE entity detection with valid data."""
        mock_neo4j.execute_read.return_value = article_entity_data

        proposals = await inconsistency_detector.detect_article_entities()

        assert_proposal_count(proposals, 1)
        proposal = proposals[0]
        assert_valid_proposal(proposal)
        assert proposal.change_type == ChangeType.FLAG_INCONSISTENCY
        assert proposal.severity == Severity.HIGH
        assert proposal.occurrence_count == 500

    @pytest.mark.asyncio
    async def test_detect_article_entities_zero_count(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test ARTICLE entity detection with zero count."""
        mock_neo4j.execute_read.return_value = [
            {"article_count": 0, "sample_ids": [], "sample_names": []}
        ]

        proposals = await inconsistency_detector.detect_article_entities()

        assert_proposal_count(proposals, 0)

    # ========================================================================
    # Low Quality Entity Name Filter Tests
    # ========================================================================

    def test_is_low_quality_entity_name_empty(self, inconsistency_detector):
        """Test empty name is low quality."""
        assert inconsistency_detector._is_low_quality_entity_name("") is True
        assert inconsistency_detector._is_low_quality_entity_name(None) is True

    def test_is_low_quality_entity_name_short(self, inconsistency_detector):
        """Test short names are low quality."""
        assert inconsistency_detector._is_low_quality_entity_name("ab") is True
        assert inconsistency_detector._is_low_quality_entity_name("a") is True

    def test_is_low_quality_entity_name_generic_terms(self, inconsistency_detector):
        """Test generic terms are low quality."""
        generic_terms = ["article", "masterarbeit", "bullish", "bearish", "news", "update"]
        for term in generic_terms:
            assert inconsistency_detector._is_low_quality_entity_name(term) is True
            assert inconsistency_detector._is_low_quality_entity_name(f"The {term}") is True

    def test_is_low_quality_entity_name_generic_endings(self, inconsistency_detector):
        """Test generic endings are low quality."""
        assert inconsistency_detector._is_low_quality_entity_name("foreign allies") is True
        assert inconsistency_detector._is_low_quality_entity_name("military forces") is True
        assert inconsistency_detector._is_low_quality_entity_name("drone troops") is True

    def test_is_low_quality_entity_name_uuid_pattern(self, inconsistency_detector):
        """Test UUID-like strings are low quality."""
        uuid_like = "550e8400-e29b-41d4-a716-446655440000"
        assert inconsistency_detector._is_low_quality_entity_name(uuid_like) is True
        assert inconsistency_detector._is_low_quality_entity_name("contains uuid here") is True

    def test_is_low_quality_entity_name_very_long(self, inconsistency_detector):
        """Test very long names are low quality."""
        long_name = "a" * 200
        assert inconsistency_detector._is_low_quality_entity_name(long_name) is True

    def test_is_low_quality_entity_name_numbers_only(self, inconsistency_detector):
        """Test number-only names are low quality."""
        assert inconsistency_detector._is_low_quality_entity_name("12345") is True
        assert inconsistency_detector._is_low_quality_entity_name("2024-01-15") is True

    def test_is_low_quality_entity_name_valid(self, inconsistency_detector):
        """Test valid names pass filter."""
        valid_names = [
            "Apple Inc.",
            "Elon Musk",
            "Microsoft Corporation",
            "New York City",
            "Federal Reserve",
        ]
        for name in valid_names:
            assert inconsistency_detector._is_low_quality_entity_name(name) is False


class TestInconsistencyDetectorIntegration:
    """Integration-style tests for InconsistencyDetector."""

    @pytest.mark.asyncio
    async def test_full_inconsistency_analysis(
        self, inconsistency_detector, mock_neo4j,
        iso_violation_data, duplicate_entity_data
    ):
        """Test running all inconsistency detections."""
        # Configure mock to return different data for each call
        mock_neo4j.execute_read.side_effect = [
            iso_violation_data,  # ISO violations
            duplicate_entity_data,  # Duplicates
            [],  # Missing properties
            [],  # Unknown entities
            [],  # Article entities
        ]

        iso_proposals = await inconsistency_detector.detect_iso_code_violations()
        dup_proposals = await inconsistency_detector.detect_duplicate_entities()
        missing_proposals = await inconsistency_detector.detect_missing_required_properties()
        unknown_proposals = await inconsistency_detector.detect_unknown_entity_types()
        article_proposals = await inconsistency_detector.detect_article_entities()

        total = len(iso_proposals) + len(dup_proposals) + len(missing_proposals) + len(unknown_proposals) + len(article_proposals)

        assert len(iso_proposals) == 1
        assert len(dup_proposals) == 2
        assert len(missing_proposals) == 0
        assert len(unknown_proposals) == 0
        assert len(article_proposals) == 0
        assert total == 3

    @pytest.mark.asyncio
    async def test_all_detectors_handle_errors_gracefully(
        self, inconsistency_detector, mock_neo4j
    ):
        """Test all detection methods handle errors gracefully."""
        mock_neo4j.execute_read.side_effect = Exception("Database unavailable")

        # All should return empty lists, not raise exceptions
        iso = await inconsistency_detector.detect_iso_code_violations()
        dup = await inconsistency_detector.detect_duplicate_entities()
        missing = await inconsistency_detector.detect_missing_required_properties()
        unknown = await inconsistency_detector.detect_unknown_entity_types()
        article = await inconsistency_detector.detect_article_entities()

        assert iso == []
        assert dup == []
        assert missing == []
        assert unknown == []
        assert article == []
