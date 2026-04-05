"""
Tier2 Orchestrator
Coordinates all 5 specialists with intelligent budget management
"""

import asyncpg
from uuid import UUID
from typing import Optional, Dict, Any, List
import logging

from app.models.schemas import Tier1Results
from app.core.config import settings
from .models import SpecialistType, SpecialistFindings
from .specialists.topic_classifier import TopicClassifierSpecialist
from .specialists.entity_extractor import EntityExtractorSpecialist
from .specialists.financial_analyst import FinancialAnalyst
from .specialists.geopolitical_analyst import GeopoliticalAnalyst
from .specialists.sentiment_analyzer import SentimentAnalyzerSpecialist
from .specialists.bias_scorer import BiasScorer
from .specialists.narrative_analyst import NarrativeAnalyst

logger = logging.getLogger(__name__)


# Specialist token budget weights (relative importance)
# Higher weight = more tokens allocated
SPECIALIST_WEIGHTS = {
    SpecialistType.FINANCIAL_ANALYST: 1.5,      # Needs more for detailed market analysis
    SpecialistType.GEOPOLITICAL_ANALYST: 1.3,  # Complex relationship analysis
    SpecialistType.NARRATIVE_ANALYST: 1.3,     # Frame detection needs context
    SpecialistType.ENTITY_EXTRACTOR: 1.2,      # May have many entities to enrich
    SpecialistType.SENTIMENT_ANALYZER: 1.0,    # Standard analysis
    SpecialistType.TOPIC_CLASSIFIER: 0.8,      # Simpler classification task
    SpecialistType.BIAS_SCORER: 0.7,           # Focused scoring task
}


class Tier2Results:
    """
    Aggregated results from all Tier2 specialists.

    This class collects findings from all active specialists and tracks
    aggregate metrics (tokens, cost, active specialists).

    Attributes:
        topic_classification: Findings from TopicClassifierSpecialist
        entity_enrichment: Findings from EntityExtractorSpecialist
        financial_metrics: Findings from FinancialAnalyst
        geopolitical_metrics: Findings from GeopoliticalAnalyst
        sentiment_metrics: Findings from SentimentAnalyzerSpecialist
        political_bias: Findings from BiasScorer
        total_tokens_used: Sum of tokens across all specialists
        total_cost_usd: Sum of costs across all specialists
        active_specialists: List of specialist names that were executed
    """

    def __init__(self):
        """Initialize empty results container."""
        self.topic_classification: Optional[SpecialistFindings] = None
        self.entity_enrichment: Optional[SpecialistFindings] = None
        self.financial_metrics: Optional[SpecialistFindings] = None
        self.geopolitical_metrics: Optional[SpecialistFindings] = None
        self.sentiment_metrics: Optional[SpecialistFindings] = None
        self.political_bias: Optional[SpecialistFindings] = None
        self.narrative_frame_metrics: Optional[SpecialistFindings] = None

        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.active_specialists: List[str] = []

    def add_findings(self, findings: SpecialistFindings):
        """
        Add specialist findings and update totals.

        Args:
            findings: SpecialistFindings from a completed specialist analysis
        """
        specialist_type = findings.specialist_type

        if specialist_type == SpecialistType.TOPIC_CLASSIFIER:
            self.topic_classification = findings
        elif specialist_type == SpecialistType.ENTITY_EXTRACTOR:
            self.entity_enrichment = findings
        elif specialist_type == SpecialistType.FINANCIAL_ANALYST:
            self.financial_metrics = findings
        elif specialist_type == SpecialistType.GEOPOLITICAL_ANALYST:
            self.geopolitical_metrics = findings
        elif specialist_type == SpecialistType.SENTIMENT_ANALYZER:
            self.sentiment_metrics = findings
        elif specialist_type == SpecialistType.BIAS_SCORER:
            self.political_bias = findings
        elif specialist_type == SpecialistType.NARRATIVE_ANALYST:
            self.narrative_frame_metrics = findings

        self.total_tokens_used += findings.tokens_used
        self.total_cost_usd += findings.cost_usd
        self.active_specialists.append(specialist_type.value)


class Tier2Orchestrator:
    """
    Coordinates all Tier2 specialists with intelligent budget management.

    Budget Allocation Strategy:
    - Total budget: 8000 tokens across 6 specialists
    - Base allocation: ~1333 tokens per specialist
    - Redistribution: Unused tokens from skipped specialists → active specialists
    - Two-stage prompting saves ~94.5% on irrelevant articles
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

        # Initialize all specialists
        self.specialists = {
            SpecialistType.TOPIC_CLASSIFIER: TopicClassifierSpecialist(),
            SpecialistType.ENTITY_EXTRACTOR: EntityExtractorSpecialist(),
            SpecialistType.FINANCIAL_ANALYST: FinancialAnalyst(),
            SpecialistType.GEOPOLITICAL_ANALYST: GeopoliticalAnalyst(),
            SpecialistType.SENTIMENT_ANALYZER: SentimentAnalyzerSpecialist(),
            SpecialistType.BIAS_SCORER: BiasScorer(),
            SpecialistType.NARRATIVE_ANALYST: NarrativeAnalyst()
        }

        self.total_budget = settings.V3_TIER2_MAX_TOKENS
        self.base_allocation = self.total_budget // len(self.specialists)

    async def analyze_article(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results
    ) -> Tier2Results:
        """
        Coordinate all specialists with budget enforcement.

        Process:
        1. Phase 1: Run all quick_checks to determine relevance
        2. Calculate budget redistribution from skipped specialists
        3. Phase 2: Run deep_dives for relevant specialists
        4. Store results in database
        5. Return aggregated Tier2Results

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results with entities, relations, topics

        Returns:
            Tier2Results with all specialist findings
        """
        logger.info(
            f"[{article_id}] Tier2 Orchestrator: Starting analysis with "
            f"{len(self.specialists)} specialists, budget={self.total_budget} tokens"
        )

        results = Tier2Results()

        # Phase 1: Run all quick_checks
        logger.info(f"[{article_id}] Tier2 Phase 1: Running quick checks")

        relevant_specialists = []
        quick_check_tokens = 0

        for specialist_type, specialist in self.specialists.items():
            quick_result = await specialist.quick_check(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results
            )

            quick_check_tokens += quick_result.tokens_used

            if quick_result.is_relevant:
                relevant_specialists.append((specialist_type, specialist))
                logger.info(
                    f"[{article_id}] {specialist_type.value}: Relevant "
                    f"(confidence={quick_result.confidence:.2f})"
                )
            else:
                logger.info(
                    f"[{article_id}] {specialist_type.value}: Skipped - "
                    f"{quick_result.reasoning}"
                )

        # Calculate budget redistribution
        num_active = len(relevant_specialists)
        num_skipped = len(self.specialists) - num_active

        if num_active == 0:
            logger.info(
                f"[{article_id}] Tier2: No relevant specialists found, "
                f"quick check tokens={quick_check_tokens}"
            )
            results.total_tokens_used = quick_check_tokens
            return results

        # Calculate weighted budget redistribution
        remaining_budget = self.total_budget - quick_check_tokens
        total_weight = sum(
            SPECIALIST_WEIGHTS.get(st, 1.0)
            for st, _ in relevant_specialists
        )
        tokens_per_unit = remaining_budget / total_weight

        # Calculate per-specialist token allocation
        token_allocations = {
            st: int(tokens_per_unit * SPECIALIST_WEIGHTS.get(st, 1.0))
            for st, _ in relevant_specialists
        }

        logger.info(
            f"[{article_id}] Tier2 Phase 2: Running {num_active} deep dives, "
            f"weighted_allocation={token_allocations}, "
            f"skipped={num_skipped}, "
            f"quick_check_tokens={quick_check_tokens}"
        )

        # Phase 2: Run deep_dives for relevant specialists with weighted tokens
        for specialist_type, specialist in relevant_specialists:
            allocated_tokens = token_allocations[specialist_type]
            findings = await specialist.analyze(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results,
                max_tokens=allocated_tokens
            )

            if findings:
                results.add_findings(findings)
                logger.info(
                    f"[{article_id}] {specialist_type.value}: Complete - "
                    f"tokens={findings.tokens_used}, cost=${findings.cost_usd:.6f}"
                )

        # Add quick check tokens to total
        results.total_tokens_used += quick_check_tokens

        # NOTE: No direct DB storage - data is stored via event publishing
        # in request_consumer.py -> analysis.v3.completed event -> feed-service
        # -> article_analysis table (unified table)

        logger.info(
            f"[{article_id}] Tier2 Orchestrator: Complete - "
            f"active_specialists={num_active}/{len(self.specialists)}, "
            f"total_tokens={results.total_tokens_used}, "
            f"total_cost=${results.total_cost_usd:.6f}"
        )

        return results

    # REMOVED: Legacy _store_results() and get_results() methods
    # These referenced non-existent tier2_specialist_results table.
    # V3 data is now stored via event-driven architecture:
    # - Tier2 executes and returns Tier2Results object
    # - request_consumer.py publishes analysis.v3.completed event
    # - feed-service analysis_consumer stores in article_analysis table
