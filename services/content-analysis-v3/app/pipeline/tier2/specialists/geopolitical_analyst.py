"""
Tier2 GEOPOLITICAL_ANALYST Specialist
Analyzes geopolitical implications, conflict severity, and diplomatic impacts
"""

from uuid import UUID
from typing import Any
import logging
import json

from ..base import BaseSpecialist
from ..models import (
    QuickCheckResult,
    SpecialistFindings,
    SpecialistType,
    GeopoliticalMetrics
)
from app.models.schemas import Tier1Results

logger = logging.getLogger(__name__)


# Geopolitical keywords that trigger deep analysis
GEOPOLITICAL_KEYWORDS = {
    "CONFLICT", "POLITICS", "DIPLOMACY", "SECURITY",
    "WAR", "PEACE", "SANCTIONS", "TREATY", "MILITARY",
    "DEFENSE", "INTELLIGENCE", "ESPIONAGE", "TERRORISM",
    "ALLIANCE", "NATO", "UN", "INTERNATIONAL"
}


QUICK_CHECK_PROMPT = """Is this article geopolitically significant?

ARTICLE:
Title: {title}

TIER1 TOPICS: {topics}
TIER1 ENTITIES: {entities}

INSTRUCTIONS:
- Check if topics include: CONFLICT, POLITICS, DIPLOMACY, SECURITY
- Check if entities involve countries, international organizations, military
- Look for international relations, conflicts, treaties, sanctions

OUTPUT (JSON):
{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation why relevant/not"
}}

Respond with ONLY the JSON object."""


DEEP_DIVE_PROMPT = """Analyze geopolitical implications of this article.

ARTICLE:
Title: {title}
Content: {content}

TIER1 CONTEXT:
Entities: {entities}
Relations: {relations}
Topics: {topics}

OUTPUT (JSON):
{{
  "metrics": {{
    "conflict_severity": 0.0-10.0,
    "diplomatic_impact": 0.0-10.0,
    "regional_stability_risk": 0.0-10.0,
    "international_attention": 0.0-10.0,
    "economic_implications": 0.0-10.0
  }},
  "countries_involved": ["Country1", "Country2"],
  "relations": [
    {{
      "subject": "Entity/Country",
      "predicate": "OPPOSES|SUPPORTS|NEGOTIATES|CONDEMNS|ALLIES",
      "object": "Entity/Country",
      "confidence": 0.0-1.0
    }}
  ]
}}

METRIC DEFINITIONS:

**conflict_severity (0.0-10.0):**
- 0-2: Diplomatic tensions, verbal disputes
- 3-5: Sanctions, trade restrictions, military posturing
- 6-8: Limited military engagement, proxy conflicts
- 9-10: Full-scale war, existential threats

**diplomatic_impact (0.0-10.0):**
- 0-2: Routine diplomatic activity
- 3-5: Significant bilateral negotiations
- 6-8: Major international summits, treaty discussions
- 9-10: Historic agreements, major alliance shifts

**regional_stability_risk (0.0-10.0):**
- 0-2: Stable situation, minimal disruption
- 3-5: Localized tensions, potential spillover
- 6-8: Regional crisis, multiple nations affected
- 9-10: Systemic collapse risk, mass migration

**international_attention (0.0-10.0):**
- 0-2: Local/regional interest only
- 3-5: Some international media coverage
- 6-8: Major international focus, UN involvement
- 9-10: Global crisis, emergency security council meetings

**economic_implications (0.0-10.0):**
- 0-2: Minimal economic impact
- 3-5: Trade disruptions, specific sectors affected
- 6-8: Regional economic consequences, market volatility
- 9-10: Global economic shock, major sanctions regime

RELATIONS:
- Extract key geopolitical relationships (OPPOSES, SUPPORTS, ALLIES, CONDEMNS, etc.)
- Focus on international relations, not domestic politics
- Include confidence scores based on explicitness in article

COUNTRIES_INVOLVED:
- List all countries/regions directly mentioned in geopolitical context
- Include international organizations if relevant (NATO, UN, EU, etc.)

Respond with ONLY the JSON object. Focus on international significance."""


class GeopoliticalAnalyst(BaseSpecialist):
    """
    GEOPOLITICAL_ANALYST specialist for Tier2.

    Analyzes articles with geopolitical significance including:
    - International conflicts and wars
    - Diplomatic relations and negotiations
    - Security alliances and treaties
    - Sanctions and international law
    - Regional stability assessments

    Two-stage process:
    1. quick_check: Fast relevance determination (~200 tokens)
    2. deep_dive: Detailed geopolitical analysis (~1500 tokens)
    """

    def __init__(self):
        """Initialize GEOPOLITICAL_ANALYST specialist."""
        super().__init__(specialist_type=SpecialistType.GEOPOLITICAL_ANALYST)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results
    ) -> QuickCheckResult:
        """
        Stage 1: Fast relevance determination for geopolitical content.

        Checks if article contains geopolitical keywords in topics or
        involves countries/international organizations in entities.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content (not used in quick check)
            tier1_results: Tier1Results with topics and entities

        Returns:
            QuickCheckResult with relevance decision
        """
        logger.info(f"[{article_id}] {self.specialist_type}: Quick check starting")

        # Extract topics and entities from Tier1 results
        topics_str = ", ".join([t.keyword for t in tier1_results.topics])
        entities_str = ", ".join([
            f"{e.name} ({e.type})"
            for e in tier1_results.entities[:10]  # Limit to first 10
        ])

        # Check for geopolitical keywords in topics
        has_geopolitical_topics = any(
            keyword in topic.keyword.upper()
            for topic in tier1_results.topics
            for keyword in GEOPOLITICAL_KEYWORDS
        )

        # Prepare quick check prompt
        prompt = QUICK_CHECK_PROMPT.format(
            title=title,
            topics=topics_str or "None",
            entities=entities_str or "None"
        )

        # Generate quick check response
        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.0
        )

        # Parse JSON response
        try:
            result_data = json.loads(response_text)

            # Apply minimum confidence boost if geopolitical topics detected
            confidence = result_data.get("confidence", 0.5)
            if has_geopolitical_topics and result_data.get("is_relevant", False):
                confidence = max(confidence, 0.7)  # Boost confidence

            result = QuickCheckResult(
                is_relevant=result_data.get("is_relevant", False),
                confidence=confidence,
                reasoning=result_data.get("reasoning", "No reasoning provided"),
                tokens_used=metadata.tokens_used
            )

            logger.info(
                f"[{article_id}] {self.specialist_type}: Quick check complete - "
                f"relevant={result.is_relevant}, confidence={result.confidence:.2f}"
            )

            return result

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"[{article_id}] {self.specialist_type}: Failed to parse quick check response - {e}"
            )
            # Fallback: Use topic-based heuristic
            return QuickCheckResult(
                is_relevant=has_geopolitical_topics,
                confidence=0.6 if has_geopolitical_topics else 0.3,
                reasoning="Fallback: Based on topic keyword detection",
                tokens_used=metadata.tokens_used
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
        Stage 2: Detailed geopolitical analysis.

        Extracts comprehensive geopolitical metrics including conflict severity,
        diplomatic impact, regional stability, and international relations.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, relations, topics
            max_tokens: Maximum tokens for this analysis

        Returns:
            SpecialistFindings with geopolitical_metrics populated
        """
        logger.info(
            f"[{article_id}] {self.specialist_type}: Deep dive starting "
            f"(budget={max_tokens} tokens)"
        )

        # Prepare context from Tier1
        entities_context = json.dumps([
            {"name": e.name, "type": e.type, "mentions": e.mentions}
            for e in tier1_results.entities[:15]  # Top 15 entities
        ], indent=2)

        relations_context = json.dumps([
            {"subject": r.subject, "predicate": r.predicate, "object": r.object}
            for r in tier1_results.relations[:10]  # Top 10 relations
        ], indent=2)

        topics_context = ", ".join([t.keyword for t in tier1_results.topics])

        # Prepare deep dive prompt
        prompt = DEEP_DIVE_PROMPT.format(
            title=title,
            content=content[:3000],  # Truncate to avoid token overflow
            entities=entities_context,
            relations=relations_context,
            topics=topics_context or "None"
        )

        # Generate deep analysis
        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.0
        )

        # Parse JSON response
        try:
            analysis_data = json.loads(response_text)

            # Extract metrics (with defaults)
            metrics_dict = analysis_data.get("metrics", {})

            # Extract countries and relations
            countries_involved = analysis_data.get("countries_involved", [])
            relations_data = analysis_data.get("relations", [])

            # Create GeopoliticalMetrics
            geopolitical_metrics = GeopoliticalMetrics(
                metrics=metrics_dict,
                countries_involved=countries_involved,
                relations=relations_data
            )

            # Create SpecialistFindings
            findings = SpecialistFindings(
                specialist_type=self.specialist_type,
                geopolitical_metrics=geopolitical_metrics,
                tokens_used=metadata.tokens_used,
                cost_usd=metadata.cost_usd,
                model=metadata.model
            )

            logger.info(
                f"[{article_id}] {self.specialist_type}: Deep dive complete - "
                f"conflict_severity={metrics_dict.get('conflict_severity', 0):.1f}, "
                f"countries={len(countries_involved)}, "
                f"relations={len(relations_data)}, "
                f"tokens={metadata.tokens_used}"
            )

            return findings

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"[{article_id}] {self.specialist_type}: Failed to parse deep dive response - {e}"
            )
            # Return empty findings with metadata
            return SpecialistFindings(
                specialist_type=self.specialist_type,
                geopolitical_metrics=GeopoliticalMetrics(
                    metrics={},
                    countries_involved=[],
                    relations=[]
                ),
                tokens_used=metadata.tokens_used,
                cost_usd=metadata.cost_usd,
                model=metadata.model
            )
