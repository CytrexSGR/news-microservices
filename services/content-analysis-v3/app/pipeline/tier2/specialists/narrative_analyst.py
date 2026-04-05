"""
Tier2 Narrative Analyst Specialist
Detects narrative frames and entity portrayal in news articles
"""

import json
import logging
from typing import Any, List, Dict
from uuid import UUID

from app.pipeline.tier2.base import BaseSpecialist
from app.pipeline.tier2.models import (
    QuickCheckResult,
    SpecialistFindings,
    SpecialistType,
    NarrativeFrame,
    NarrativeFrameMetrics
)

logger = logging.getLogger(__name__)


# Frame types with detection guidance
FRAME_TYPES = {
    "victim": "Entity portrayed as suffering, harmed, or oppressed",
    "hero": "Entity portrayed as savior, helper, or positive force",
    "threat": "Entity portrayed as dangerous, harmful, or problematic",
    "solution": "Action/entity portrayed as the answer to a problem",
    "conflict": "Framing emphasizing opposition, struggle, or tension",
    "economic": "Framing focused on financial/economic impacts",
    "moral": "Framing with ethical/moral implications",
    "attribution": "Framing that assigns blame or responsibility"
}

# Propaganda techniques to detect
PROPAGANDA_INDICATORS = [
    "loaded_language",
    "appeal_to_fear",
    "bandwagon",
    "false_dilemma",
    "ad_hominem",
    "straw_man",
    "cherry_picking",
    "appeal_to_authority",
    "emotional_appeal",
    "oversimplification"
]


class NarrativeAnalyst(BaseSpecialist):
    """
    Analyzes narrative framing in news articles.

    Detects:
    - Narrative frames (victim, hero, threat, etc.)
    - Entity portrayal (how entities are presented)
    - Propaganda indicators
    - Narrative tension levels

    Two-stage approach:
    1. quick_check: Determine if narrative analysis is valuable
    2. deep_dive: Extract detailed frame analysis
    """

    def __init__(self):
        """Initialize narrative analyst."""
        super().__init__(SpecialistType.NARRATIVE_ANALYST)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any
    ) -> QuickCheckResult:
        """
        Stage 1: Determine if narrative analysis is valuable.

        Checks:
        - Does the article have clear entities that could be framed?
        - Is this opinion/editorial content?
        - Does it discuss events with multiple perspectives?

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, relations, topics

        Returns:
            QuickCheckResult indicating if deep narrative analysis is needed
        """
        logger.debug(f"[{article_id}] NARRATIVE_ANALYST: quick_check")

        # Build entity context from tier1
        entities_str = "None"
        if hasattr(tier1_results, 'entities') and tier1_results.entities:
            entity_names = [e.name for e in tier1_results.entities[:8]]
            entities_str = ", ".join(entity_names)

        topics_str = "None"
        if hasattr(tier1_results, 'topics') and tier1_results.topics:
            topics_str = ", ".join([t.keyword for t in tier1_results.topics[:5]])

        prompt = f"""Is narrative framing analysis valuable for this article?

ARTICLE:
Title: {title}
Entities: {entities_str}
Topics: {topics_str}
Content Preview: {content[:500]}

Narrative analysis is valuable if:
- Political, geopolitical, or controversial topics
- Multiple actors/entities involved
- Potential for bias or one-sided portrayal
- Opinion pieces or editorial content
- Conflict or crisis coverage
- Stories with clear protagonists/antagonists

OUTPUT (JSON):
{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}

Keep it brief. Check if narrative framing analysis adds value."""

        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.0
            )

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
        Stage 2: Extract detailed narrative frame analysis.

        Analyzes:
        - Detected frames with entities and confidence
        - Entity portrayal mapping
        - Dominant narrative frame
        - Propaganda indicators

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results object
            max_tokens: Maximum tokens for this analysis

        Returns:
            SpecialistFindings with narrative_frame_metrics populated
        """
        logger.debug(f"[{article_id}] NARRATIVE_ANALYST: deep_dive (max_tokens={max_tokens})")

        # Truncate content to fit within token budget
        max_content_chars = (max_tokens - 500) * 4
        content_truncated = content[:max_content_chars]

        # Build entity list from tier1
        entities_str = ""
        if hasattr(tier1_results, 'entities') and tier1_results.entities:
            entity_names = [e.name for e in tier1_results.entities[:10]]
            entities_str = ", ".join(entity_names)

        frame_descriptions = "\n".join([f"- {k}: {v}" for k, v in FRAME_TYPES.items()])

        prompt = f"""Analyze narrative framing in this news article.

ARTICLE:
Title: {title}
Content: {content_truncated}

⚠️ AVAILABLE ENTITIES (USE ONLY THESE - DO NOT INVENT NEW ONES):
{entities_str if entities_str else "No entities extracted - skip entity mapping"}

FRAME TYPES:
{frame_descriptions}

PROPAGANDA TECHNIQUES TO CHECK:
loaded_language, appeal_to_fear, bandwagon, false_dilemma, ad_hominem,
straw_man, cherry_picking, appeal_to_authority, emotional_appeal, oversimplification

OUTPUT (JSON):
{{
  "frames": [
    {{
      "frame_type": "victim|hero|threat|solution|conflict|economic|moral|attribution",
      "confidence": 0.0-1.0,
      "entities": ["Entity1 from list above"],
      "text_excerpt": "Brief quote supporting this frame",
      "role_mapping": {{"Entity1": "role"}}
    }}
  ],
  "dominant_frame": "most prominent frame type",
  "entity_portrayals": {{
    "Entity Name from list above": ["victim", "hero"]
  }},
  "narrative_tension": 0.0-1.0,
  "propaganda_indicators": ["technique1"] or []
}}

🚨 CRITICAL RULES:
1. "entities" field MUST ONLY contain names from AVAILABLE ENTITIES list above
2. DO NOT create new entities, descriptions, or phrases
3. If no matching entity exists, use empty array: "entities": []
4. "entity_portrayals" keys MUST be exact entity names from the list
5. Identify 1-4 narrative frames per article
6. Rate tension: 0=neutral/factual, 1=highly charged"""

        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0
            )

            result = json.loads(response_text)

            # Get valid entity names from tier1 for validation
            valid_entities = set()
            if hasattr(tier1_results, 'entities') and tier1_results.entities:
                valid_entities = {e.name for e in tier1_results.entities}

            # Parse frames with entity validation
            frames = []
            for frame_data in result.get("frames", []):
                raw_entities = frame_data.get("entities", [])
                raw_role_mapping = frame_data.get("role_mapping", {})

                # Filter to only valid tier1 entities
                if valid_entities:
                    filtered_entities = [e for e in raw_entities if e in valid_entities]
                    filtered_role_mapping = {k: v for k, v in raw_role_mapping.items() if k in valid_entities}

                    # Log if we filtered out garbage
                    garbage = set(raw_entities) - set(filtered_entities)
                    if garbage:
                        logger.warning(
                            f"[{article_id}] Filtered out invalid entities: {garbage}"
                        )
                else:
                    filtered_entities = []
                    filtered_role_mapping = {}

                frame = NarrativeFrame(
                    frame_type=frame_data.get("frame_type", "unknown"),
                    confidence=max(0.0, min(1.0, float(frame_data.get("confidence", 0.5)))),
                    entities=filtered_entities,
                    text_excerpt=frame_data.get("text_excerpt", ""),
                    role_mapping=filtered_role_mapping
                )
                frames.append(frame)

            # Filter entity_portrayals to valid entities only
            raw_portrayals = result.get("entity_portrayals", {})
            if valid_entities:
                filtered_portrayals = {k: v for k, v in raw_portrayals.items() if k in valid_entities}
                garbage_portrayals = set(raw_portrayals.keys()) - set(filtered_portrayals.keys())
                if garbage_portrayals:
                    logger.warning(
                        f"[{article_id}] Filtered out invalid entity_portrayals: {garbage_portrayals}"
                    )
            else:
                filtered_portrayals = {}

            # Build metrics
            narrative_metrics = NarrativeFrameMetrics(
                frames=frames,
                dominant_frame=result.get("dominant_frame"),
                entity_portrayals=filtered_portrayals,
                narrative_tension=max(0.0, min(1.0, float(result.get("narrative_tension", 0.0)))),
                propaganda_indicators=result.get("propaganda_indicators", [])
            )

            return SpecialistFindings(
                specialist_type=SpecialistType.NARRATIVE_ANALYST,
                narrative_frame_metrics=narrative_metrics,
                tokens_used=metadata.tokens_used,
                cost_usd=metadata.cost_usd,
                model=metadata.model
            )

        except json.JSONDecodeError as e:
            logger.error(f"[{article_id}] JSON parse failed in deep_dive: {e}")
            return self._empty_findings(metadata.tokens_used if 'metadata' in locals() else 0)

        except Exception as e:
            logger.error(f"[{article_id}] deep_dive failed: {e}")
            return self._empty_findings(0)

    def _empty_findings(self, tokens_used: int) -> SpecialistFindings:
        """
        Create empty findings (fallback on error).

        Args:
            tokens_used: Tokens consumed before error

        Returns:
            SpecialistFindings with empty narrative metrics
        """
        return SpecialistFindings(
            specialist_type=SpecialistType.NARRATIVE_ANALYST,
            narrative_frame_metrics=NarrativeFrameMetrics(
                frames=[],
                dominant_frame=None,
                entity_portrayals={},
                narrative_tension=0.0,
                propaganda_indicators=[]
            ),
            tokens_used=tokens_used,
            cost_usd=0.0,
            model="error-fallback"
        )
