"""Tests for specialised research functions."""

from types import SimpleNamespace

import pytest

from app.services.specialized_functions import (
    FeedSourceAssessment,
    FactCheckFunction,
    TrendAnalysisFunction,
    FactCheckOutput,
    TrendAnalysisOutput,
)


def test_feed_source_assessment_prompt_structure():
    """Ensure the assessment prompt contains expected JSON skeleton."""
    function = FeedSourceAssessment()

    prompt = function.build_prompt(
        domain="example.com",
        include_bias_analysis=True,
        include_publication_patterns=True,
        include_audience_profile=False,
    )

    # Original assertions
    assert "example.com" in prompt
    assert '"credibility_tier": "tier_1|tier_2|tier_3"' in prompt
    assert '"reputation_score": 0-100' in prompt
    assert '"recommendation": {' in prompt

    # NEW: Verify ALL required JSON fields are present in prompt
    assert '"credibility_tier":' in prompt
    assert '"reputation_score":' in prompt
    assert '"founded_year":' in prompt
    assert '"organization_type":' in prompt
    assert '"editorial_standards":' in prompt
    assert '"trust_ratings":' in prompt
    assert '"political_bias":' in prompt
    assert '"recommendation":' in prompt
    assert '"summary":' in prompt

    # NEW: Verify domain appears in the prompt context
    assert prompt.count("example.com") >= 1

    # NEW: Verify JSON-only instruction is present (no markdown allowed)
    assert "ONLY valid JSON" in prompt or "JSON structure" in prompt


@pytest.mark.asyncio
async def test_feed_source_assessment_execute_uses_service(monkeypatch):
    """Verify execute delegates to ResearchService with structured schema."""
    function = FeedSourceAssessment()

    async def fake_create_research_task(*args, **kwargs):
        return SimpleNamespace(
            id=1,
            status="completed",
            result={"content": "ok"},
            structured_data={"credibility_tier": "tier_3"},
            validation_status="valid",
            cost=0.1,
            tokens_used=100,
        )

    monkeypatch.setattr(
        "app.services.research.ResearchService.create_research_task",
        fake_create_research_task,
    )

    result = await function.execute(db=SimpleNamespace(), user_id=1, domain="example.com")

    assert result["function"] == "feed_source_assessment"
    assert result["status"] == "completed"
    assert result["structured_data"]["credibility_tier"] == "tier_3"


def test_fact_check_function_prompt_structure():
    """Ensure the fact-check prompt contains expected JSON skeleton."""
    function = FactCheckFunction()

    prompt = function.build_prompt(
        claim="The moon landing was faked",
        detailed=True,
        include_context=True,
    )

    assert "The moon landing was faked" in prompt
    assert '"verdict":' in prompt
    assert '"confidence": 0-100' in prompt
    assert '"claim_rating":' in prompt
    assert '"supporting_evidence":' in prompt
    assert '"contradicting_evidence":' in prompt


def test_fact_check_output_schema_validation():
    """Verify FactCheckOutput schema validates correctly."""
    valid_data = {
        "verdict": "false",
        "confidence": 95,
        "claim_rating": "false",
        "supporting_evidence": [],
        "contradicting_evidence": [
            {"source": "NASA", "reliability": "high", "summary": "Moon landing happened"}
        ],
        "summary": "Claim is false according to authoritative sources",
    }

    output = FactCheckOutput(**valid_data)
    assert output.verdict == "false"
    assert output.confidence == 95
    assert len(output.contradicting_evidence) == 1


def test_fact_check_function_models():
    """Verify FactCheckFunction uses correct model and depth."""
    function = FactCheckFunction()

    assert function.model == "sonar-reasoning-pro"
    assert function.depth == "deep"
    assert function.output_schema == FactCheckOutput


@pytest.mark.asyncio
async def test_fact_check_function_execute(monkeypatch):
    """Verify fact-check execute delegates correctly."""
    function = FactCheckFunction()

    async def fake_create_research_task(*args, **kwargs):
        return SimpleNamespace(
            id=2,
            status="completed",
            result={"content": "Fact-check complete"},
            structured_data={"verdict": "false", "confidence": 90},
            validation_status="valid",
            cost=0.15,
            tokens_used=200,
        )

    monkeypatch.setattr(
        "app.services.research.ResearchService.create_research_task",
        fake_create_research_task,
    )

    result = await function.execute(
        db=SimpleNamespace(),
        user_id=1,
        claim="Test claim"
    )

    assert result["function"] == "fact_check"
    assert result["status"] == "completed"
    assert result["structured_data"]["verdict"] == "false"


def test_trend_analysis_function_prompt_structure():
    """Ensure the trend analysis prompt contains expected JSON skeleton."""
    function = TrendAnalysisFunction()

    prompt = function.build_prompt(
        topic="AI regulation",
        timeframe="week",
        include_geographic=True,
        include_narratives=True,
    )

    assert "AI regulation" in prompt
    assert '"overall_trend":' in prompt
    assert '"coverage_intensity":' in prompt
    assert '"identified_trends":' in prompt
    assert '"geographic_distribution":' in prompt
    assert '"emerging_narratives":' in prompt


def test_trend_analysis_output_schema_validation():
    """Verify TrendAnalysisOutput schema validates correctly."""
    valid_data = {
        "topic": "Climate change",
        "timeframe": "month",
        "overall_trend": "rising",
        "coverage_intensity": "high",
        "identified_trends": [
            {
                "trend": "COP29 discussions",
                "strength": "growing",
                "coverage_volume": "high",
                "key_sources": ["BBC", "Reuters"]
            }
        ],
        "key_drivers": ["Legislative action", "Scientific reports"],
        "geographic_distribution": [
            {
                "region": "Europe",
                "coverage_level": "high",
                "notable_aspects": "Focus on EU policies"
            }
        ],
        "notable_sources": ["BBC", "Reuters", "NYT"],
        "summary": "Climate coverage is increasing due to COP29",
    }

    output = TrendAnalysisOutput(**valid_data)
    assert output.topic == "Climate change"
    assert output.overall_trend == "rising"
    assert len(output.identified_trends) == 1
    assert output.identified_trends[0].strength == "growing"


def test_trend_analysis_function_models():
    """Verify TrendAnalysisFunction uses correct model and depth."""
    function = TrendAnalysisFunction()

    assert function.model == "sonar-pro"
    assert function.depth == "deep"
    assert function.output_schema == TrendAnalysisOutput


@pytest.mark.asyncio
async def test_trend_analysis_function_execute(monkeypatch):
    """Verify trend analysis execute delegates correctly."""
    function = TrendAnalysisFunction()

    async def fake_create_research_task(*args, **kwargs):
        return SimpleNamespace(
            id=3,
            status="completed",
            result={"content": "Trend analysis complete"},
            structured_data={"overall_trend": "rising", "coverage_intensity": "high"},
            validation_status="valid",
            cost=0.20,
            tokens_used=300,
        )

    monkeypatch.setattr(
        "app.services.research.ResearchService.create_research_task",
        fake_create_research_task,
    )

    result = await function.execute(
        db=SimpleNamespace(),
        user_id=1,
        topic="AI safety"
    )

    assert result["function"] == "trend_analysis"
    assert result["status"] == "completed"
    assert result["structured_data"]["overall_trend"] == "rising"
