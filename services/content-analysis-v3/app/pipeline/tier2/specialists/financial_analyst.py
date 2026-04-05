"""
Tier2 Financial Analyst Specialist
Analyzes financial implications, market impact, and affected symbols
"""

import json
import logging
from uuid import UUID
from typing import Any

from ..base import BaseSpecialist
from ..models import (
    QuickCheckResult,
    SpecialistFindings,
    SpecialistType,
    FinancialMetrics
)

logger = logging.getLogger(__name__)


QUICK_CHECK_PROMPT = """Quick relevance check: Does this article discuss financial/economic topics?

ARTICLE:
Title: {title}
Content: {content}...

TIER1 TOPICS: {topics}

Is this article about finance, markets, economy, companies, or trading?
Reply with JSON: {{"is_relevant": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
"""


DEEP_DIVE_PROMPT = """Analyze financial implications of this article.

ARTICLE:
Title: {title}
Content: {content}

TIER1 ENTITIES: {entities}
TIER1 TOPICS: {topics}

OUTPUT (JSON):
{{
  "metrics": {{
    "market_impact": 0.0-10.0,
    "volatility_expected": 0.0-10.0,
    "sector_affected": "TECHNOLOGY|FINANCE|ENERGY|HEALTHCARE|COMMODITIES|CRYPTO|OTHER",
    "price_direction": "BULLISH|BEARISH|NEUTRAL"
  }},
  "affected_symbols": ["TSLA", "BTC-USD", "AAPL"]
}}

METRICS SCORING:
- market_impact: How much will this affect markets? (0=none, 5=moderate, 10=massive)
- volatility_expected: How much price movement expected? (0=stable, 5=moderate, 10=extreme)
- sector_affected: Primary sector most impacted
- price_direction: Overall directional bias (BULLISH=up, BEARISH=down, NEUTRAL=uncertain)

AFFECTED SYMBOLS:
- List 1-5 most affected stock symbols, crypto pairs, or indices
- Use standard format: "TSLA", "BTC-USD", "SPY", "GLD", "EURUSD"
- Only include symbols directly mentioned or strongly implied

Respond with ONLY the JSON object. No explanations.
"""


class FinancialAnalyst(BaseSpecialist):
    """
    Financial Analyst Specialist for Tier2.

    Analyzes articles about financial markets, economy, companies, and trading
    to extract market impact metrics and affected financial symbols.
    """

    def __init__(self):
        """Initialize Financial Analyst specialist."""
        super().__init__(specialist_type=SpecialistType.FINANCIAL_ANALYST)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any
    ) -> QuickCheckResult:
        """
        Stage 1: Fast financial relevance check.

        Checks if article discusses finance, markets, economy, or trading.
        Uses tier1_results.topics to quickly identify financial keywords.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with topics, entities, relations

        Returns:
            QuickCheckResult indicating if article is financially relevant
        """
        logger.info(f"[{article_id}] Financial Analyst: Quick check started")

        # Check Tier1 topics for financial keywords
        financial_keywords = {
            "FINANCE", "MARKETS", "ECONOMY", "TRADING",
            "STOCKS", "CRYPTO", "COMMODITIES", "BANKING"
        }

        # Handle both Topic objects and strings (defensive coding)
        topics_list = []
        for t in tier1_results.topics:
            if isinstance(t, str):
                # Topic is a string (e.g., "SECURITY")
                topics_list.append(t)
            elif hasattr(t, 'keyword'):
                # Topic is an object with keyword attribute
                topics_list.append(f"{t.keyword} (confidence={t.confidence:.2f})")
            else:
                # Unknown type, convert to string
                topics_list.append(str(t))

        topics_str = ", ".join(topics_list) if topics_list else "None"

        # Fast heuristic: Check if any financial topics present
        has_financial_topic = False
        for topic in tier1_results.topics:
            if isinstance(topic, str):
                # Topic is a string
                if topic.upper() in financial_keywords:
                    has_financial_topic = True
                    break
            elif hasattr(topic, 'keyword'):
                # Topic is an object
                if topic.keyword.upper() in financial_keywords:
                    has_financial_topic = True
                    break

        if has_financial_topic:
            # High confidence if Tier1 already identified financial topics
            logger.info(
                f"[{article_id}] Financial Analyst: "
                f"Financial topics found in Tier1, proceeding to deep dive"
            )
            return QuickCheckResult(
                is_relevant=True,
                confidence=0.9,
                reasoning=f"Financial topics detected in Tier1: {topics_str}",
                tokens_used=0  # No LLM call needed
            )

        # Otherwise, use LLM for deeper check
        prompt = QUICK_CHECK_PROMPT.format(
            title=title,
            content=content[:1000],  # Use first 1000 chars for speed
            topics=topics_str
        )

        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=100,
            temperature=0.0
        )

        # Parse response
        try:
            result = json.loads(response_text)
            is_relevant = result.get("is_relevant", False)
            confidence = result.get("confidence", 0.5)
            reasoning = result.get("reasoning", "LLM decision")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"[{article_id}] Financial Analyst: "
                f"Failed to parse quick check response: {e}"
            )
            # Conservative: mark as relevant if unsure
            is_relevant = True
            confidence = 0.5
            reasoning = "Parse error, defaulting to relevant"

        logger.info(
            f"[{article_id}] Financial Analyst: "
            f"Quick check complete - relevant={is_relevant}, "
            f"confidence={confidence:.2f}"
        )

        return QuickCheckResult(
            is_relevant=is_relevant,
            confidence=confidence,
            reasoning=reasoning,
            tokens_used=metadata.tokens_used
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
        Stage 2: Detailed financial analysis.

        Extracts market impact metrics, volatility expectations, affected sectors,
        price direction, and affected financial symbols (stocks, crypto, etc).

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, topics, relations
            max_tokens: Maximum tokens for analysis

        Returns:
            SpecialistFindings with financial_metrics populated
        """
        logger.info(f"[{article_id}] Financial Analyst: Deep dive started")

        # Prepare context from Tier1
        entities_list = [
            f"{e.name} ({e.type})"
            for e in tier1_results.entities[:10]  # Top 10 entities
        ]
        entities_str = ", ".join(entities_list) if entities_list else "None"

        # Handle both Topic objects and strings (defensive coding)
        topics_list = []
        for t in tier1_results.topics:
            if isinstance(t, str):
                topics_list.append(t)
            elif hasattr(t, 'keyword'):
                topics_list.append(t.keyword)
            else:
                topics_list.append(str(t))

        topics_str = ", ".join(topics_list) if topics_list else "None"

        # Prepare prompt
        prompt = DEEP_DIVE_PROMPT.format(
            title=title,
            content=content[:3000],  # Use first 3000 chars for detailed analysis
            entities=entities_str,
            topics=topics_str
        )

        # Generate analysis
        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.0
        )

        # Parse response
        try:
            result = json.loads(response_text)

            # Extract metrics
            metrics = result.get("metrics", {})
            affected_symbols = result.get("affected_symbols", [])

            # Validate metrics
            market_impact = float(metrics.get("market_impact", 0.0))
            volatility_expected = float(metrics.get("volatility_expected", 0.0))
            sector_affected = metrics.get("sector_affected", "OTHER")
            price_direction = metrics.get("price_direction", "NEUTRAL")

            # Create FinancialMetrics
            financial_metrics = FinancialMetrics(
                metrics={
                    "market_impact": market_impact,
                    "volatility_expected": volatility_expected,
                    "sector_affected": sector_affected,
                    "price_direction": price_direction
                },
                affected_symbols=affected_symbols[:10]  # Limit to 10 symbols
            )

            logger.info(
                f"[{article_id}] Financial Analyst: "
                f"Deep dive complete - "
                f"market_impact={market_impact:.1f}, "
                f"volatility={volatility_expected:.1f}, "
                f"sector={sector_affected}, "
                f"direction={price_direction}, "
                f"symbols={len(affected_symbols)}"
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(
                f"[{article_id}] Financial Analyst: "
                f"Failed to parse deep dive response: {e}. "
                f"Response: {response_text[:200]}"
            )
            # Return empty findings on parse error
            financial_metrics = FinancialMetrics(
                metrics={},
                affected_symbols=[]
            )

        return SpecialistFindings(
            specialist_type=SpecialistType.FINANCIAL_ANALYST,
            financial_metrics=financial_metrics,
            tokens_used=metadata.tokens_used,
            cost_usd=metadata.cost_usd,
            model=metadata.model
        )
