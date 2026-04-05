"""
Tests for DIA Verifier (Phase 2)

Tests tool execution, parallel processing, and evidence aggregation.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import (
    ProblemHypothesis,
    VerificationRequiredEvent,
    ToolExecutionResult
)
from models.adversarial_test_case import VerificationPlan, ExpectedCorrection

from app.services.dia_verifier import DIAVerifier


@pytest.fixture
def sample_event():
    """Create sample verification event."""
    return VerificationRequiredEvent(
        analysis_result_id=uuid4(),
        article_id=uuid4(),
        article_title="Tesla Reports Q3 Earnings",
        article_content="Tesla announced Q3 2024 earnings of $5 billion...",
        article_url="https://example.com/tesla",
        article_published_at=datetime.utcnow(),
        uq_confidence_score=0.45,
        uncertainty_factors=["Numerical claim lacks verification"],
        priority="high"
    )


@pytest.fixture
def sample_hypothesis():
    """Create sample problem hypothesis."""
    return ProblemHypothesis(
        primary_concern="Financial figure '$5 billion' appears to be incorrect",
        affected_content="Tesla announced Q3 2024 earnings of $5 billion",
        hypothesis_type="factual_error",
        confidence=0.85,
        reasoning="Historical Tesla profits are typically $3-4.5B per quarter",
        verification_approach="Cross-reference with SEC filings and financial databases"
    )


@pytest.fixture
def sample_plan():
    """Create sample verification plan."""
    return VerificationPlan(
        priority="high",
        verification_methods=[
            "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount')",
            "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
        ],
        external_sources=[
            "SEC EDGAR Database",
            "Tesla Investor Relations"
        ],
        expected_corrections=[
            ExpectedCorrection(
                field="earnings",
                original="$5 billion",
                corrected="$4.194 billion",
                confidence_improvement=0.20
            )
        ],
        estimated_verification_time_seconds=60
    )


class TestDIAVerifier:
    """Test suite for DIA Verifier."""

    def test_init(self):
        """Test verifier initialization."""
        verifier = DIAVerifier()

        assert verifier is not None
        assert len(verifier.tool_registry) >= 2  # At least 2 tools
        assert "perplexity_deep_search" in verifier.tool_registry
        assert "financial_data_lookup" in verifier.tool_registry

    def test_parse_verification_methods(self):
        """Test parsing of verification method strings."""
        verifier = DIAVerifier()

        methods = [
            "perplexity_deep_search(query='Tesla earnings')",
            "financial_data_lookup(company='TSLA', metric='earnings')",
            "invalid_tool(param='value')",
            "malformed_method_without_parens"
        ]

        parsed = verifier._parse_verification_methods(methods)

        # Should parse first two, skip last two
        assert len(parsed) == 2

        # Check first parsed method
        tool_name, params = parsed[0]
        assert tool_name == "perplexity_deep_search"
        assert params["query"] == "Tesla earnings"

        # Check second parsed method
        tool_name, params = parsed[1]
        assert tool_name == "financial_data_lookup"
        assert params["company"] == "TSLA"
        assert params["metric"] == "earnings"

    @pytest.mark.asyncio
    async def test_execute_verification_end_to_end(
        self,
        sample_event,
        sample_hypothesis,
        sample_plan
    ):
        """
        Test complete verification workflow (end-to-end).

        Note: This test will make real API calls if keys are configured.
        It's marked as integration test.
        """
        verifier = DIAVerifier()

        # Execute verification
        evidence = await verifier.execute_verification(
            plan=sample_plan,
            hypothesis=sample_hypothesis,
            event=sample_event
        )

        # Verify evidence package structure
        assert evidence is not None
        assert evidence.verification_request_id == sample_event.event_id
        assert evidence.problem_hypothesis == sample_hypothesis
        assert isinstance(evidence.tool_executions, list)
        assert len(evidence.tool_executions) >= 2
        assert evidence.total_execution_time_ms > 0
        assert isinstance(evidence.hypothesis_confirmed, bool)
        assert 0.0 <= evidence.confidence_score <= 1.0
        assert isinstance(evidence.key_findings, list)
        assert isinstance(evidence.corrected_facts, dict)
        assert isinstance(evidence.source_citations, list)

    def test_extract_key_findings(self):
        """Test extraction of key findings from tool results."""
        verifier = DIAVerifier()

        # Mock tool results
        results = [
            ToolExecutionResult(
                tool_name="perplexity_deep_search",
                tool_parameters={"query": "test"},
                success=True,
                execution_time_ms=1000,
                result_data={
                    "answer": "Tesla reported Q3 2024 earnings of $4.194 billion, according to SEC filings."
                },
                source_citations=["https://sec.gov/..."],
                confidence=0.95
            ),
            ToolExecutionResult(
                tool_name="financial_data_lookup",
                tool_parameters={"company": "TSLA"},
                success=True,
                execution_time_ms=800,
                result_data={
                    "company": "TSLA",
                    "metric": "earnings",
                    "data": {
                        "reported_eps": "4.194",
                        "fiscal_date_ending": "2024-09-30"
                    }
                },
                source_citations=["Alpha Vantage"],
                confidence=0.90
            )
        ]

        findings = verifier._extract_key_findings(results)

        assert len(findings) >= 2
        assert any("Perplexity" in f for f in findings)
        assert any("Financial Data" in f for f in findings)

    def test_calculate_overall_confidence(self):
        """Test confidence score calculation."""
        verifier = DIAVerifier()

        # Test case 1: All tools successful with high confidence
        results_high = [
            ToolExecutionResult(
                tool_name="tool1",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.95
            ),
            ToolExecutionResult(
                tool_name="tool2",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.90
            )
        ]

        confidence_high = verifier._calculate_overall_confidence(
            results_high,
            hypothesis_confirmed=True
        )

        assert confidence_high >= 0.85
        assert confidence_high <= 0.95

        # Test case 2: Mixed success
        results_mixed = [
            ToolExecutionResult(
                tool_name="tool1",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.80
            ),
            ToolExecutionResult(
                tool_name="tool2",
                tool_parameters={},
                success=False,
                execution_time_ms=100,
                error_message="Failed",
                source_citations=[],
                confidence=0.0
            )
        ]

        confidence_mixed = verifier._calculate_overall_confidence(
            results_mixed,
            hypothesis_confirmed=False
        )

        assert confidence_mixed < confidence_high
        assert confidence_mixed >= 0.3

    def test_build_source_citations(self):
        """Test building structured source citations."""
        verifier = DIAVerifier()

        citations = [
            "https://sec.gov/filing123",
            "https://reuters.com/article",
            "https://sec.gov/filing123",  # Duplicate
            "https://example.com/blog"
        ]

        source_objects = verifier._build_source_citations(citations)

        # Should deduplicate
        assert len(source_objects) == 3

        # Check reliability categorization
        gov_source = next((s for s in source_objects if ".gov" in s["url"]), None)
        assert gov_source is not None
        assert gov_source["reliability"] == "primary"

        reuters_source = next((s for s in source_objects if "reuters" in s["url"]), None)
        assert reuters_source is not None
        assert reuters_source["reliability"] == "authoritative"

    def test_calculate_source_reliability(self):
        """Test source reliability calculation."""
        verifier = DIAVerifier()

        sources_high = [
            {"reliability": "primary"},
            {"reliability": "primary"}
        ]
        reliability_high = verifier._calculate_source_reliability(sources_high)
        assert reliability_high == 1.0

        sources_mixed = [
            {"reliability": "primary"},
            {"reliability": "authoritative"},
            {"reliability": "secondary"}
        ]
        reliability_mixed = verifier._calculate_source_reliability(sources_mixed)
        assert 0.7 <= reliability_mixed <= 0.9

    def test_calculate_evidence_consistency(self):
        """Test evidence consistency calculation."""
        verifier = DIAVerifier()

        # High consistency (similar confidences)
        results_consistent = [
            ToolExecutionResult(
                tool_name="tool1",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.90
            ),
            ToolExecutionResult(
                tool_name="tool2",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.92
            )
        ]

        consistency_high = verifier._calculate_evidence_consistency(results_consistent)
        assert consistency_high >= 0.95

        # Low consistency (varied confidences)
        results_inconsistent = [
            ToolExecutionResult(
                tool_name="tool1",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.95
            ),
            ToolExecutionResult(
                tool_name="tool2",
                tool_parameters={},
                success=True,
                execution_time_ms=100,
                source_citations=[],
                confidence=0.30
            )
        ]

        consistency_low = verifier._calculate_evidence_consistency(results_inconsistent)
        assert consistency_low < consistency_high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
