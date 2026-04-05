"""
TOPIC_CLASSIFIER Specialist - Tier2
Detailed topic classification with parent categories
"""

import logging
import json
from uuid import UUID
from typing import Any

from app.pipeline.tier2.base import BaseSpecialist
from app.pipeline.tier2.models import (
    SpecialistType,
    QuickCheckResult,
    SpecialistFindings,
    TopicClassification
)
from app.models.schemas import Tier1Results

logger = logging.getLogger(__name__)


QUICK_CHECK_PROMPT = """Does this article discuss specific topics worth detailed classification?

ARTICLE:
Title: {title}

TIER1 TOPICS: {topics}

Analyze if these topics warrant detailed classification (specific subcategories, industry sectors, etc.).

Answer YES or NO with brief reason (max 20 words).

Format:
YES - reason
or
NO - reason
"""


DEEP_DIVE_PROMPT = """Classify this article into detailed topics with parent categories.

ARTICLE:
Title: {title}
Content: {content}

TIER1 TOPICS (as reference): {tier1_topics}

INSTRUCTIONS:
1. Provide 2-5 detailed, specific topics (not just broad categories)
2. Each topic should have a parent category for hierarchical organization
3. Topics should be more granular than Tier1 keywords
4. Assign confidence based on topic prominence in article

OUTPUT (JSON):
{{
  "topics": [
    {{
      "topic": "Bitcoin Price Analysis",
      "parent_topic": "Economics and Finance",
      "confidence": 0.95
    }},
    {{
      "topic": "Federal Reserve Policy",
      "parent_topic": "Economics and Finance",
      "confidence": 0.85
    }}
  ]
}}

EXAMPLES OF GOOD TOPICS:
- "Renewable Energy Investment" under "Technology and Innovation"
- "NATO Military Strategy" under "Geopolitics and Defense"
- "Central Bank Digital Currency" under "Economics and Finance"
- "AI Ethics and Regulation" under "Technology and Innovation"

EXAMPLES OF PARENT TOPICS:
- Economics and Finance
- Geopolitics and Defense
- Technology and Innovation
- Social and Cultural Issues
- Environmental and Climate
- Legal and Regulatory
- Healthcare and Biosciences
- Energy and Resources

Respond with ONLY the JSON object. No explanations.
"""


class TopicClassifierSpecialist(BaseSpecialist):
    """
    TOPIC_CLASSIFIER - Detailed topic classification with hierarchy.

    Purpose: Enhance Tier1's broad topic keywords with specific,
    detailed topics organized into parent categories.

    Budget: ~1700 tokens (200 quick check + 1500 deep dive)
    """

    def __init__(self):
        super().__init__(specialist_type=SpecialistType.TOPIC_CLASSIFIER)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results
    ) -> QuickCheckResult:
        """
        Stage 1: Fast relevance check.

        Determines if article has classifiable topics worth detailed analysis.
        Uses Tier1 topics to make quick decision.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content (not used in quick check)
            tier1_results: Tier1Results with basic topic keywords

        Returns:
            QuickCheckResult with relevance decision
        """
        logger.info(f"[{article_id}] TOPIC_CLASSIFIER: Quick check starting")

        # Format Tier1 topics for prompt
        tier1_topics = [
            f"{topic.keyword} (confidence={topic.confidence:.2f})"
            for topic in tier1_results.topics
        ]
        topics_str = ", ".join(tier1_topics) if tier1_topics else "None identified"

        # Prepare prompt
        prompt = QUICK_CHECK_PROMPT.format(
            title=title,
            topics=topics_str
        )

        # Call LLM
        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=100,  # Small budget for quick check
                temperature=0.0
            )

            # Parse response
            response_text = response_text.strip()
            is_relevant = response_text.upper().startswith("YES")

            # Extract reasoning (after YES/NO and dash)
            if " - " in response_text:
                reasoning = response_text.split(" - ", 1)[1].strip()
            else:
                reasoning = response_text

            # Confidence based on number of Tier1 topics
            confidence = min(0.95, 0.6 + (len(tier1_results.topics) * 0.15))

            result = QuickCheckResult(
                is_relevant=is_relevant,
                confidence=confidence,
                reasoning=reasoning,
                tokens_used=metadata.tokens_used
            )

            logger.info(
                f"[{article_id}] TOPIC_CLASSIFIER: Quick check complete - "
                f"relevant={is_relevant}, confidence={confidence:.2f}, "
                f"tokens={metadata.tokens_used}"
            )

            return result

        except Exception as e:
            logger.error(f"[{article_id}] TOPIC_CLASSIFIER: Quick check failed: {e}")
            # Conservative fallback: assume relevant if we have topics
            return QuickCheckResult(
                is_relevant=len(tier1_results.topics) > 0,
                confidence=0.5,
                reasoning=f"Error during quick check: {str(e)}",
                tokens_used=0
            )

    async def deep_dive(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results,
        max_tokens: int
    ) -> SpecialistFindings:
        """
        Stage 2: Detailed topic classification.

        Extracts 2-5 specific topics with parent categories,
        building on Tier1's broad keyword classification.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with basic topics
            max_tokens: Token budget for this analysis

        Returns:
            SpecialistFindings with detailed topic_classification
        """
        logger.info(
            f"[{article_id}] TOPIC_CLASSIFIER: Deep dive starting "
            f"(max_tokens={max_tokens})"
        )

        # Format Tier1 topics for context
        tier1_topics_list = [
            {
                "keyword": topic.keyword,
                "confidence": topic.confidence,
                "parent_category": topic.parent_category
            }
            for topic in tier1_results.topics
        ]
        tier1_topics_json = json.dumps(tier1_topics_list, indent=2)

        # Prepare prompt
        prompt = DEEP_DIVE_PROMPT.format(
            title=title,
            content=content[:3000],  # Limit content to control token usage
            tier1_topics=tier1_topics_json
        )

        # Call LLM
        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0
            )

            # Parse JSON response
            try:
                response_data = json.loads(response_text)
                topics = response_data.get("topics", [])

                # Validate topic structure
                validated_topics = []
                for topic in topics:
                    if all(k in topic for k in ["topic", "parent_topic", "confidence"]):
                        validated_topics.append({
                            "topic": str(topic["topic"]),
                            "parent_topic": str(topic["parent_topic"]),
                            "confidence": float(topic["confidence"])
                        })

                # Create findings
                findings = SpecialistFindings(
                    specialist_type=SpecialistType.TOPIC_CLASSIFIER,
                    topic_classification=TopicClassification(
                        topics=validated_topics
                    ),
                    tokens_used=metadata.tokens_used,
                    cost_usd=metadata.cost_usd,
                    model=metadata.model
                )

                logger.info(
                    f"[{article_id}] TOPIC_CLASSIFIER: Deep dive complete - "
                    f"topics={len(validated_topics)}, "
                    f"tokens={metadata.tokens_used}, "
                    f"cost=${metadata.cost_usd:.6f}"
                )

                return findings

            except json.JSONDecodeError as e:
                logger.error(
                    f"[{article_id}] TOPIC_CLASSIFIER: JSON parse failed: {e}"
                )
                # Return empty findings with metadata
                return SpecialistFindings(
                    specialist_type=SpecialistType.TOPIC_CLASSIFIER,
                    topic_classification=TopicClassification(topics=[]),
                    tokens_used=metadata.tokens_used,
                    cost_usd=metadata.cost_usd,
                    model=metadata.model
                )

        except Exception as e:
            logger.error(f"[{article_id}] TOPIC_CLASSIFIER: Deep dive failed: {e}")
            # Return empty findings
            return SpecialistFindings(
                specialist_type=SpecialistType.TOPIC_CLASSIFIER,
                topic_classification=TopicClassification(topics=[]),
                tokens_used=0,
                cost_usd=0.0,
                model=self.provider.model
            )
