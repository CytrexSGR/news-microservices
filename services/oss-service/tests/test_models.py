"""
Unit Tests for Pydantic Models.

Tests model validation and serialization.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.proposal import (
    OntologyChangeProposal,
    AnalysisResult,
    ChangeType,
    Severity,
    Evidence,
    ImpactAnalysis
)


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_all_change_types_defined(self):
        """Test all expected change types exist."""
        expected_types = [
            "NEW_ENTITY_TYPE",
            "NEW_RELATIONSHIP_TYPE",
            "MODIFY_ENTITY_PROPERTIES",
            "MODIFY_RELATIONSHIP_PROPERTIES",
            "FLAG_INCONSISTENCY",
            "SUGGEST_CONSTRAINT",
            "SUGGEST_INDEX",
            "DEPRECATE_ENTITY",
            "DEPRECATE_RELATIONSHIP",
            "MERGE_ENTITIES",
        ]

        for type_name in expected_types:
            assert hasattr(ChangeType, type_name)

    def test_change_type_is_string_enum(self):
        """Test ChangeType values are strings."""
        assert ChangeType.NEW_ENTITY_TYPE.value == "NEW_ENTITY_TYPE"
        assert ChangeType.FLAG_INCONSISTENCY.value == "FLAG_INCONSISTENCY"


class TestSeverity:
    """Tests for Severity enum."""

    def test_all_severities_defined(self):
        """Test all expected severities exist."""
        expected_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for severity in expected_severities:
            assert hasattr(Severity, severity)

    def test_severity_is_string_enum(self):
        """Test Severity values are strings."""
        assert Severity.CRITICAL.value == "CRITICAL"
        assert Severity.LOW.value == "LOW"


class TestEvidence:
    """Tests for Evidence model."""

    def test_evidence_required_fields(self):
        """Test Evidence requires example_id and example_type."""
        evidence = Evidence(
            example_id="12345",
            example_type="NODE"
        )

        assert evidence.example_id == "12345"
        assert evidence.example_type == "NODE"

    def test_evidence_optional_fields(self):
        """Test Evidence optional fields."""
        evidence = Evidence(
            example_id="12345",
            example_type="NODE",
            properties={"name": "Test"},
            context="Test context",
            frequency=100
        )

        assert evidence.properties == {"name": "Test"}
        assert evidence.context == "Test context"
        assert evidence.frequency == 100

    def test_evidence_missing_required_field(self):
        """Test Evidence validation fails without required fields."""
        with pytest.raises(ValidationError):
            Evidence(example_id="12345")  # Missing example_type


class TestImpactAnalysis:
    """Tests for ImpactAnalysis model."""

    def test_impact_analysis_defaults(self):
        """Test ImpactAnalysis default values."""
        impact = ImpactAnalysis()

        assert impact.affected_entities_count is None
        assert impact.affected_relationships_count is None
        assert impact.breaking_change is False
        assert impact.migration_complexity == "LOW"
        assert impact.estimated_effort_hours is None
        assert impact.benefits == []
        assert impact.risks == []

    def test_impact_analysis_all_fields(self):
        """Test ImpactAnalysis with all fields."""
        impact = ImpactAnalysis(
            affected_entities_count=1000,
            affected_relationships_count=500,
            breaking_change=True,
            migration_complexity="HIGH",
            estimated_effort_hours=20.0,
            benefits=["Better performance", "Cleaner data"],
            risks=["Data migration required"]
        )

        assert impact.affected_entities_count == 1000
        assert impact.affected_relationships_count == 500
        assert impact.breaking_change is True
        assert impact.migration_complexity == "HIGH"
        assert impact.estimated_effort_hours == 20.0
        assert len(impact.benefits) == 2
        assert len(impact.risks) == 1


class TestOntologyChangeProposal:
    """Tests for OntologyChangeProposal model."""

    @pytest.fixture
    def valid_proposal_data(self):
        """Valid proposal data for testing."""
        return {
            "proposal_id": "OSS_20251125_120000_abc12345",
            "change_type": ChangeType.NEW_ENTITY_TYPE,
            "severity": Severity.MEDIUM,
            "title": "Test Proposal",
            "description": "Test description for the proposal",
            "confidence": 0.85,
            "impact_analysis": ImpactAnalysis(
                affected_entities_count=100,
                breaking_change=False
            )
        }

    def test_proposal_required_fields(self, valid_proposal_data):
        """Test proposal with required fields only."""
        proposal = OntologyChangeProposal(**valid_proposal_data)

        assert proposal.proposal_id == "OSS_20251125_120000_abc12345"
        assert proposal.change_type == ChangeType.NEW_ENTITY_TYPE
        assert proposal.severity == Severity.MEDIUM
        assert proposal.title == "Test Proposal"
        assert proposal.confidence == 0.85

    def test_proposal_optional_fields(self, valid_proposal_data):
        """Test proposal with optional fields."""
        valid_proposal_data.update({
            "definition": "class NewEntity: pass",
            "pattern_query": "MATCH (n) RETURN n",
            "occurrence_count": 500,
            "tags": ["test", "pattern"]
        })

        proposal = OntologyChangeProposal(**valid_proposal_data)

        assert proposal.definition == "class NewEntity: pass"
        assert proposal.pattern_query == "MATCH (n) RETURN n"
        assert proposal.occurrence_count == 500
        assert proposal.tags == ["test", "pattern"]

    def test_proposal_confidence_validation_min(self, valid_proposal_data):
        """Test confidence cannot be less than 0."""
        valid_proposal_data["confidence"] = -0.1

        with pytest.raises(ValidationError):
            OntologyChangeProposal(**valid_proposal_data)

    def test_proposal_confidence_validation_max(self, valid_proposal_data):
        """Test confidence cannot be greater than 1."""
        valid_proposal_data["confidence"] = 1.1

        with pytest.raises(ValidationError):
            OntologyChangeProposal(**valid_proposal_data)

    def test_proposal_confidence_boundary_values(self, valid_proposal_data):
        """Test confidence boundary values are valid."""
        valid_proposal_data["confidence"] = 0.0
        proposal_min = OntologyChangeProposal(**valid_proposal_data)
        assert proposal_min.confidence == 0.0

        valid_proposal_data["confidence"] = 1.0
        proposal_max = OntologyChangeProposal(**valid_proposal_data)
        assert proposal_max.confidence == 1.0

    def test_proposal_with_evidence(self, valid_proposal_data):
        """Test proposal with evidence list."""
        valid_proposal_data["evidence"] = [
            Evidence(example_id="1", example_type="NODE"),
            Evidence(example_id="2", example_type="NODE", context="Second example")
        ]

        proposal = OntologyChangeProposal(**valid_proposal_data)

        assert len(proposal.evidence) == 2
        assert proposal.evidence[0].example_id == "1"

    def test_proposal_oss_version_default(self, valid_proposal_data):
        """Test default OSS version."""
        proposal = OntologyChangeProposal(**valid_proposal_data)

        assert proposal.oss_version == "1.0.0"

    def test_proposal_missing_required_field(self):
        """Test proposal validation fails without required fields."""
        with pytest.raises(ValidationError):
            OntologyChangeProposal(
                proposal_id="test",
                # Missing other required fields
            )


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_analysis_result_required_fields(self):
        """Test AnalysisResult with required fields."""
        result = AnalysisResult(cycle_id="cycle_test_123")

        assert result.cycle_id == "cycle_test_123"
        assert result.started_at is not None
        assert result.completed_at is None

    def test_analysis_result_defaults(self):
        """Test AnalysisResult default values."""
        result = AnalysisResult(cycle_id="test")

        assert result.patterns_detected == 0
        assert result.inconsistencies_detected == 0
        assert result.proposals_generated == 0
        assert result.proposals_submitted == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.proposals == []

    def test_analysis_result_with_all_fields(self):
        """Test AnalysisResult with all fields populated."""
        now = datetime.now()
        proposal = OntologyChangeProposal(
            proposal_id="test",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test",
            confidence=0.8,
            impact_analysis=ImpactAnalysis()
        )

        result = AnalysisResult(
            cycle_id="cycle_full_test",
            started_at=now,
            completed_at=now,
            patterns_detected=10,
            inconsistencies_detected=5,
            proposals_generated=3,
            proposals_submitted=2,
            errors=["Error 1"],
            warnings=["Warning 1"],
            proposals=[proposal]
        )

        assert result.patterns_detected == 10
        assert result.inconsistencies_detected == 5
        assert result.proposals_generated == 3
        assert result.proposals_submitted == 2
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.proposals) == 1

    def test_analysis_result_started_at_auto_set(self):
        """Test started_at is automatically set."""
        before = datetime.now()
        result = AnalysisResult(cycle_id="test")
        after = datetime.now()

        assert before <= result.started_at <= after
