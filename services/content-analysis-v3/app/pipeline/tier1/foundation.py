"""
Tier 1: Foundation Extraction Module
Extracts entities, relations, topics, and scores from article content
Budget: 2000 tokens, Cost: ~$0.00007/article
"""

import asyncpg
from uuid import UUID
from typing import Optional, List
import logging
import json

from app.models.schemas import Tier1Results, Entity, Relation, Topic
from app.providers.factory import ProviderFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


def _sanitize_tier1_response(response_json: dict) -> dict:
    """
    Sanitize Tier1 JSON response by removing None values.

    OpenAI sometimes returns None values in relations/entities which break Pydantic validation.
    This function filters out invalid items before validation.

    Args:
        response_json: Raw JSON dict from OpenAI

    Returns:
        Sanitized JSON dict with None values filtered out
    """
    # Filter entities with None values
    if "entities" in response_json and isinstance(response_json["entities"], list):
        response_json["entities"] = [
            entity for entity in response_json["entities"]
            if entity.get("name") is not None and entity.get("type") is not None
        ]

    # Filter relations with None values in subject/predicate/object
    if "relations" in response_json and isinstance(response_json["relations"], list):
        response_json["relations"] = [
            relation for relation in response_json["relations"]
            if (relation.get("subject") is not None and
                relation.get("predicate") is not None and
                relation.get("object") is not None)
        ]

    # Filter topics with None values
    if "topics" in response_json and isinstance(response_json["topics"], list):
        response_json["topics"] = [
            topic for topic in response_json["topics"]
            if topic.get("keyword") is not None
        ]

    return response_json


TIER1_PROMPT_TEMPLATE = """Extract structured information from this article.

ARTICLE:
Title: {title}
URL: {url}
Content: {content}

OUTPUT (JSON):
{{
  "entities": [
    {{"name": "entity name", "type": "PERSON|ORGANIZATION|LOCATION|EVENT", "confidence": 0.0-1.0, "mentions": 1, "aliases": [], "role": null}}
  ],
  "relations": [
    {{"subject": "entity1", "predicate": "relationship", "object": "entity2", "confidence": 0.0-1.0}}
  ],
  "topics": [
    {{"keyword": "FINANCE", "confidence": 0.0-1.0, "parent_category": "Economic"}}
  ],
  "impact_score": 0.0-10.0,
  "credibility_score": 0.0-10.0,
  "urgency_score": 0.0-10.0
}}

INSTRUCTIONS:

**ENTITIES:**
- Extract key entities mentioned in the article
- Types: PERSON (individuals), ORGANIZATION (companies, agencies), LOCATION (countries, cities), EVENT (specific events)
- Provide confidence score (0.9-1.0 for explicit mentions, 0.7-0.8 for strong context, 0.5-0.6 for implied)
- Count total mentions for each entity
- Optional: Add aliases (alternative names) and role (position/function) if known
- Only extract entities with clear relevance to the article's main topic

**RELATIONS:**
- Extract Subject-Predicate-Object triplets showing relationships
- Subject/Object should be entity names (prefer entities from entities list)
- Predicate should be a clear action/relationship verb
- Confidence: 0.9-1.0 (explicit statement), 0.7-0.8 (strong implication), 0.5-0.6 (weak/uncertain)
- Extract 3-10 most important relations (quality over quantity)

**TOPICS:**
- Classify article into relevant router keywords
- Keyword should be uppercase category: FINANCE, CONFLICT, POLITICS, SECURITY, TECHNOLOGY, HUMANITARIAN, etc.
- Parent category groups related keywords
- Confidence based on how central the topic is to the article
- Include 2-5 topics maximum

**SCORES:**
- impact_score (0.0-10.0): How significant is this for global markets/politics?
  - 0-3: Local/niche impact
  - 4-6: Regional significance
  - 7-8: National importance
  - 9-10: Global/market-moving event

- credibility_score (0.0-10.0): How reliable is the source?
  - 0-3: Unverified claims, questionable source
  - 4-6: Mainstream media, some verification
  - 7-8: Established news outlets, multiple sources
  - 9-10: Official statements, primary sources

- urgency_score (0.0-10.0): How time-sensitive is this information?
  - 0-3: Background/analysis, no time pressure
  - 4-6: Recent development, moderate time sensitivity
  - 7-8: Breaking news, developing situation
  - 9-10: Critical alert, immediate action required

Respond with ONLY the JSON object. No explanations."""


class Tier1Foundation:
    """Tier 1: Foundation extraction - entities, relations, topics, scores."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.provider = ProviderFactory.create_for_tier("tier1")

    async def execute(
        self,
        article_id: UUID,
        title: str,
        url: str,
        content: str
    ) -> Tier1Results:
        """
        Execute Tier1 foundation extraction on article.

        Args:
            article_id: Article UUID
            title: Article title
            url: Article URL
            content: Full article content

        Returns:
            Tier1Results with entities, relations, topics, and scores

        Raises:
            ProviderError: If LLM call fails
        """

        logger.info(f"[{article_id}] Starting Tier1 foundation extraction")

        # Prepare prompt
        prompt = TIER1_PROMPT_TEMPLATE.format(
            title=title,
            url=url,
            content=content
        )

        # Generate extraction
        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=settings.V3_TIER1_MAX_TOKENS,
            response_format=Tier1Results,
            temperature=0.0
        )

        # Parse and sanitize response (remove None values from OpenAI)
        response_json = json.loads(response_text)
        sanitized_json = _sanitize_tier1_response(response_json)
        results = Tier1Results.model_validate(sanitized_json)
        results.tokens_used = metadata.tokens_used
        results.cost_usd = metadata.cost_usd
        results.model = metadata.model

        # NOTE: No direct DB storage - data is stored via event publishing
        # in request_consumer.py -> analysis.v3.completed event -> feed-service
        # -> article_analysis table (unified table)

        logger.info(
            f"[{article_id}] Tier1 complete: "
            f"entities={len(results.entities)}, "
            f"relations={len(results.relations)}, "
            f"topics={len(results.topics)}, "
            f"impact={results.impact_score}, "
            f"cost=${results.cost_usd:.6f}"
        )

        return results

    # REMOVED: Legacy _store_results() and get_results() methods
    # These referenced non-existent tier1_entities, tier1_relations, tier1_topics, tier1_scores tables.
    # V3 data is now stored via event-driven architecture:
    # - Tier1 executes and returns Tier1Results object
    # - request_consumer.py publishes analysis.v3.completed event
    # - feed-service analysis_consumer stores in article_analysis table
