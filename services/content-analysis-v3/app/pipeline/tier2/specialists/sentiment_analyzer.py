"""
Tier2 Sentiment Analyzer Specialist
Analyzes article sentiment with financial/opinion focus
"""

import json
import logging
from typing import Any
from uuid import UUID

from app.pipeline.tier2.base import BaseSpecialist
from app.pipeline.tier2.models import (
    QuickCheckResult,
    SpecialistFindings,
    SpecialistType,
    SentimentMetrics
)

logger = logging.getLogger(__name__)


class SentimentAnalyzerSpecialist(BaseSpecialist):
    """
    Analyzes sentiment in articles.

    For financial articles: bullish/bearish sentiment ratios
    For non-financial: positive/negative sentiment ratios

    Two-stage approach:
    1. quick_check: Determine if sentiment analysis is valuable
    2. deep_dive: Extract detailed sentiment metrics
    """

    def __init__(self):
        """Initialize sentiment analyzer."""
        super().__init__(SpecialistType.SENTIMENT_ANALYZER)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any
    ) -> QuickCheckResult:
        """
        Stage 1: Determine if sentiment analysis is valuable.

        Checks:
        - Is this financial/market news?
        - Is this opinion-heavy content?
        - Does tier1 indicate entities/topics worth sentiment analysis?

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, relations, topics

        Returns:
            QuickCheckResult indicating if deep sentiment analysis is needed
        """
        logger.debug(f"[{article_id}] SENTIMENT_ANALYZER: quick_check")

        # Build prompt for relevance check
        # Use tier1 entities to avoid re-extraction
        entities_str = "None"
        if hasattr(tier1_results, 'entities') and tier1_results.entities:
            entity_names = [e.name for e in tier1_results.entities[:5]]
            entities_str = ", ".join(entity_names)

        topics_str = "None"
        if hasattr(tier1_results, 'topics') and tier1_results.topics:
            topics_str = ", ".join([t.keyword for t in tier1_results.topics[:3]])

        prompt = f"""Is sentiment analysis valuable for this article?

ARTICLE:
Title: {title}
Entities: {entities_str}
Topics: {topics_str}
Content Preview: {content[:400]}

Sentiment analysis is valuable if:
- Financial/market news (stocks, crypto, economy)
- Opinion pieces or editorial content
- Contains strong emotional language
- Political or controversial topics

OUTPUT (JSON):
{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}

Keep it brief. Check if sentiment analysis adds value."""

        try:
            # Call LLM
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.0
            )

            # Parse JSON response
            result = json.loads(response_text)

            return QuickCheckResult(
                is_relevant=result.get("is_relevant", False),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", "No reasoning provided"),
                tokens_used=metadata.tokens_used
            )

        except json.JSONDecodeError as e:
            logger.warning(f"[{article_id}] JSON parse failed in quick_check: {e}")
            # Conservative: assume relevant if parsing fails
            return QuickCheckResult(
                is_relevant=True,
                confidence=0.5,
                reasoning="Parse error - defaulting to relevant",
                tokens_used=0
            )
        except Exception as e:
            logger.error(f"[{article_id}] quick_check failed: {e}")
            # Conservative: assume relevant on error
            return QuickCheckResult(
                is_relevant=True,
                confidence=0.5,
                reasoning=f"Error: {str(e)}",
                tokens_used=0
            )

    async def deep_dive(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any,
        max_tokens: int
    ) -> SpecialistFindings:
        """
        Stage 2: Extract detailed sentiment metrics.

        Analyzes sentiment ratios and confidence:
        - Financial articles: bullish_ratio, bearish_ratio
        - Non-financial: positive_ratio, negative_ratio
        - Always: confidence score

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results object
            max_tokens: Maximum tokens for this analysis

        Returns:
            SpecialistFindings with sentiment_metrics populated
        """
        logger.debug(f"[{article_id}] SENTIMENT_ANALYZER: deep_dive (max_tokens={max_tokens})")

        # Truncate content to fit within token budget
        # Rough estimate: 1 token ≈ 4 characters
        max_content_chars = (max_tokens - 300) * 4  # Reserve 300 tokens for prompt structure
        content_truncated = content[:max_content_chars]

        # Check if this is financial content based on tier1 results
        is_financial = self._is_financial_content(tier1_results)
        sentiment_type = "bullish/bearish" if is_financial else "positive/negative"

        prompt = f"""Analyze sentiment in this article.

ARTICLE:
Title: {title}
Content: {content_truncated}

OUTPUT (JSON):
{{
  "metrics": {{
    "bullish_ratio": 0.0-1.0,
    "bearish_ratio": 0.0-1.0,
    "confidence": 0.0-1.0
  }}
}}

Instructions:
- For financial articles: Use bullish_ratio (optimistic market outlook) and bearish_ratio (pessimistic market outlook)
- For non-financial: Use bullish_ratio for positive sentiment and bearish_ratio for negative sentiment
- Ratios should sum to approximately 1.0 (allow neutral content: sum < 1.0)
- Confidence indicates certainty of sentiment assessment
- This article appears to be: {sentiment_type} content

Focus on overall tone, not individual sentences."""

        try:
            # Call LLM
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0
            )

            # Parse JSON response
            result = json.loads(response_text)
            metrics_data = result.get("metrics", {})

            # Validate and normalize metrics
            bullish_ratio = float(metrics_data.get("bullish_ratio", 0.5))
            bearish_ratio = float(metrics_data.get("bearish_ratio", 0.5))
            confidence = float(metrics_data.get("confidence", 0.5))

            # Clamp values to [0, 1]
            bullish_ratio = max(0.0, min(1.0, bullish_ratio))
            bearish_ratio = max(0.0, min(1.0, bearish_ratio))
            confidence = max(0.0, min(1.0, confidence))

            # Normalize if sum > 1.0
            total = bullish_ratio + bearish_ratio
            if total > 1.0:
                bullish_ratio /= total
                bearish_ratio /= total

            sentiment_metrics = SentimentMetrics(
                metrics={
                    "bullish_ratio": round(bullish_ratio, 3),
                    "bearish_ratio": round(bearish_ratio, 3),
                    "confidence": round(confidence, 3),
                    "is_financial": is_financial
                }
            )

            return SpecialistFindings(
                specialist_type=SpecialistType.SENTIMENT_ANALYZER,
                sentiment_metrics=sentiment_metrics,
                tokens_used=metadata.tokens_used,
                cost_usd=metadata.cost_usd,
                model=metadata.model
            )

        except json.JSONDecodeError as e:
            logger.error(f"[{article_id}] JSON parse failed in deep_dive: {e}")
            # Return neutral sentiment on parse failure
            return self._neutral_findings(metadata.tokens_used if 'metadata' in locals() else 0)

        except Exception as e:
            logger.error(f"[{article_id}] deep_dive failed: {e}")
            # Return neutral sentiment on error
            return self._neutral_findings(0)

    def _is_financial_content(self, tier1_results: Any) -> bool:
        """
        Determine if content is financial based on tier1 results.

        Checks for financial entities, topics, or keywords.

        Args:
            tier1_results: Tier1Results object

        Returns:
            True if financial content detected
        """
        financial_keywords = {
            'stock', 'market', 'crypto', 'bitcoin', 'ethereum', 'trading',
            'investment', 'finance', 'economy', 'bull', 'bear', 'portfolio',
            'price', 'dollar', 'currency', 'forex', 'commodity'
        }

        # Check topics
        if hasattr(tier1_results, 'topics') and tier1_results.topics:
            topics_lower = [t.keyword.lower() for t in tier1_results.topics]
            if any(keyword in topic for topic in topics_lower for keyword in financial_keywords):
                return True

        # Check entities
        if hasattr(tier1_results, 'entities') and tier1_results.entities:
            for entity in tier1_results.entities:
                entity_name = entity.name.lower()
                entity_type = entity.type.lower()

                # Check entity name
                if any(keyword in entity_name for keyword in financial_keywords):
                    return True

                # Check entity type
                if entity_type in ['organization', 'product', 'money']:
                    return True

        return False

    def _neutral_findings(self, tokens_used: int) -> SpecialistFindings:
        """
        Create neutral sentiment findings (fallback).

        Args:
            tokens_used: Tokens consumed before error

        Returns:
            SpecialistFindings with neutral sentiment (0.5/0.5)
        """
        return SpecialistFindings(
            specialist_type=SpecialistType.SENTIMENT_ANALYZER,
            sentiment_metrics=SentimentMetrics(
                metrics={
                    "bullish_ratio": 0.5,
                    "bearish_ratio": 0.5,
                    "confidence": 0.3,
                    "is_financial": False,
                    "error": "Fallback to neutral sentiment"
                }
            ),
            tokens_used=tokens_used,
            cost_usd=0.0,
            model="error-fallback"
        )
