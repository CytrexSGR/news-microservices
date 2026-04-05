"""
Tier2 ENTITY_EXTRACTOR Specialist
Enhances Tier1 entities with additional contextual details
"""

import json
import logging
from typing import Any
from uuid import UUID

from app.pipeline.tier2.base import BaseSpecialist
from app.pipeline.tier2.models import (
    SpecialistType,
    QuickCheckResult,
    SpecialistFindings,
    EntityEnrichment
)
from app.models.schemas import Tier1Results

logger = logging.getLogger(__name__)


class EntityExtractorSpecialist(BaseSpecialist):
    """
    ENTITY_EXTRACTOR Specialist - Enhances Tier1 entities with contextual details.

    Stage 1 (quick_check):
        - Determines if entities need enrichment
        - Uses Tier1 entity list for decision

    Stage 2 (deep_dive):
        - Extracts enhanced entity details (company info, person roles, etc.)
        - Enriches with industry, stock symbols, positions, etc.
    """

    def __init__(self):
        """Initialize ENTITY_EXTRACTOR specialist."""
        super().__init__(SpecialistType.ENTITY_EXTRACTOR)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results
    ) -> QuickCheckResult:
        """
        Stage 1: Determine if entities need enrichment.

        Args:
            article_id: Article UUID
            title: Article title
            content: Article content (not used in quick check)
            tier1_results: Tier1 results containing basic entities

        Returns:
            QuickCheckResult indicating if deep_dive should run
        """
        # Extract entity names from Tier1
        entity_list = [
            f"{e.name} ({e.type})" for e in tier1_results.entities
        ] if tier1_results.entities else []

        if not entity_list:
            # No entities to enrich
            return QuickCheckResult(
                is_relevant=False,
                confidence=1.0,
                reasoning="No entities found in Tier1 results",
                tokens_used=0
            )

        entities_str = ", ".join(entity_list[:10])  # Limit to first 10
        if len(tier1_results.entities) > 10:
            entities_str += f" ... and {len(tier1_results.entities) - 10} more"

        prompt = f"""Do the entities in this article need enrichment (company details, person roles, location context)?

ARTICLE TITLE: {title}

TIER1 ENTITIES: {entities_str}

Answer with YES or NO followed by a brief reason (one sentence).

Examples:
- "YES - Contains organizations (Tesla Inc, SpaceX) that need industry/stock details"
- "NO - Only generic locations with no additional context needed"
- "YES - Contains persons (Elon Musk) that need role/position information"
"""

        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1
            )

            response_clean = response_text.strip().upper()
            is_relevant = response_clean.startswith("YES")

            # Extract reasoning (everything after YES/NO)
            reasoning = response_text.strip()
            if reasoning.startswith("YES") or reasoning.startswith("NO"):
                reasoning = reasoning[3:].strip(" -:").strip()

            if not reasoning:
                reasoning = "Entity enrichment decision made"

            return QuickCheckResult(
                is_relevant=is_relevant,
                confidence=0.9 if is_relevant else 0.95,
                reasoning=reasoning,
                tokens_used=metadata.tokens_used
            )

        except Exception as e:
            logger.error(
                f"[{article_id}] ENTITY_EXTRACTOR quick_check failed: {e}",
                exc_info=True
            )
            # Conservative fallback: assume relevant if check fails
            return QuickCheckResult(
                is_relevant=True,
                confidence=0.5,
                reasoning=f"Quick check failed, assuming relevant: {str(e)}",
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
        Stage 2: Extract enhanced entity details.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1 results with basic entities
            max_tokens: Token budget for this analysis

        Returns:
            SpecialistFindings with entity_enrichment populated
        """
        # Build Tier1 entity context
        tier1_entities_json = [
            {
                "name": e.name,
                "type": e.type,
                "confidence": e.confidence,
                "mentions": e.mentions
            }
            for e in tier1_results.entities
        ] if tier1_results.entities else []

        # Truncate content to first 1000 chars for context
        content_excerpt = content[:1000] + ("..." if len(content) > 1000 else "")

        prompt = f"""Provide essential information for entities in this article.

ARTICLE:
Title: {title}
Content: {content_excerpt}

TIER1 ENTITIES: {json.dumps(tier1_entities_json, indent=2)}

OUTPUT (strict JSON format):
{{
  "entities": [
    {{
      "name": "Tesla Inc",
      "type": "ORGANIZATION",
      "details": {{
        "industry": "Automotive",
        "stock_symbol": "TSLA"
      }}
    }},
    {{
      "name": "Elon Musk",
      "type": "PERSON",
      "details": {{
        "role": "CEO",
        "affiliation": "Tesla, SpaceX"
      }}
    }},
    {{
      "name": "Berlin",
      "type": "LOCATION",
      "details": {{
        "country": "Germany",
        "region": "Central Europe"
      }}
    }}
  ]
}}

RULES:
1. Enrich ONLY entities from TIER1 list
2. Add only essential contextual details
3. For ORGANIZATION: industry, stock_symbol (if publicly traded)
4. For PERSON: role, affiliation (company/organization)
5. For LOCATION: country, region (geographic region)
6. For EVENT: date, location, participants
7. Use null for unknown fields
8. Keep details concise and factual
9. Output ONLY valid JSON, no additional text

STRICT JSON OUTPUT:"""

        try:
            response_text, metadata = await self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.1
            )

            # Parse JSON response
            response_clean = response_text.strip()

            # Extract JSON if wrapped in markdown code blocks
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()

            try:
                enriched_data = json.loads(response_clean)
                entities = enriched_data.get("entities", [])
            except json.JSONDecodeError as e:
                logger.warning(
                    f"[{article_id}] ENTITY_EXTRACTOR: Failed to parse JSON: {e}. "
                    f"Response: {response_clean[:200]}"
                )
                entities = []

            return SpecialistFindings(
                specialist_type=SpecialistType.ENTITY_EXTRACTOR,
                entity_enrichment=EntityEnrichment(entities=entities),
                tokens_used=metadata.tokens_used,
                cost_usd=metadata.cost_usd,
                model=metadata.model
            )

        except Exception as e:
            logger.error(
                f"[{article_id}] ENTITY_EXTRACTOR deep_dive failed: {e}",
                exc_info=True
            )
            # Return empty findings on error
            return SpecialistFindings(
                specialist_type=SpecialistType.ENTITY_EXTRACTOR,
                entity_enrichment=EntityEnrichment(entities=[]),
                tokens_used=0,
                cost_usd=0.0,
                model=self.provider.model
            )
