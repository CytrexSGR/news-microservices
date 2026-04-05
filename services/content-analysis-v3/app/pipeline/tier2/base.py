"""
Tier2 Base Specialist
Abstract base class for all Tier2 specialists with 2-stage prompting
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from app.providers.base import BaseLLMProvider
from app.providers.factory import ProviderFactory
from app.core.config import settings
from .models import QuickCheckResult, SpecialistFindings, SpecialistType

logger = logging.getLogger(__name__)


class BaseSpecialist(ABC):
    """
    Abstract base class for all Tier2 specialists.

    Two-stage processing:
    1. quick_check: Fast relevance determination (~200 tokens)
    2. deep_dive: Detailed analysis (~1500 tokens)

    Budget enforcement ensures total tokens don't exceed allocation.
    """

    def __init__(self, specialist_type: SpecialistType):
        """
        Initialize specialist with provider.

        Args:
            specialist_type: Type of specialist (from SpecialistType enum)
        """
        self.specialist_type = specialist_type
        self.provider: BaseLLMProvider = ProviderFactory.create_for_tier("tier2")
        self._total_tokens_used = 0

    @abstractmethod
    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any
    ) -> QuickCheckResult:
        """
        Stage 1: Fast relevance determination.

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results object with entities, relations, topics

        Returns:
            QuickCheckResult with is_relevant flag and reasoning

        Implementation Guidelines:
        - Use tier1_results to avoid duplicate extraction
        - Keep prompt minimal (target: 200 tokens)
        - Return fast (target: < 2 seconds)
        - Be conservative: if unsure, mark as relevant
        """
        pass

    @abstractmethod
    async def deep_dive(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any,
        max_tokens: int
    ) -> SpecialistFindings:
        """
        Stage 2: Detailed analysis (only if quick_check returned True).

        Args:
            article_id: Article UUID
            title: Article title
            content: Full article content
            tier1_results: Tier1Results object
            max_tokens: Maximum tokens for this analysis

        Returns:
            SpecialistFindings with specialist-specific data

        Implementation Guidelines:
        - Use max_tokens to size your analysis
        - Build on tier1_results (don't re-extract basics)
        - Structure output for database storage
        - Track actual token usage
        """
        pass

    async def analyze(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Any,
        max_tokens: int = 1700
    ) -> Optional[SpecialistFindings]:
        """
        Two-stage analysis workflow.

        Args:
            article_id: Article UUID
            title: Article title
            content: Article content
            tier1_results: Tier1Results object
            max_tokens: Total budget for this specialist

        Returns:
            SpecialistFindings if relevant, None if skipped

        Process:
            1. Run quick_check (~200 tokens)
            2. If not relevant, return None
            3. If relevant, run deep_dive with remaining budget
        """
        logger.info(f"[{article_id}] {self.specialist_type}: Starting analysis")

        # Stage 1: Quick relevance check
        quick_result = await self.quick_check(
            article_id=article_id,
            title=title,
            content=content,
            tier1_results=tier1_results
        )

        self._total_tokens_used += quick_result.tokens_used

        if not quick_result.is_relevant:
            logger.info(
                f"[{article_id}] {self.specialist_type}: Not relevant - {quick_result.reasoning}"
            )
            return None

        # Stage 2: Deep analysis with remaining budget
        remaining_tokens = max_tokens - quick_result.tokens_used

        if remaining_tokens < 500:
            logger.warning(
                f"[{article_id}] {self.specialist_type}: Insufficient budget "
                f"({remaining_tokens} tokens remaining)"
            )
            return None

        logger.info(
            f"[{article_id}] {self.specialist_type}: Relevant (confidence={quick_result.confidence:.2f}), "
            f"proceeding to deep dive with {remaining_tokens} tokens"
        )

        findings = await self.deep_dive(
            article_id=article_id,
            title=title,
            content=content,
            tier1_results=tier1_results,
            max_tokens=remaining_tokens
        )

        self._total_tokens_used += findings.tokens_used

        logger.info(
            f"[{article_id}] {self.specialist_type}: Complete - "
            f"tokens={findings.tokens_used}, cost=${findings.cost_usd:.6f}"
        )

        return findings

    @property
    def total_tokens_used(self) -> int:
        """Total tokens consumed by this specialist."""
        return self._total_tokens_used

    def reset_token_counter(self):
        """Reset token tracking (use between articles)."""
        self._total_tokens_used = 0
