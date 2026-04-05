"""
Specialized research functions that produce structured output.
"""

from typing import Any, Dict, Optional, Type, Union
from pydantic import BaseModel, Field, validator

from app.services.research import ResearchFunction


class TrustRatings(BaseModel):
    """Trust ratings from various sources."""
    media_bias_fact_check: Optional[str] = None
    allsides_rating: Optional[str] = None
    newsguard_score: Optional[Union[int, str]] = None  # Can be int score or string status


class FeedSourceAssessmentOutput(BaseModel):
    """
    Structured output for feed source credibility assessment.
    """

    credibility_tier: str = Field(..., pattern="^(tier_1|tier_2|tier_3)$")
    reputation_score: int = Field(..., ge=0, le=100)
    founded_year: Optional[int] = Field(
        default=None, description="Approximate year when the organisation was founded"
    )
    organization_type: str = Field(
        ...,
        description="Organisation type e.g. digital_native|traditional_media|news_agency|blog|unknown",
    )
    category: str = Field(
        ...,
        description="Primary feed category from fixed set: General News|Finance & Markets|Tech & Science|Geopolitics & Security|Energy & Industry|Regional / Local|Think Tanks / Analysis|Special Interest",
    )
    editorial_standards: Dict[str, str]
    trust_ratings: Union[TrustRatings, Dict[str, Any]]  # Flexible: schema or dict
    political_bias: str = Field(
        ...,
        description="Political leaning e.g. left|center_left|center|center_right|right|unknown",
    )
    recommendation: Dict[str, Any]
    summary: str = Field(..., description="Short narrative summary of the assessment")

    @validator("founded_year")
    def _validate_year(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 1600 or value > 2100:
            raise ValueError("founded_year must be a realistic year")
        return value


class FeedSourceAssessment(ResearchFunction):
    """Assess credibility and reputation of a news source."""

    def __init__(self) -> None:
        super().__init__(
            name="feed_source_assessment",
            description="Assess credibility, bias and reputation of news sources",
            model="sonar",
            depth="standard",
            output_schema=FeedSourceAssessmentOutput,
        )

    def build_prompt(self, domain: str, **kwargs: Any) -> str:
        """Build prompt instructing Perplexity to answer using a JSON schema."""
        include_bias = kwargs.get("include_bias_analysis", True)
        include_patterns = kwargs.get("include_publication_patterns", True)
        include_audience = kwargs.get("include_audience_profile", False)

        prompt = f"""Analyze the news source at domain: {domain}

IMPORTANT: Your response must be ONLY valid JSON with no additional text, markdown, or explanations.

Return the assessment in this EXACT JSON structure:

{{
  "credibility_tier": "tier_1|tier_2|tier_3",
  "reputation_score": 0-100,
  "founded_year": year or null,
  "organization_type": "digital_native|traditional_media|news_agency|blog|unknown",
  "category": "General News|Finance & Markets|Tech & Science|Geopolitics & Security|Energy & Industry|Regional / Local|Think Tanks / Analysis|Special Interest",
  "editorial_standards": {{
    "fact_checking_level": "high|medium|low|unknown",
    "corrections_policy": "transparent|moderate|minimal|unknown",
    "source_attribution": "good|fair|poor|unknown"
  }},
  "trust_ratings": {{
    "media_bias_fact_check": "rating or unknown",
    "allsides_rating": "rating or unknown",
    "newsguard_score": score or null
  }},
  "political_bias": "left|center_left|center|center_right|right|unknown",
  "recommendation": {{
    "skip_waiting_period": true|false,
    "initial_quality_boost": 0-20,
    "bot_detection_threshold": "strict|normal|lenient"
  }},
  "summary": "Brief assessment summary"
}}

Category definitions:
- General News: Broad general news coverage (e.g. BBC, Reuters, CNN, Aljazeera)
- Finance & Markets: Stock markets, economics, commodities, currencies (e.g. Bloomberg, Financial Times)
- Tech & Science: Technology, research, innovation (e.g. TechCrunch, Wired, Ars Technica)
- Geopolitics & Security: International politics, military, conflicts (e.g. Defense News, Foreign Affairs)
- Energy & Industry: Energy, commodities, infrastructure (e.g. OilPrice, industry publications)
- Regional / Local: Country-specific or continental focus (e.g. ABC Australia, Euronews)
- Think Tanks / Analysis: Institutes, studies, strategic analysis (e.g. Brookings, RAND)
- Special Interest: Specialized topics like environment, AI, media (e.g. MIT Tech Review, Nature)

Choose the SINGLE most appropriate category based on the source's primary focus."""

        if include_bias:
            prompt += "\nInclude bias analysis from Media Bias/Fact Check and AllSides if available."

        if include_patterns:
            prompt += "\nDescribe typical publication patterns such as frequency and content types."

        if include_audience:
            prompt += "\nAdd key audience segments if credible information is available."

        prompt += "\n\nAlways cite authoritative references and keep statements factual."
        prompt += "\n\nREMINDER: Output ONLY the JSON object, no markdown, no explanations, no extra text."

        return prompt


class EvidenceSource(BaseModel):
    """Single evidence source for fact-checking."""
    source: str = Field(..., description="Source name or URL")
    reliability: str = Field(..., description="high|medium|low")
    summary: str = Field(..., description="Brief summary of what this source says")


class FactCheckOutput(BaseModel):
    """
    Structured output for fact-checking claims.
    """

    verdict: str = Field(
        ...,
        pattern="^(true|mostly_true|mixed|mostly_false|false|unverifiable)$",
        description="Overall verdict on the claim",
    )
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    claim_rating: str = Field(
        ...,
        description="Rating category: accurate|misleading|false|unverified",
    )
    supporting_evidence: list[Union[EvidenceSource, Dict[str, Any]]] = Field(
        default_factory=list, description="Evidence supporting the claim"
    )
    contradicting_evidence: list[Union[EvidenceSource, Dict[str, Any]]] = Field(
        default_factory=list, description="Evidence contradicting the claim"
    )
    context: Optional[str] = Field(
        default=None, description="Important context or nuance"
    )
    fact_checker_assessments: Optional[Dict[str, str]] = Field(
        default=None,
        description="Assessments from professional fact-checkers (Snopes, FactCheck.org, etc.)",
    )
    summary: str = Field(..., description="Clear summary of the fact-check result")


class FactCheckFunction(ResearchFunction):
    """Fact-check claims using multiple sources."""

    def __init__(self) -> None:
        super().__init__(
            name="fact_check",
            description="Fact-check claims with evidence and citations",
            model="sonar-reasoning-pro",
            depth="deep",
            output_schema=FactCheckOutput,
        )

    def build_prompt(self, claim: str, **kwargs: Any) -> str:
        """Build prompt instructing Perplexity to fact-check with JSON structure."""
        detailed = kwargs.get("detailed", True)
        include_context = kwargs.get("include_context", True)

        prompt = f"""Fact-check the following claim using authoritative sources:

Claim: "{claim}"

Provide your fact-check analysis in the following JSON structure:

{{
  "verdict": "true|mostly_true|mixed|mostly_false|false|unverifiable",
  "confidence": 0-100,
  "claim_rating": "accurate|misleading|false|unverified",
  "supporting_evidence": [
    {{
      "source": "Source name or URL",
      "reliability": "high|medium|low",
      "summary": "What this source says"
    }}
  ],
  "contradicting_evidence": [
    {{
      "source": "Source name or URL",
      "reliability": "high|medium|low",
      "summary": "What this source says"
    }}
  ],
  "context": "Important context or nuance if needed",
  "fact_checker_assessments": {{
    "snopes": "rating if available",
    "factcheck_org": "rating if available",
    "politifact": "rating if available"
  }},
  "summary": "Clear summary of the fact-check result"
}}"""

        if detailed:
            prompt += "\n\nInclude detailed evidence from multiple high-quality sources."
            prompt += "\nDistinguish between supporting and contradicting evidence clearly."

        if include_context:
            prompt += "\nProvide important context that might affect the verdict."

        prompt += "\n\nAlways cite authoritative sources and be precise about confidence levels."

        return prompt


class TrendItem(BaseModel):
    """Single trend identified in news coverage."""
    trend: str = Field(..., description="Brief description of the trend")
    strength: str = Field(..., pattern="^(emerging|growing|strong|declining)$")
    coverage_volume: str = Field(..., description="high|medium|low")
    key_sources: list[str] = Field(
        default_factory=list, description="Notable sources covering this trend"
    )


class GeographicDistribution(BaseModel):
    """Geographic breakdown of trend coverage."""
    region: str = Field(..., description="Geographic region name")
    coverage_level: str = Field(..., description="high|medium|low")
    notable_aspects: Optional[str] = Field(
        default=None, description="Regional variations or unique angles"
    )


class TrendAnalysisOutput(BaseModel):
    """
    Structured output for trend analysis in news coverage.
    """

    topic: str = Field(..., description="Topic being analyzed")
    timeframe: str = Field(..., description="Analysis timeframe")
    overall_trend: str = Field(
        ..., description="Overall trend direction: rising|stable|declining|mixed"
    )
    coverage_intensity: str = Field(..., description="high|medium|low")
    identified_trends: list[Union[TrendItem, Dict[str, Any]]] = Field(
        default_factory=list, description="Specific trends identified"
    )
    key_drivers: list[str] = Field(
        default_factory=list, description="Main drivers influencing coverage"
    )
    geographic_distribution: list[Union[GeographicDistribution, Dict[str, Any]]] = Field(
        default_factory=list, description="Geographic breakdown of coverage"
    )
    timeline_highlights: Optional[Dict[str, str]] = Field(
        default=None, description="Key events or shifts in the timeline"
    )
    notable_sources: list[str] = Field(
        default_factory=list,
        description="Major news outlets covering this topic prominently",
    )
    emerging_narratives: Optional[list[str]] = Field(
        default=None, description="New narrative angles emerging in coverage"
    )
    summary: str = Field(..., description="Executive summary of trend analysis")


class TrendAnalysisFunction(ResearchFunction):
    """Analyze trends in news coverage."""

    def __init__(self) -> None:
        super().__init__(
            name="trend_analysis",
            description="Analyze emerging trends across news sources",
            model="sonar-pro",
            depth="deep",
            output_schema=TrendAnalysisOutput,
        )

    def build_prompt(self, topic: str, timeframe: str = "month", **kwargs: Any) -> str:
        """Build prompt instructing Perplexity to analyze trends with JSON structure."""
        include_geographic = kwargs.get("include_geographic", True)
        include_narratives = kwargs.get("include_narratives", True)

        prompt = f"""Analyze news coverage trends for the following topic:

Topic: "{topic}"
Timeframe: Last {timeframe}

Provide your trend analysis in the following JSON structure:

{{
  "topic": "{topic}",
  "timeframe": "{timeframe}",
  "overall_trend": "rising|stable|declining|mixed",
  "coverage_intensity": "high|medium|low",
  "identified_trends": [
    {{
      "trend": "Brief description of trend",
      "strength": "emerging|growing|strong|declining",
      "coverage_volume": "high|medium|low",
      "key_sources": ["Source 1", "Source 2"]
    }}
  ],
  "key_drivers": [
    "Main driver 1",
    "Main driver 2"
  ],
  "geographic_distribution": [
    {{
      "region": "Region name",
      "coverage_level": "high|medium|low",
      "notable_aspects": "Regional variations"
    }}
  ],
  "timeline_highlights": {{
    "date or period": "Key event or shift"
  }},
  "notable_sources": [
    "Major outlet 1",
    "Major outlet 2"
  ],
  "emerging_narratives": [
    "New narrative angle 1",
    "New narrative angle 2"
  ],
  "summary": "Executive summary of trend analysis"
}}"""

        if include_geographic:
            prompt += "\n\nInclude geographic distribution showing regional variations in coverage."

        if include_narratives:
            prompt += "\nIdentify emerging narrative angles and shifts in framing."

        prompt += "\n\nBase analysis on recent news coverage and cite authoritative sources."

        return prompt


# Mapping export convenience
SPECIALIZED_FUNCTIONS: Dict[str, Type[ResearchFunction]] = {
    "feed_source_assessment": FeedSourceAssessment,
    "fact_check": FactCheckFunction,
    "trend_analysis": TrendAnalysisFunction,
}

