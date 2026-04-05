"""
Shared contracts for inter-service communication.

This module provides type-safe Pydantic models that ensure consistent
data structures across service boundaries, particularly for research
task creation and specialized function parameters.

Usage:
    from shared.contracts import ResearchTaskRequest, validate_research_request
"""

from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchTaskRequest(BaseModel):
    """
    Standard contract for creating research tasks across services.

    This ensures feed-service and research-service use identical field names
    and validation logic, preventing silent parameter drops.

    Fields:
        request_id: Unique identifier for distributed tracing (X-Request-ID header)
        query: Research query text
        model_name: Perplexity model (sonar, sonar-pro, sonar-reasoning-pro)
        depth: Search depth (standard, deep)
        feed_id: UUID of associated feed (optional)
        legacy_feed_id: Integer feed ID for backward compatibility (optional)
        article_id: UUID of associated article (optional)
        legacy_article_id: Integer article ID for backward compatibility (optional)
        research_function: Name of specialized function (feed_source_assessment, fact_check, trend_analysis)
        function_parameters: Parameters for specialized function (domain, claim, topic, etc.)
    """
    model_config = ConfigDict(protected_namespaces=())

    request_id: Optional[str] = Field(
        default=None,
        description="Unique request ID for tracing across services (optional - can be in X-Request-ID header)",
        min_length=36,
        max_length=36
    )

    query: str = Field(
        ...,
        description="Research query text",
        min_length=1,
        max_length=5000
    )

    model_name: Optional[str] = Field(
        default="sonar",
        description="Perplexity model to use"
    )

    depth: Optional[str] = Field(
        default="standard",
        description="Search depth level",
        pattern="^(standard|deep)$"
    )

    feed_id: Optional[UUID] = Field(
        default=None,
        description="UUID of associated feed"
    )

    legacy_feed_id: Optional[int] = Field(
        default=None,
        description="Integer feed ID for backward compatibility"
    )

    article_id: Optional[UUID] = Field(
        default=None,
        description="UUID of associated article"
    )

    legacy_article_id: Optional[int] = Field(
        default=None,
        description="Integer article ID for backward compatibility"
    )

    research_function: Optional[str] = Field(
        default=None,
        description="Name of specialized research function",
        pattern="^(feed_source_assessment|fact_check|trend_analysis)?$"
    )

    function_parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for specialized function"
    )

    @model_validator(mode='after')
    def validate_research_params(self):
        """
        GUARDRAIL: Validate research_function and function_parameters together.

        This prevents silent failures by ensuring:
        1. If function_parameters is provided, research_function must also be provided
        2. If research_function is provided, function_parameters must also be provided

        Root cause from incident 2025-10-18-20: function_parameters were dropped silently
        because research_function was missing, causing build_prompt() to fail with
        "missing 1 required positional argument: 'domain'".

        See: /home/cytrex/news-microservices/docs/incidents/2025-10-18-20-feed-assessment-implementation-lessons-learned.md
        """
        has_function = self.research_function is not None
        has_params = self.function_parameters is not None

        # Case 1: Parameters without function name
        if has_params and not has_function:
            raise ValueError(
                "function_parameters provided but research_function is missing. "
                "This indicates a specialized function is intended but not specified. "
                "Valid values: feed_source_assessment, fact_check, trend_analysis"
            )

        # Case 2: Function name without parameters
        if has_function and not has_params:
            raise ValueError(
                f"research_function '{self.research_function}' specified but function_parameters is missing. "
                f"Specialized functions require parameters to execute."
            )

        return self


class FeedSourceAssessmentParams(BaseModel):
    """
    Type-safe parameters for feed_source_assessment function.

    This prevents build_prompt() failures by ensuring all required
    parameters are present before the research task is created.

    Fields:
        domain: Domain name to assess (e.g., "www.bbc.com")
        feed_url: Full feed URL (optional, for additional context)
        feed_name: Human-readable feed name (optional, for prompts)
        include_bias_analysis: Include political bias analysis (default: True)
        include_publication_patterns: Include publication frequency/patterns (default: True)
        include_audience_profile: Include audience demographics (default: False)
    """

    domain: str = Field(
        ...,
        description="Domain name to assess (e.g., 'www.bbc.com')",
        min_length=3,
        max_length=255
    )

    feed_url: Optional[str] = Field(
        default=None,
        description="Full feed URL for additional context"
    )

    feed_name: Optional[str] = Field(
        default=None,
        description="Human-readable feed name"
    )

    include_bias_analysis: bool = Field(
        default=True,
        description="Include political bias analysis from Media Bias/Fact Check"
    )

    include_publication_patterns: bool = Field(
        default=True,
        description="Include publication frequency and content type patterns"
    )

    include_audience_profile: bool = Field(
        default=False,
        description="Include audience demographics (slower)"
    )


class FactCheckParams(BaseModel):
    """
    Type-safe parameters for fact_check function.

    Fields:
        claim: Claim to fact-check
        detailed: Include detailed evidence breakdown (default: True)
        include_context: Include important context/nuance (default: True)
    """

    claim: str = Field(
        ...,
        description="Claim to fact-check",
        min_length=10,
        max_length=2000
    )

    detailed: bool = Field(
        default=True,
        description="Include detailed evidence breakdown"
    )

    include_context: bool = Field(
        default=True,
        description="Include important context and nuance"
    )


class TrendAnalysisParams(BaseModel):
    """
    Type-safe parameters for trend_analysis function.

    Fields:
        topic: Topic to analyze
        timeframe: Analysis period (day, week, month, year)
        include_geographic: Include geographic distribution (default: True)
        include_narratives: Include emerging narrative angles (default: True)
    """

    topic: str = Field(
        ...,
        description="Topic to analyze trends for",
        min_length=3,
        max_length=500
    )

    timeframe: str = Field(
        default="month",
        description="Analysis period",
        pattern="^(day|week|month|year)$"
    )

    include_geographic: bool = Field(
        default=True,
        description="Include geographic distribution of coverage"
    )

    include_narratives: bool = Field(
        default=True,
        description="Include emerging narrative angles"
    )


def validate_research_request(request_data: dict) -> ResearchTaskRequest:
    """
    Validate and parse research task request data.

    This function provides fail-fast validation at service boundaries,
    catching contract violations before they propagate into the system.

    Args:
        request_data: Raw request data dictionary

    Returns:
        Validated ResearchTaskRequest instance

    Raises:
        ValueError: If validation fails (caught by FastAPI as 422)

    Example:
        >>> from shared.contracts import validate_research_request
        >>>
        >>> validated = validate_research_request({
        ...     "request_id": "12345678-1234-1234-1234-123456789012",
        ...     "query": "Assess BBC credibility",
        ...     "research_function": "feed_source_assessment",
        ...     "function_parameters": {
        ...         "domain": "www.bbc.com",
        ...         "feed_url": "https://feeds.bbci.co.uk/news/rss.xml",
        ...         "feed_name": "BBC News"
        ...     }
        ... })
        >>> print(validated.research_function)
        'feed_source_assessment'
    """
    return ResearchTaskRequest(**request_data)


def build_assessment_request(
    feed_id: UUID,
    domain: str,
    feed_url: str,
    feed_name: str,
    request_id: Optional[str] = None,
    query: Optional[str] = None
) -> ResearchTaskRequest:
    """
    Builder function for feed assessment requests.

    This convenience function constructs a properly validated assessment
    request, ensuring all required fields are present and correctly typed.

    Args:
        feed_id: UUID of feed to assess
        domain: Domain name extracted from feed URL
        feed_url: Full feed URL
        feed_name: Human-readable feed name
        request_id: Optional request ID for tracing (usually sent in X-Request-ID header)
        query: Optional custom query (auto-generated if not provided)

    Returns:
        Validated ResearchTaskRequest ready to send to research-service

    Example:
        >>> from shared.contracts import build_assessment_request
        >>> from uuid import UUID
        >>>
        >>> request = build_assessment_request(
        ...     feed_id=UUID("bba49986-e780-4c8f-b8ca-d8f258bc42ad"),
        ...     domain="www.middleeasteye.net",
        ...     feed_url="https://www.middleeasteye.net/rss",
        ...     feed_name="Middle East Eye"
        ... )
        >>> print(request.research_function)
        'feed_source_assessment'
    """
    if query is None:
        query = f"Assess the credibility and reliability of {feed_name} news source"

    return ResearchTaskRequest(
        request_id=request_id,
        query=query,
        model_name="sonar",
        depth="standard",
        feed_id=feed_id,
        research_function="feed_source_assessment",
        function_parameters=FeedSourceAssessmentParams(
            domain=domain,
            feed_url=feed_url,
            feed_name=feed_name
        ).dict()
    )
