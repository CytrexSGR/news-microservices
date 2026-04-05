"""
Perplexity Deep Search Tool

Uses Perplexity API for web-based fact verification with automatic citations.

Related: ADR-018 (DIA-Planner & Verifier - Phase 2)
"""

import logging
import httpx
import time
from typing import Dict, List, Optional

# Import from project root models
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from models.verification_events import ToolExecutionResult
from app.core.config import settings

logger = logging.getLogger(__name__)


async def perplexity_deep_search(
    query: str,
    search_domain_filter: Optional[List[str]] = None,
    search_recency_filter: Optional[str] = None
) -> ToolExecutionResult:
    """
    Execute deep web search using Perplexity API.

    This tool performs real-time web search with AI-powered analysis and
    automatic source citations. Perfect for fact-checking and verification.

    Args:
        query: Search query (e.g., "Tesla Q3 2024 earnings actual amount")
        search_domain_filter: Optional list of domains to search
                            (e.g., ["sec.gov", "ir.tesla.com"])
        search_recency_filter: Optional time filter
                             ("day", "week", "month", "year")

    Returns:
        ToolExecutionResult with:
        - result_data: {"answer": str, "sources": List[str]}
        - source_citations: List of URLs
        - confidence: 0.0-1.0 based on citation quality

    Example:
        result = await perplexity_deep_search(
            query="Tesla Q3 2024 earnings actual amount",
            search_domain_filter=["sec.gov", "ir.tesla.com"],
            search_recency_filter="month"
        )
    """
    start_time = time.time()

    tool_params = {
        "query": query,
        "search_domain_filter": search_domain_filter,
        "search_recency_filter": search_recency_filter
    }

    try:
        logger.info(f"[Perplexity] Executing deep search: {query[:100]}...")

        # Check if API key is configured
        # Prefer dedicated Perplexity key, fallback to OpenAI key
        perplexity_api_key = settings.PERPLEXITY_API_KEY or settings.OPENAI_API_KEY

        if not perplexity_api_key:
            raise ValueError("Perplexity API key not configured (set PERPLEXITY_API_KEY or OPENAI_API_KEY)")

        # Build request
        request_data = {
            "model": "sonar-pro",  # Use pro model for better results
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a fact-checking research assistant. "
                        "Provide accurate, well-sourced answers with clear citations. "
                        "Focus on authoritative sources and recent information."
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2,  # Low temperature for factual accuracy
            "return_citations": True
        }

        # Add optional filters
        if search_domain_filter:
            request_data["search_domain_filter"] = search_domain_filter
            logger.info(f"[Perplexity] Domain filter: {search_domain_filter}")

        if search_recency_filter:
            request_data["search_recency_filter"] = search_recency_filter
            logger.info(f"[Perplexity] Recency filter: {search_recency_filter}")

        # Make API call
        async with httpx.AsyncClient(timeout=settings.TOOL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )

            response.raise_for_status()
            result = response.json()

        # Extract answer and citations
        answer = result["choices"][0]["message"]["content"]
        citations = result["choices"][0]["message"].get("citations", [])

        execution_time = int((time.time() - start_time) * 1000)

        # Calculate confidence based on citation quality
        confidence = _calculate_confidence(citations, search_domain_filter)

        logger.info(
            f"[Perplexity] Search completed in {execution_time}ms. "
            f"Citations: {len(citations)}, Confidence: {confidence:.2f}"
        )

        return ToolExecutionResult(
            tool_name="perplexity_deep_search",
            tool_parameters=tool_params,
            success=True,
            execution_time_ms=execution_time,
            result_data={
                "answer": answer,
                "sources": citations,
                "model": "sonar-pro",
                "token_usage": result.get("usage", {})
            },
            source_citations=citations,
            confidence=confidence
        )

    except httpx.HTTPStatusError as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = f"Perplexity API error: {e.response.status_code} - {e.response.text}"
        logger.error(f"[Perplexity] {error_msg}")

        return ToolExecutionResult(
            tool_name="perplexity_deep_search",
            tool_parameters=tool_params,
            success=False,
            execution_time_ms=execution_time,
            error_message=error_msg,
            source_citations=[],
            confidence=0.0
        )

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(f"[Perplexity] {error_msg}", exc_info=True)

        return ToolExecutionResult(
            tool_name="perplexity_deep_search",
            tool_parameters=tool_params,
            success=False,
            execution_time_ms=execution_time,
            error_message=error_msg,
            source_citations=[],
            confidence=0.0
        )


def _calculate_confidence(
    citations: List[str],
    domain_filter: Optional[List[str]]
) -> float:
    """
    Calculate confidence score based on citation quality.

    Args:
        citations: List of citation URLs
        domain_filter: Optional domain filter applied

    Returns:
        Confidence score 0.0-1.0

    Logic:
        - Base confidence: 0.5 if citations exist, 0.2 if none
        - +0.1 for each authoritative domain (.gov, .edu, known orgs)
        - +0.2 if all citations match domain filter
        - Capped at 0.95 (never 100% certain)
    """
    if not citations:
        return 0.2  # Low confidence without sources

    base_confidence = 0.5

    # Check for authoritative domains
    authoritative_domains = [
        ".gov", ".edu", "sec.gov", "ir.tesla.com",
        "reuters.com", "bloomberg.com", "ft.com",
        "un.org", "europa.eu", "nature.com"
    ]

    authoritative_count = sum(
        1 for url in citations
        if any(domain in url.lower() for domain in authoritative_domains)
    )

    authority_boost = min(0.3, authoritative_count * 0.1)

    # Check if citations match domain filter
    filter_match_boost = 0.0
    if domain_filter and citations:
        matching_citations = sum(
            1 for url in citations
            if any(domain in url.lower() for domain in domain_filter)
        )
        if matching_citations == len(citations):
            filter_match_boost = 0.2

    confidence = base_confidence + authority_boost + filter_match_boost

    # Cap at 0.95 (never 100% certain)
    return min(0.95, confidence)


# For testing
if __name__ == "__main__":
    import asyncio

    async def test_perplexity():
        """Test the Perplexity tool."""
        logging.basicConfig(level=logging.INFO)

        # Test query
        result = await perplexity_deep_search(
            query="What were Tesla's actual Q3 2024 earnings?",
            search_domain_filter=["sec.gov", "ir.tesla.com"],
            search_recency_filter="month"
        )

        print("\n" + "="*70)
        print("PERPLEXITY TOOL TEST")
        print("="*70)
        print(f"Success: {result.success}")
        print(f"Execution Time: {result.execution_time_ms}ms")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Citations: {len(result.source_citations)}")
        print(f"\nAnswer:\n{result.result_data.get('answer', 'N/A')[:500]}...")
        print(f"\nSources:")
        for url in result.source_citations[:5]:
            print(f"  - {url}")

    asyncio.run(test_perplexity())
