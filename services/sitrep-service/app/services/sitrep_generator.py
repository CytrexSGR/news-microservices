# services/sitrep-service/app/services/sitrep_generator.py
"""SITREP generation using LLM.

Generates structured intelligence briefings (SITREP - Situation Reports)
from aggregated news clusters using OpenAI GPT-4.

Features:
- Structured prompt template for intelligence briefings
- Executive summary generation
- Key developments with risk assessment
- Entity extraction and sentiment analysis
- Token management and cost tracking
- Error handling with circuit breaker pattern

Example:
    >>> generator = SitrepGenerator()
    >>> sitrep = await generator.generate(stories, report_type="daily")
    >>> print(sitrep.executive_summary)
"""

import json
import logging
import time
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from app.config import settings
from app.schemas.story import TopStory
from app.schemas.sitrep import (
    SitrepResponse,
    KeyDevelopment,
    RiskAssessment,
)

logger = logging.getLogger(__name__)


class SitrepGenerationError(Exception):
    """Exception raised when SITREP generation fails."""

    pass


class SitrepGenerator:
    """
    Generates SITREP reports using LLM.

    Creates structured intelligence briefings from aggregated
    cluster data using OpenAI GPT-4. Handles prompt construction,
    API calls, response parsing, and error handling.

    Attributes:
        SYSTEM_PROMPT: System prompt defining the AI analyst role
        STRUCTURED_OUTPUT_PROMPT: Instructions for JSON output format
        MAX_RETRIES: Maximum retry attempts for API failures

    Example:
        >>> generator = SitrepGenerator()
        >>> stories = await aggregator.get_top_stories(limit=10)
        >>> sitrep = await generator.generate(stories, report_type="daily")
    """

    SYSTEM_PROMPT = """You are a senior intelligence analyst creating a daily situation report (SITREP).
Your role is to synthesize news clusters into a concise, actionable briefing for decision-makers.

Key Principles:
- Be objective and factual - avoid speculation
- Prioritize actionable intelligence over narrative
- Identify risks and emerging patterns
- Use clear, professional language
- Quantify impacts where possible

Format Requirements:
- Executive Summary: 2-3 sentences capturing the most critical developments
- Key Developments: Major stories with significance and risk assessment
- Sentiment Analysis: Overall tone and distribution across stories
- Emerging Signals: Patterns or trends that may warrant monitoring

Risk Assessment Levels:
- CRITICAL: Immediate action required, severe impact expected
- HIGH: Significant impact, close monitoring needed
- MEDIUM: Moderate impact, situational awareness recommended
- LOW: Minor impact, routine monitoring sufficient"""

    STRUCTURED_OUTPUT_PROMPT = """Respond with a JSON object containing your analysis.
The JSON must have these fields:
{
    "executive_summary": "2-3 sentence high-level summary",
    "key_developments": [
        {
            "title": "Development headline",
            "summary": "Brief summary",
            "significance": "Why this matters",
            "risk_level": "low|medium|high|critical",
            "risk_category": "geopolitical|economic|security|operational",
            "related_entities": ["Entity1", "Entity2"]
        }
    ],
    "sentiment_analysis": {
        "overall": "positive|negative|neutral|mixed",
        "positive_percent": 0.0,
        "negative_percent": 0.0,
        "neutral_percent": 0.0,
        "rationale": "Brief explanation"
    },
    "emerging_signals": [
        {
            "signal_type": "trend|pattern|anomaly|risk",
            "description": "What was detected",
            "confidence": 0.0,
            "related_entities": ["Entity1"]
        }
    ],
    "content_markdown": "# Full report in Markdown format\\n\\n## Executive Summary\\n..."
}

CRITICAL: Return ONLY valid JSON. No markdown formatting, no code fences, no explanations outside the JSON."""

    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1.0  # Base delay for exponential backoff

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SITREP generator.

        Args:
            api_key: OpenAI API key (uses settings.OPENAI_API_KEY if not provided)
        """
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._client: Optional[AsyncOpenAI] = None

        if not self._api_key:
            logger.warning(
                "OpenAI API key not configured. SITREP generation will fail."
            )

    @property
    def client(self) -> AsyncOpenAI:
        """Get or create AsyncOpenAI client (lazy initialization)."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    def build_prompt(self, stories: List[TopStory], report_type: str = "daily") -> str:
        """
        Build prompt for LLM generation.

        Constructs a detailed prompt containing all story information
        formatted for intelligence analysis.

        Args:
            stories: List of top stories to include
            report_type: Type of report (daily, weekly, breaking)

        Returns:
            Formatted prompt string for LLM
        """
        lines = [
            f"Generate a {report_type.upper()} SITREP based on these {len(stories)} news clusters:",
            "",
            f"Analysis Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Report Type: {report_type.upper()}",
            "",
            "=" * 60,
            "CLUSTER DATA",
            "=" * 60,
            "",
        ]

        total_articles = 0
        breaking_count = 0
        all_entities = set()

        for i, story in enumerate(stories, 1):
            total_articles += story.article_count
            if story.is_breaking:
                breaking_count += 1

            # Mark breaking news prominently
            breaking_tag = " [BREAKING NEWS]" if story.is_breaking else ""
            category_tag = f" [{story.category.upper()}]" if story.category != "default" else ""

            lines.append(f"### CLUSTER {i}{breaking_tag}{category_tag}")
            lines.append(f"**Title:** {story.title}")
            lines.append(f"- Articles: {story.article_count}")
            lines.append(f"- Tension Score: {story.tension_score:.1f}/10")
            lines.append(f"- Relevance Score: {story.relevance_score:.2f}")
            lines.append(f"- Category: {story.category}")
            lines.append(f"- First Seen: {story.first_seen_at.strftime('%Y-%m-%d %H:%M UTC')}")

            if story.growth_rate is not None:
                lines.append(f"- Growth Rate: {story.growth_rate:.1f}x")

            if story.top_entities:
                entities_str = ", ".join(story.top_entities[:5])
                lines.append(f"- Key Entities: {entities_str}")
                all_entities.update(story.top_entities[:5])

            lines.append("")

        lines.extend([
            "=" * 60,
            "SUMMARY STATISTICS",
            "=" * 60,
            f"- Total Clusters: {len(stories)}",
            f"- Total Articles: {total_articles}",
            f"- Breaking News Items: {breaking_count}",
            f"- Unique Entities: {len(all_entities)}",
            "",
            "=" * 60,
            "INSTRUCTIONS",
            "=" * 60,
            "",
            self.STRUCTURED_OUTPUT_PROMPT,
        ])

        return "\n".join(lines)

    def extract_entities(self, stories: List[TopStory]) -> List[str]:
        """
        Extract unique entities from stories.

        Collects all entities mentioned across stories and returns
        a deduplicated list.

        Args:
            stories: List of stories to extract entities from

        Returns:
            List of unique entity names
        """
        entities = set()
        for story in stories:
            entities.update(story.top_entities)
        return sorted(list(entities))

    async def _call_llm(
        self,
        prompt: str,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with retry logic.

        Handles API errors with exponential backoff and returns
        the parsed JSON response.

        Args:
            prompt: User prompt to send
            retry_count: Current retry attempt number

        Returns:
            Parsed JSON response from LLM

        Raises:
            SitrepGenerationError: If all retries fail
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content

            # Parse JSON response
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Raw response: {content[:500]}...")
                raise SitrepGenerationError(f"Invalid JSON response: {e}")

            # Return response with usage info
            return {
                "content": parsed,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except RateLimitError as e:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY_BASE * (2 ** retry_count)
                logger.warning(
                    f"Rate limit hit, retrying in {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})"
                )
                import asyncio
                await asyncio.sleep(delay)
                return await self._call_llm(prompt, retry_count + 1)
            raise SitrepGenerationError(f"Rate limit exceeded after {self.MAX_RETRIES} retries: {e}")

        except APITimeoutError as e:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY_BASE * (2 ** retry_count)
                logger.warning(
                    f"API timeout, retrying in {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})"
                )
                import asyncio
                await asyncio.sleep(delay)
                return await self._call_llm(prompt, retry_count + 1)
            raise SitrepGenerationError(f"API timeout after {self.MAX_RETRIES} retries: {e}")

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise SitrepGenerationError(f"OpenAI API error: {e}")

        except Exception as e:
            logger.exception(f"Unexpected error calling LLM: {e}")
            raise SitrepGenerationError(f"LLM call failed: {e}")

    def _parse_key_developments(
        self,
        developments_data: List[Dict[str, Any]],
        stories: List[TopStory],
    ) -> List[KeyDevelopment]:
        """
        Parse key developments from LLM response.

        Converts raw development data into structured KeyDevelopment
        objects with risk assessments.

        Args:
            developments_data: Raw development data from LLM
            stories: Source stories for cluster ID mapping

        Returns:
            List of KeyDevelopment objects
        """
        developments = []
        story_map = {s.title.lower(): s.cluster_id for s in stories}

        for dev in developments_data[:5]:  # Limit to top 5 developments
            try:
                # Find matching cluster ID
                cluster_id = None
                title_lower = dev.get("title", "").lower()
                for story_title, cid in story_map.items():
                    if story_title in title_lower or title_lower in story_title:
                        cluster_id = cid
                        break

                risk = None
                if dev.get("risk_level"):
                    risk = RiskAssessment(
                        level=dev.get("risk_level", "medium"),
                        category=dev.get("risk_category", "operational"),
                        description=dev.get("significance", ""),
                    )

                development = KeyDevelopment(
                    title=dev.get("title", "Unknown Development"),
                    summary=dev.get("summary", ""),
                    significance=dev.get("significance", ""),
                    risk_assessment=risk,
                    related_entities=dev.get("related_entities", []),
                    source_cluster_id=cluster_id,
                )
                developments.append(development)

            except Exception as e:
                logger.warning(f"Failed to parse development: {e}")
                continue

        return developments

    async def generate(
        self,
        stories: List[TopStory],
        report_type: str = "daily",
        report_date: Optional[date] = None,
        category: Optional[str] = None,
    ) -> SitrepResponse:
        """
        Generate SITREP from stories.

        Main entry point for SITREP generation. Takes top stories
        and produces a complete intelligence briefing.

        Args:
            stories: List of top stories to analyze
            report_type: Type of report (daily, weekly, breaking)
            report_date: Date for report (defaults to today)
            category: Category filter used for this SITREP (optional)

        Returns:
            Generated SitrepResponse with full briefing

        Raises:
            ValueError: If no stories provided
            SitrepGenerationError: If generation fails
        """
        if not stories:
            raise ValueError("No stories provided for SITREP generation")

        if report_date is None:
            report_date = date.today()

        logger.info(
            f"Generating {report_type} SITREP from {len(stories)} stories"
        )

        # Build prompt
        prompt = self.build_prompt(stories, report_type)
        prompt_length = len(prompt)
        logger.debug(f"Prompt length: {prompt_length} characters")

        # Call LLM
        start_time = time.time()
        try:
            response = await self._call_llm(prompt)
        except SitrepGenerationError:
            raise
        except Exception as e:
            raise SitrepGenerationError(f"Failed to generate SITREP: {e}")

        generation_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"LLM response received in {generation_time_ms}ms")

        # Extract response content
        content = response["content"]
        usage = response["usage"]

        # Extract entities
        entities = self.extract_entities(stories)

        # Parse key developments
        key_developments = self._parse_key_developments(
            content.get("key_developments", []),
            stories,
        )

        # Extract sentiment summary
        sentiment_data = content.get("sentiment_analysis", {})
        sentiment_summary = {
            "overall": sentiment_data.get("overall", "neutral"),
            "positive_percent": sentiment_data.get("positive_percent", 0.0),
            "negative_percent": sentiment_data.get("negative_percent", 0.0),
            "neutral_percent": sentiment_data.get("neutral_percent", 100.0),
        }

        # Extract emerging signals
        emerging_signals = None
        if content.get("emerging_signals"):
            emerging_signals = [
                {
                    "signal_type": s.get("signal_type", "trend"),
                    "description": s.get("description", ""),
                    "confidence": s.get("confidence", 0.5),
                    "related_entities": s.get("related_entities", []),
                }
                for s in content.get("emerging_signals", [])
            ]

        # Build response
        return SitrepResponse(
            id=uuid4(),
            report_date=report_date,
            report_type=report_type,
            category=category,
            title=f"{report_type.title()} SITREP - {report_date}",
            executive_summary=content.get("executive_summary", "Summary not available."),
            content_markdown=content.get("content_markdown", ""),
            content_html=None,  # TODO: Convert markdown to HTML if needed
            key_developments=key_developments,
            top_stories=[
                {
                    "cluster_id": str(s.cluster_id),
                    "title": s.title,
                    "article_count": s.article_count,
                    "tension_score": s.tension_score,
                    "is_breaking": s.is_breaking,
                    "category": s.category,
                }
                for s in stories
            ],
            key_entities=[
                {"name": e, "type": "unknown", "mention_count": 1}
                for e in entities
            ],
            sentiment_summary=sentiment_summary,
            emerging_signals=emerging_signals,
            generation_model=settings.OPENAI_MODEL,
            generation_time_ms=generation_time_ms,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            articles_analyzed=sum(s.article_count for s in stories),
            confidence_score=0.8,  # TODO: Calculate from LLM response
            human_reviewed=False,
            created_at=datetime.now(timezone.utc),
        )

    async def generate_with_review(
        self,
        stories: List[TopStory],
        report_type: str = "daily",
        report_date: Optional[date] = None,
        category: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> tuple:
        """
        Generate SITREP and submit to review queue for risk scoring.

        This method extends generate() by automatically submitting the
        generated SITREP to the HITL review queue. Based on the risk score:
        - Low risk (< 0.3): Auto-approved, ready for publication
        - High risk (>= 0.3): Pending human review

        Args:
            stories: List of top stories to analyze
            report_type: Type of report (daily, weekly, breaking)
            report_date: Date for report (defaults to today)
            category: Category filter used for this SITREP (optional)
            auth_token: JWT token for review service authentication

        Returns:
            Tuple of (SitrepResponse, ReviewResult) where ReviewResult
            contains the risk score and review status.

        Raises:
            ValueError: If no stories provided
            SitrepGenerationError: If generation fails

        Example:
            >>> sitrep, review = await generator.generate_with_review(stories)
            >>> if review.is_approved:
            ...     publish(sitrep)
            ... else:
            ...     queue_for_review(sitrep, review)
        """
        from app.services.review_client import get_review_client, ReviewClientError

        # First, generate the SITREP
        sitrep = await self.generate(
            stories=stories,
            report_type=report_type,
            report_date=report_date,
            category=category,
        )

        # Build content for risk analysis
        # Combine executive summary and key developments for comprehensive analysis
        content_parts = [sitrep.executive_summary]

        if sitrep.key_developments:
            for dev in sitrep.key_developments:
                content_parts.append(dev.title)
                content_parts.append(dev.summary)
                if dev.significance:
                    content_parts.append(dev.significance)

        content_for_review = "\n\n".join(content_parts)

        # Submit to review queue
        try:
            client = get_review_client()
            review_result = await client.submit_for_review(
                target_type="sitrep",
                target_id=str(sitrep.id),
                content=content_for_review,
                metadata={
                    "ai_generated": True,
                    "source": "sitrep-service",
                    "report_type": report_type,
                    "report_date": str(report_date or date.today()),
                    "category": category,
                    "articles_analyzed": sitrep.articles_analyzed,
                    "generation_model": sitrep.generation_model,
                },
                auth_token=auth_token,
            )

            logger.info(
                f"SITREP {sitrep.id} submitted for review: "
                f"risk_score={review_result.risk_score}, "
                f"status={review_result.status}"
            )

            # Update human_reviewed field based on review result
            if review_result.is_approved:
                # For auto-approved, mark as reviewed (by system)
                sitrep.human_reviewed = True

            return sitrep, review_result

        except ReviewClientError as e:
            logger.error(f"Failed to submit SITREP for review: {e}")
            # Return SITREP with a default "pending" review result
            # to ensure safety - don't auto-publish on error
            from app.services.review_client import ReviewResult
            default_review = ReviewResult(
                id="error",
                target_type="sitrep",
                target_id=str(sitrep.id),
                risk_score=1.0,  # High risk on error
                risk_level="high",
                risk_factors=["review_service_error"],
                status="pending",
                error=str(e),
            )
            return sitrep, default_review

    async def generate_summary_only(
        self,
        stories: List[TopStory],
    ) -> str:
        """
        Generate only an executive summary (lighter weight).

        Useful for quick previews or low-token-cost summaries.

        Args:
            stories: List of top stories to summarize

        Returns:
            Executive summary string
        """
        if not stories:
            return "No stories available for summary."

        # Build lighter prompt for summary only
        story_titles = [
            f"- {s.title}" + (" [BREAKING]" if s.is_breaking else "")
            for s in stories[:5]
        ]

        prompt = f"""Provide a 2-3 sentence executive summary of these top news stories:

{chr(10).join(story_titles)}

Total articles analyzed: {sum(s.article_count for s in stories)}

Respond with ONLY the summary text, no JSON or formatting."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a news analyst providing brief summaries."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=settings.OPENAI_TEMPERATURE,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary generation failed."
