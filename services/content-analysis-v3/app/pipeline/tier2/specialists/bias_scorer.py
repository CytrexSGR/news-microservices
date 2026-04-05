"""
Tier2 Bias Scorer Specialist
Analyzes political bias in articles with simplified scoring
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
    PoliticalBiasMetrics
)

logger = logging.getLogger(__name__)


QUICK_CHECK_PROMPT = """Quick check: Does this article have political content or viewpoint?

ARTICLE:
Title: {title}
Content: {content}...

Is this article about politics, policy, ideology, or does it express a political viewpoint?
Reply with JSON: {{"is_relevant": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
"""


DEEP_DIVE_PROMPT = """Analyze political bias.

ARTICLE:
Title: {title}
Content: {content}

OUTPUT (JSON only):
{{
  "political_direction": "far_left|left|center_left|center|center_right|right|far_right",
  "bias_score": -1.0 to +1.0,
  "bias_strength": "minimal|weak|moderate|strong|extreme",
  "confidence": 0.0-1.0
}}

SCALE: far_left (-1.0 to -0.7) → left (-0.7 to -0.4) → center_left (-0.4 to -0.15) → center (-0.15 to +0.15) → center_right (+0.15 to +0.4) → right (+0.4 to +0.7) → far_right (+0.7 to +1.0)

STRENGTH: minimal (|score| < 0.15), weak (0.15-0.4), moderate (0.4-0.7), strong (0.7-0.85), extreme (≥0.85)

ASSESS: Word choice, sources, framing, emphasis, tone. Factual = center (0.0). Slight preference = weak (±0.2). Clear slant = moderate/strong (±0.5-0.8).
"""


class BiasScorer(BaseSpecialist):
    """
    Bias Scorer Specialist for Tier2.

    Analyzes political bias in articles using simplified 7-level scale
    (far_left → far_right) with numerical scoring and strength assessment.

    Applied to ALL articles (not selective like other specialists).
    """

    def __init__(self):
        """Initialize Bias Scorer specialist."""
        super().__init__(specialist_type=SpecialistType.BIAS_SCORER)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any
    ) -> QuickCheckResult:
        """
        Stage 1: Fast political content check.

        Checks if article has political content or expresses political viewpoint.

        NOTE: For bias scoring, we may want to run on ALL articles regardless
        of political content (non-political articles → center score).
        This quick_check can be skipped by always returning is_relevant=True.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with topics, entities, relations

        Returns:
            QuickCheckResult indicating if article has political content
        """
        logger.info(f"[{article_id}] Bias Scorer: Quick check started")

        # For bias scoring, we want to analyze ALL articles
        # Non-political articles will just score as "center" with minimal strength
        # So we always mark as relevant to proceed to deep_dive

        logger.info(
            f"[{article_id}] Bias Scorer: "
            f"Marking all articles relevant (bias applied to all content)"
        )

        return QuickCheckResult(
            is_relevant=True,
            confidence=1.0,
            reasoning="Bias scoring applies to all articles",
            tokens_used=0  # No LLM call needed
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
        Stage 2: Detailed political bias analysis.

        Analyzes article to determine:
        - Political direction (7-level scale)
        - Bias score (-1.0 to +1.0)
        - Bias strength (minimal to extreme)
        - Confidence level

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, topics, relations
            max_tokens: Maximum tokens for analysis

        Returns:
            SpecialistFindings with political_bias populated
        """
        logger.info(f"[{article_id}] Bias Scorer: Deep dive started")

        # Prepare prompt (use first 2000 chars for bias analysis with smart truncation)
        if len(content) > 2000:
            content_preview = content[:2000]
            # Try to cut at sentence boundary for better context
            last_period = max(
                content_preview.rfind('. '),
                content_preview.rfind('.\n'),
                content_preview.rfind('? '),
                content_preview.rfind('! ')
            )
            if last_period > 1500:  # Only if we have at least 1500 chars
                content_preview = content_preview[:last_period + 1]
        else:
            content_preview = content

        prompt = DEEP_DIVE_PROMPT.format(
            title=title,
            content=content_preview
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

            # Extract fields
            political_direction = result.get("political_direction", "center")
            bias_score = float(result.get("bias_score", 0.0))
            bias_strength = result.get("bias_strength", "minimal")
            confidence = float(result.get("confidence", 0.5))

            # Validate bias_score range
            bias_score = max(-1.0, min(1.0, bias_score))

            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))

            # Create PoliticalBiasMetrics
            political_bias = PoliticalBiasMetrics(
                political_direction=political_direction,
                bias_score=bias_score,
                bias_strength=bias_strength,
                confidence=confidence
            )

            logger.info(
                f"[{article_id}] Bias Scorer: "
                f"Deep dive complete - "
                f"direction={political_direction}, "
                f"score={bias_score:.2f}, "
                f"strength={bias_strength}, "
                f"confidence={confidence:.2f}"
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(
                f"[{article_id}] Bias Scorer: "
                f"Failed to parse deep dive response: {e}. "
                f"Response: {response_text[:200]}"
            )
            # Return center/minimal on parse error (neutral fallback)
            political_bias = PoliticalBiasMetrics(
                political_direction="center",
                bias_score=0.0,
                bias_strength="minimal",
                confidence=0.0
            )

        return SpecialistFindings(
            specialist_type=SpecialistType.BIAS_SCORER,
            political_bias=political_bias,
            tokens_used=metadata.tokens_used,
            cost_usd=metadata.cost_usd,
            model=metadata.model
        )
