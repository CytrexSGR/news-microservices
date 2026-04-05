"""
DIA (Dynamic Intelligence Augmentation) Planner

Two-stage planning process:
1. Stage 1: Diagnosis Refinement (Root Cause Analysis)
2. Stage 2: Plan Generation (Verification Strategy)

Related: ADR-018 (DIA-Planner & Verifier)
"""

import json
import logging
from typing import Tuple
from openai import OpenAI

# Import from project root models
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import (
    VerificationRequiredEvent,
    ProblemHypothesis
)
from models.adversarial_test_case import VerificationPlan

from app.core.config import settings
from app.core.prompts import STAGE_1_SYSTEM_PROMPT, STAGE_2_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DIAPlanner:
    """
    Two-stage DIA planning: Diagnosis → Plan

    The planner compensates for imprecise UQ sensor output by:
    1. Using LLM to perform precise root cause analysis
    2. Generating structured verification plans based on diagnosis
    """

    def __init__(self):
        """Initialize DIA Planner with OpenAI client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.stage1_temperature = settings.DIA_STAGE1_TEMPERATURE
        self.stage2_temperature = settings.DIA_STAGE2_TEMPERATURE
        self.max_retries = settings.DIA_MAX_RETRIES

        logger.info(
            f"[DIAPlanner] Initialized with model={self.model}, "
            f"stage1_temp={self.stage1_temperature}, "
            f"stage2_temp={self.stage2_temperature}"
        )

    async def process_verification_request(
        self,
        event: VerificationRequiredEvent
    ) -> Tuple[ProblemHypothesis, VerificationPlan]:
        """
        Execute two-stage planning process.

        Args:
            event: Verification required event from content-analysis-service

        Returns:
            Tuple of (problem_hypothesis, verification_plan)

        Raises:
            ValueError: If LLM returns invalid JSON
            Exception: If LLM calls fail after retries
        """
        logger.info(
            f"[DIAPlanner] Processing verification request for "
            f"article_id={event.article_id}, "
            f"uq_score={event.uq_confidence_score:.2f}"
        )

        # =====================================================================
        # Stage 1: Root Cause Analysis
        # =====================================================================
        logger.info("[DIAPlanner] Stage 1: Analyzing root cause...")
        problem_hypothesis = await self._diagnose_root_cause(event)

        logger.info(
            f"[DIAPlanner] Stage 1 Complete: "
            f"hypothesis_type={problem_hypothesis.hypothesis_type}, "
            f"confidence={problem_hypothesis.confidence:.2f}"
        )
        logger.debug(f"[DIAPlanner] Primary concern: {problem_hypothesis.primary_concern}")

        # =====================================================================
        # Stage 2: Plan Generation
        # =====================================================================
        logger.info("[DIAPlanner] Stage 2: Generating verification plan...")
        verification_plan = await self._generate_plan(
            problem_hypothesis=problem_hypothesis,
            event=event
        )

        logger.info(
            f"[DIAPlanner] Stage 2 Complete: "
            f"priority={verification_plan.priority}, "
            f"methods={len(verification_plan.verification_methods)}, "
            f"sources={len(verification_plan.external_sources)}"
        )

        logger.info("[DIAPlanner] Two-stage planning completed successfully")
        return problem_hypothesis, verification_plan

    async def _diagnose_root_cause(
        self,
        event: VerificationRequiredEvent
    ) -> ProblemHypothesis:
        """
        Stage 1: Root Cause Analysis

        Transforms vague uncertainty factors into precise problem hypothesis.

        Args:
            event: Verification required event

        Returns:
            ProblemHypothesis with precise diagnosis
        """
        # Build user prompt with context
        user_prompt = self._build_stage1_prompt(event)

        # Call LLM with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"[Stage 1] LLM call attempt {attempt}/{self.max_retries}")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": STAGE_1_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.stage1_temperature,
                    max_tokens=1000
                )

                # Parse response
                hypothesis_data = json.loads(response.choices[0].message.content)

                # Validate and create Pydantic model
                hypothesis = ProblemHypothesis(**hypothesis_data)

                logger.info(
                    f"[Stage 1] Root cause identified: {hypothesis.hypothesis_type} "
                    f"(confidence: {hypothesis.confidence:.2f})"
                )

                return hypothesis

            except json.JSONDecodeError as e:
                logger.error(f"[Stage 1] JSON parse error (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise ValueError(f"Failed to parse LLM response after {self.max_retries} attempts")

            except Exception as e:
                logger.error(f"[Stage 1] Error (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise

        raise Exception("Unexpected error in Stage 1")

    async def _generate_plan(
        self,
        problem_hypothesis: ProblemHypothesis,
        event: VerificationRequiredEvent
    ) -> VerificationPlan:
        """
        Stage 2: Plan Generation

        Creates structured verification plan based on precise diagnosis.

        Args:
            problem_hypothesis: Diagnosis from Stage 1
            event: Original verification request

        Returns:
            VerificationPlan with actionable steps
        """
        # Build user prompt with hypothesis and context
        user_prompt = self._build_stage2_prompt(problem_hypothesis, event)

        # Call LLM with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"[Stage 2] LLM call attempt {attempt}/{self.max_retries}")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": STAGE_2_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.stage2_temperature,
                    max_tokens=1500
                )

                # Parse response
                plan_data = json.loads(response.choices[0].message.content)

                # Validate and create Pydantic model
                plan = VerificationPlan(**plan_data)

                logger.info(
                    f"[Stage 2] Plan generated: {len(plan.verification_methods)} methods, "
                    f"priority={plan.priority}"
                )

                return plan

            except json.JSONDecodeError as e:
                logger.error(f"[Stage 2] JSON parse error (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise ValueError(f"Failed to parse LLM response after {self.max_retries} attempts")

            except Exception as e:
                logger.error(f"[Stage 2] Error (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise

        raise Exception("Unexpected error in Stage 2")

    def _build_stage1_prompt(self, event: VerificationRequiredEvent) -> str:
        """
        Build user prompt for Stage 1 (Root Cause Analysis).

        Args:
            event: Verification required event

        Returns:
            Formatted prompt string
        """
        # Format uncertainty factors as bullet list
        factors_formatted = "\n".join(f"  - {f}" for f in event.uncertainty_factors)

        # Truncate content if too long (keep first 2000 chars)
        content_preview = event.article_content
        if len(content_preview) > 2000:
            content_preview = content_preview[:2000] + "\n...[truncated]"

        prompt = f"""
Article Content:
Title: {event.article_title}
URL: {event.article_url}
Published: {event.article_published_at}

{content_preview}

UQ Sensor Output:
- Confidence Score: {event.uq_confidence_score} (lower = more uncertain)
- Uncertainty Factors:
{factors_formatted}

Current Analysis (potentially incorrect):
- Summary: {event.analysis_summary or 'N/A'}
- Entities: {len(event.extracted_entities or [])} extracted
- Category: {event.category_analysis or 'N/A'}

Task: Identify the precise root cause of uncertainty. What EXACTLY is the problem?
"""

        return prompt.strip()

    def _build_stage2_prompt(
        self,
        problem_hypothesis: ProblemHypothesis,
        event: VerificationRequiredEvent
    ) -> str:
        """
        Build user prompt for Stage 2 (Plan Generation).

        Args:
            problem_hypothesis: Diagnosis from Stage 1
            event: Original verification request

        Returns:
            Formatted prompt string
        """
        prompt = f"""
Problem Hypothesis (from Stage 1 Root Cause Analysis):
{problem_hypothesis.model_dump_json(indent=2)}

Original Article Context:
- Title: {event.article_title}
- URL: {event.article_url}
- Published: {event.article_published_at}
- Priority: {event.priority}

Available Tools:
- perplexity_deep_search(query: str) - Deep web search
- internal_knowledge_search(query: str) - Search our article database
- fact_check_claim(claim: str) - Fact-checking databases
- entity_lookup(entity_name: str, entity_type: str) - Resolve entity identity
- temporal_verification(event: str, date: str) - Verify timeline
- financial_data_lookup(company: str, metric: str, period: str) - Financial data

Task: Create a precise, executable verification plan to confirm/refute this hypothesis.
Focus on the most authoritative sources. Be specific with tool parameters.
"""

        return prompt.strip()

    def _get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for prompt."""
        return """
- perplexity_deep_search(query: str) - Deep web search with citations
- internal_knowledge_search(query: str) - Search internal article database
- fact_check_claim(claim: str) - Check against fact-checking databases
- entity_lookup(entity_name: str, entity_type: str) - Resolve entity identity
- temporal_verification(event: str, date: str) - Verify event timeline
- financial_data_lookup(company: str, metric: str, period: str) - Query financial databases
"""


# For testing/debugging
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    from uuid import uuid4

    async def test_planner():
        """Test the DIA Planner with a sample event."""

        # Create test event
        event = VerificationRequiredEvent(
            analysis_result_id=uuid4(),
            article_id=uuid4(),
            article_title="Tesla Reports Record Q3 Earnings",
            article_content="Tesla Inc. announced today record-breaking financial results for Q3 2024, reporting net profits of $5 billion...",
            article_url="https://example.com/tesla-earnings",
            article_published_at=datetime.utcnow(),
            uq_confidence_score=0.45,
            uncertainty_factors=[
                "Low confidence in claim accuracy",
                "Numerical claim lacks verification"
            ],
            priority="high"
        )

        # Test planner
        planner = DIAPlanner()
        hypothesis, plan = await planner.process_verification_request(event)

        print("\n" + "="*70)
        print("STAGE 1 OUTPUT:")
        print("="*70)
        print(hypothesis.model_dump_json(indent=2))

        print("\n" + "="*70)
        print("STAGE 2 OUTPUT:")
        print("="*70)
        print(plan.model_dump_json(indent=2))

    # Run test
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_planner())
