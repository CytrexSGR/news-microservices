"""
DIA (Dynamic Intelligence Augmentation) Verifier

Executes verification plans by orchestrating external tools in parallel
and aggregating evidence into structured packages.

Related: ADR-018 (DIA-Planner & Verifier - Phase 2)
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Tuple, Callable, Any

# Import from project root models
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import (
    ProblemHypothesis,
    EvidencePackage,
    ToolExecutionResult,
    VerificationRequiredEvent
)
from models.adversarial_test_case import VerificationPlan

from app.tools import perplexity_deep_search, financial_data_lookup

logger = logging.getLogger(__name__)


class DIAVerifier:
    """
    DIA Verifier: Execute verification plans and aggregate evidence.

    This class:
    1. Parses verification plan methods
    2. Executes tools in parallel
    3. Aggregates results into EvidencePackage
    4. Calculates confidence scores

    Example:
        verifier = DIAVerifier()
        evidence = await verifier.execute_verification(
            plan=verification_plan,
            hypothesis=problem_hypothesis,
            event=verification_event
        )
    """

    def __init__(self):
        """Initialize DIA Verifier with tool registry."""
        # Register available tools
        self.tool_registry: Dict[str, Callable] = {
            "perplexity_deep_search": perplexity_deep_search,
            "financial_data_lookup": financial_data_lookup,
        }

        logger.info(
            f"[DIAVerifier] Initialized with {len(self.tool_registry)} tools: "
            f"{list(self.tool_registry.keys())}"
        )

    async def execute_verification(
        self,
        plan: VerificationPlan,
        hypothesis: ProblemHypothesis,
        event: VerificationRequiredEvent
    ) -> EvidencePackage:
        """
        Execute verification plan and aggregate evidence.

        Args:
            plan: Verification plan from DIA Planner (Stage 2)
            hypothesis: Problem hypothesis from DIA Planner (Stage 1)
            event: Original verification request

        Returns:
            EvidencePackage with complete evidence and corrections

        Process:
            1. Parse verification_methods to extract tool calls
            2. Execute all tools in parallel using asyncio.gather
            3. Aggregate results into EvidencePackage
            4. Calculate confidence and identify corrections
        """
        start_time = time.time()

        logger.info(
            f"[DIAVerifier] Executing verification plan with "
            f"{len(plan.verification_methods)} methods"
        )

        # =====================================================================
        # Step 1: Parse verification methods
        # =====================================================================
        tool_calls = self._parse_verification_methods(plan.verification_methods)
        logger.info(f"[DIAVerifier] Parsed {len(tool_calls)} tool calls")

        # =====================================================================
        # Step 2: Execute tools in parallel
        # =====================================================================
        logger.info("[DIAVerifier] Executing tools in parallel...")
        tool_results = await self._execute_tools_parallel(tool_calls)

        successful_tools = sum(1 for r in tool_results if r.success)
        logger.info(
            f"[DIAVerifier] Tool execution complete: "
            f"{successful_tools}/{len(tool_results)} successful"
        )

        # =====================================================================
        # Step 3: Aggregate evidence
        # =====================================================================
        logger.info("[DIAVerifier] Aggregating evidence...")
        evidence_package = self._aggregate_evidence(
            hypothesis=hypothesis,
            plan=plan,
            tool_results=tool_results,
            event=event,
            total_execution_time_ms=int((time.time() - start_time) * 1000)
        )

        logger.info(
            f"[DIAVerifier] Verification complete: "
            f"hypothesis_confirmed={evidence_package.hypothesis_confirmed}, "
            f"confidence={evidence_package.confidence_score:.2f}"
        )

        return evidence_package

    def _parse_verification_methods(
        self,
        methods: List[str]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse verification methods into tool calls.

        Args:
            methods: List of method strings from plan
                    e.g., ["perplexity_deep_search(query='Tesla Q3 2024 earnings')"]

        Returns:
            List of (tool_name, parameters) tuples

        Example:
            Input: ["perplexity_deep_search(query='Tesla Q3 2024 earnings')"]
            Output: [("perplexity_deep_search", {"query": "Tesla Q3 2024 earnings"})]
        """
        tool_calls = []

        for method in methods:
            try:
                # Parse method string: tool_name(param1='value1', param2='value2')
                match = re.match(r"(\w+)\((.*)\)", method.strip())

                if not match:
                    logger.warning(f"[DIAVerifier] Failed to parse method: {method}")
                    continue

                tool_name = match.group(1)
                params_str = match.group(2)

                # Parse parameters
                params = {}
                if params_str:
                    # Simple parameter parsing (key='value' or key="value")
                    param_pattern = r"(\w+)=['\"]([^'\"]+)['\"]"
                    for param_match in re.finditer(param_pattern, params_str):
                        key = param_match.group(1)
                        value = param_match.group(2)
                        params[key] = value

                # Validate tool exists
                if tool_name not in self.tool_registry:
                    logger.warning(
                        f"[DIAVerifier] Unknown tool: {tool_name}. "
                        f"Available: {list(self.tool_registry.keys())}"
                    )
                    continue

                tool_calls.append((tool_name, params))
                logger.debug(f"[DIAVerifier] Parsed: {tool_name}({params})")

            except Exception as e:
                logger.error(
                    f"[DIAVerifier] Error parsing method '{method}': {e}",
                    exc_info=True
                )

        return tool_calls

    async def _execute_tools_parallel(
        self,
        tool_calls: List[Tuple[str, Dict[str, Any]]]
    ) -> List[ToolExecutionResult]:
        """
        Execute multiple tools in parallel using asyncio.gather.

        Args:
            tool_calls: List of (tool_name, parameters) tuples

        Returns:
            List of ToolExecutionResult objects
        """
        if not tool_calls:
            logger.warning("[DIAVerifier] No valid tool calls to execute")
            return []

        # Create coroutines for each tool
        coroutines = []
        for tool_name, params in tool_calls:
            tool_func = self.tool_registry[tool_name]
            coroutine = tool_func(**params)
            coroutines.append(coroutine)

        # Execute all tools in parallel
        logger.info(f"[DIAVerifier] Executing {len(coroutines)} tools in parallel...")
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Handle exceptions
        tool_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_name, params = tool_calls[i]
                logger.error(
                    f"[DIAVerifier] Tool {tool_name} raised exception: {result}",
                    exc_info=result
                )
                # Create failed ToolExecutionResult
                tool_results.append(ToolExecutionResult(
                    tool_name=tool_name,
                    tool_parameters=params,
                    success=False,
                    execution_time_ms=0,
                    error_message=str(result),
                    source_citations=[],
                    confidence=0.0
                ))
            else:
                tool_results.append(result)

        return tool_results

    def _aggregate_evidence(
        self,
        hypothesis: ProblemHypothesis,
        plan: VerificationPlan,
        tool_results: List[ToolExecutionResult],
        event: VerificationRequiredEvent,
        total_execution_time_ms: int
    ) -> EvidencePackage:
        """
        Aggregate tool results into comprehensive evidence package.

        Args:
            hypothesis: Original problem hypothesis
            plan: Verification plan
            tool_results: Results from all tool executions
            event: Original verification request
            total_execution_time_ms: Total execution time

        Returns:
            Complete EvidencePackage

        Logic:
            1. Collect all sources and citations
            2. Extract key findings from tool results
            3. Determine if hypothesis is confirmed
            4. Calculate overall confidence score
            5. Identify corrected facts
        """
        logger.info("[DIAVerifier] Aggregating evidence from tool results...")

        # Collect successful results
        successful_results = [r for r in tool_results if r.success]

        if not successful_results:
            logger.warning("[DIAVerifier] No successful tool executions!")

        # Extract key findings
        key_findings = self._extract_key_findings(successful_results)

        # Collect all source citations
        all_citations = []
        for result in successful_results:
            all_citations.extend(result.source_citations)

        # Build source citation objects
        source_citations = self._build_source_citations(all_citations)

        # Determine if hypothesis is confirmed
        hypothesis_confirmed = self._is_hypothesis_confirmed(
            hypothesis,
            successful_results
        )

        # Calculate overall confidence
        confidence_score = self._calculate_overall_confidence(
            tool_results,
            hypothesis_confirmed
        )

        # Identify corrected facts
        corrected_facts = self._identify_corrections(
            hypothesis,
            successful_results,
            plan
        )

        # Build evidence package
        evidence_package = EvidencePackage(
            verification_request_id=event.event_id,
            problem_hypothesis=hypothesis,
            verification_plan=plan.model_dump(),
            tool_executions=tool_results,
            total_execution_time_ms=total_execution_time_ms,
            hypothesis_confirmed=hypothesis_confirmed,
            confidence_score=confidence_score,
            key_findings=key_findings,
            corrected_facts=corrected_facts,
            source_citations=source_citations,
            verification_quality={
                "source_reliability": self._calculate_source_reliability(source_citations),
                "evidence_consistency": self._calculate_evidence_consistency(successful_results),
                "coverage_completeness": len(successful_results) / max(len(tool_results), 1)
            }
        )

        logger.info(
            f"[DIAVerifier] Evidence package created: "
            f"{len(key_findings)} findings, "
            f"{len(corrected_facts)} corrections, "
            f"{len(source_citations)} sources"
        )

        return evidence_package

    def _extract_key_findings(
        self,
        results: List[ToolExecutionResult]
    ) -> List[str]:
        """
        Extract key findings from tool results.

        Args:
            results: Successful tool execution results

        Returns:
            List of key finding strings
        """
        findings = []

        for result in results:
            if result.tool_name == "perplexity_deep_search":
                # Extract first few sentences from answer
                answer = result.result_data.get("answer", "")
                if answer:
                    # Take first 200 chars as key finding
                    finding = answer[:200].strip()
                    if len(answer) > 200:
                        finding += "..."
                    findings.append(f"[Perplexity] {finding}")

            elif result.tool_name == "financial_data_lookup":
                # Extract specific financial metrics
                data = result.result_data.get("data", {})
                company = result.result_data.get("company", "")
                metric = result.result_data.get("metric", "")

                if metric == "earnings":
                    eps = data.get("reported_eps")
                    date = data.get("fiscal_date_ending")
                    if eps and date:
                        findings.append(
                            f"[Financial Data] {company} reported EPS of {eps} "
                            f"for period ending {date}"
                        )

                elif metric == "quote":
                    price = data.get("price")
                    if price:
                        findings.append(
                            f"[Financial Data] {company} current price: ${price}"
                        )

        if not findings:
            findings.append("No specific findings extracted from tools")

        return findings

    def _build_source_citations(
        self,
        all_citations: List[str]
    ) -> List[Dict[str, str]]:
        """
        Build structured source citation objects.

        Args:
            all_citations: List of URL strings

        Returns:
            List of citation objects with metadata
        """
        # Deduplicate citations
        unique_citations = list(set(all_citations))

        source_objects = []
        for url in unique_citations:
            # Categorize reliability
            reliability = "secondary"  # default

            if any(domain in url.lower() for domain in [".gov", "sec.gov"]):
                reliability = "primary"
            elif any(domain in url.lower() for domain in ["reuters.com", "bloomberg.com"]):
                reliability = "authoritative"

            source_objects.append({
                "source": url,
                "url": url,
                "reliability": reliability
            })

        return source_objects

    def _is_hypothesis_confirmed(
        self,
        hypothesis: ProblemHypothesis,
        results: List[ToolExecutionResult]
    ) -> bool:
        """
        Determine if hypothesis is confirmed by evidence.

        Args:
            hypothesis: Problem hypothesis
            results: Successful tool results

        Returns:
            True if hypothesis is confirmed

        Logic:
            - If majority of tools succeeded and have high confidence → likely confirmed
            - For now, simple heuristic based on confidence scores
            - Future: Use LLM to analyze evidence and determine confirmation
        """
        if not results:
            return False

        # Calculate average confidence from tools
        avg_confidence = sum(r.confidence for r in results) / len(results)

        # If average confidence > 0.7, consider hypothesis confirmed
        confirmed = avg_confidence > 0.7

        logger.info(
            f"[DIAVerifier] Hypothesis confirmation: {confirmed} "
            f"(avg_confidence={avg_confidence:.2f})"
        )

        return confirmed

    def _calculate_overall_confidence(
        self,
        tool_results: List[ToolExecutionResult],
        hypothesis_confirmed: bool
    ) -> float:
        """
        Calculate overall confidence score for evidence package.

        Args:
            tool_results: All tool execution results
            hypothesis_confirmed: Whether hypothesis was confirmed

        Returns:
            Confidence score 0.0-1.0

        Logic:
            - Base confidence from successful tool results
            - Penalty for failed tools
            - Boost if hypothesis confirmed
        """
        if not tool_results:
            return 0.0

        successful_results = [r for r in tool_results if r.success]

        if not successful_results:
            return 0.1  # Very low confidence if no tools succeeded

        # Calculate average confidence from successful tools
        avg_tool_confidence = sum(r.confidence for r in successful_results) / len(successful_results)

        # Success rate
        success_rate = len(successful_results) / len(tool_results)

        # Base confidence: weighted average
        base_confidence = (avg_tool_confidence * 0.7) + (success_rate * 0.3)

        # Boost if hypothesis confirmed
        if hypothesis_confirmed:
            base_confidence = min(0.95, base_confidence + 0.1)

        return round(base_confidence, 2)

    def _identify_corrections(
        self,
        hypothesis: ProblemHypothesis,
        results: List[ToolExecutionResult],
        plan: VerificationPlan
    ) -> Dict[str, Dict[str, str]]:
        """
        Identify corrected facts from verification results.

        Args:
            hypothesis: Problem hypothesis
            results: Successful tool results
            plan: Verification plan (contains expected corrections)

        Returns:
            Dictionary of corrected facts

        Example:
            {
                "Tesla Q3 2024 profit": {
                    "original": "$5 billion",
                    "corrected": "$4.194 billion",
                    "source": "SEC Filing 10-Q",
                    "source_url": "https://sec.gov/..."
                }
            }
        """
        corrections = {}

        # Use expected corrections from plan as template
        for expected_correction in plan.expected_corrections:
            field = expected_correction.field
            original = expected_correction.original
            corrected = expected_correction.corrected

            # Try to find supporting evidence from tool results
            supporting_source = self._find_supporting_source(corrected, results)

            corrections[f"{field}: {original}"] = {
                "original": original,
                "corrected": corrected,
                "source": supporting_source.get("source", "Verification tools"),
                "source_url": supporting_source.get("url", "")
            }

        return corrections

    def _find_supporting_source(
        self,
        corrected_value: str,
        results: List[ToolExecutionResult]
    ) -> Dict[str, str]:
        """
        Find best supporting source for corrected value.

        Args:
            corrected_value: The corrected fact value
            results: Tool execution results

        Returns:
            Source information dict
        """
        # Simple heuristic: Use first authoritative source
        for result in results:
            if result.source_citations:
                # Prefer .gov sources
                gov_sources = [url for url in result.source_citations if ".gov" in url.lower()]
                if gov_sources:
                    return {"source": "Government source", "url": gov_sources[0]}

                # Otherwise use first source
                return {"source": "External verification", "url": result.source_citations[0]}

        return {"source": "Verification tools", "url": ""}

    def _calculate_source_reliability(
        self,
        sources: List[Dict[str, str]]
    ) -> float:
        """Calculate source reliability score based on source types."""
        if not sources:
            return 0.0

        reliability_scores = {
            "primary": 1.0,
            "authoritative": 0.8,
            "secondary": 0.6
        }

        total_score = sum(
            reliability_scores.get(s.get("reliability", "secondary"), 0.6)
            for s in sources
        )

        return round(total_score / len(sources), 2)

    def _calculate_evidence_consistency(
        self,
        results: List[ToolExecutionResult]
    ) -> float:
        """
        Calculate consistency score across evidence.

        Simple heuristic: If all tools have similar confidence, evidence is consistent.
        """
        if len(results) < 2:
            return 1.0

        confidences = [r.confidence for r in results]
        avg_confidence = sum(confidences) / len(confidences)

        # Calculate variance
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

        # Low variance = high consistency
        consistency = max(0.0, 1.0 - (variance * 2))

        return round(consistency, 2)


# For testing/debugging
if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    from uuid import uuid4

    async def test_verifier():
        """Test the DIA Verifier with a sample plan."""
        logging.basicConfig(level=logging.INFO)

        # Create test data
        event = VerificationRequiredEvent(
            analysis_result_id=uuid4(),
            article_id=uuid4(),
            article_title="Tesla Reports Record Q3 Earnings",
            article_content="Tesla announced Q3 earnings of $5 billion...",
            article_url="https://example.com/tesla",
            article_published_at=datetime.utcnow(),
            uq_confidence_score=0.45,
            uncertainty_factors=["Numerical claim lacks verification"]
        )

        hypothesis = ProblemHypothesis(
            primary_concern="Financial figure appears incorrect",
            affected_content="Q3 earnings of $5 billion",
            hypothesis_type="factual_error",
            confidence=0.85,
            reasoning="Unusually high compared to historical data",
            verification_approach="Cross-reference with official sources"
        )

        plan = VerificationPlan(
            priority="high",
            verification_methods=[
                "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount')",
                "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
            ],
            external_sources=["SEC filings", "Tesla IR"],
            expected_corrections=[{
                "field": "earnings",
                "original": "$5 billion",
                "corrected": "$4.2 billion",
                "confidence_improvement": 0.20
            }],
            estimated_verification_time_seconds=60
        )

        # Execute verification
        verifier = DIAVerifier()
        evidence = await verifier.execute_verification(
            plan=plan,
            hypothesis=hypothesis,
            event=event
        )

        # Print results
        print("\n" + "="*70)
        print("EVIDENCE PACKAGE")
        print("="*70)
        print(evidence.model_dump_json(indent=2))

    asyncio.run(test_verifier())
