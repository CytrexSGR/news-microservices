"""RAG (Retrieval-Augmented Generation) service for intelligence queries."""

import hashlib
import time
import httpx
import structlog
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from app.core.config import settings
from .rag_prompts import (
    SYSTEM_PROMPT_BRIEF,
    SYSTEM_PROMPT_DETAILED,
    CONTEXT_TEMPLATE,
)

logger = structlog.get_logger()


class Depth(str, Enum):
    BRIEF = "brief"
    DETAILED = "detailed"


@dataclass
class RAGSource:
    """A source document used in the RAG response."""
    title: str
    url: Optional[str]
    similarity: float
    published_at: Optional[str]


@dataclass
class RAGResponse:
    """Response from the RAG service."""
    answer: str
    depth: str
    sources: List[RAGSource]
    tokens_used: int
    context_articles: int
    metadata: Dict[str, Any]


# Cache for LLM responses
_response_cache: Dict[str, Tuple[RAGResponse, float]] = {}
CACHE_TTL = 300  # 5 minutes


def _cache_key(question: str, depth: str) -> str:
    """Generate cache key from question and depth."""
    return hashlib.md5(f"{question.lower().strip()}:{depth}".encode()).hexdigest()


class RAGService:
    """
    RAG service for answering intelligence questions.

    Pipeline:
    1. Semantic search for relevant articles
    2. Fetch intelligence summary (bursts, sentiment, etc.)
    3. Format context for LLM
    4. Generate answer via LLM
    """

    def __init__(self):
        self.search_url = getattr(settings, 'SEARCH_SERVICE_URL', 'http://search-service:8006')
        self.llm_model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.llm_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self._http_client: Optional[httpx.AsyncClient] = None

        # Allow mocking in tests
        self.search_client: Optional[Any] = None
        self.llm_client: Optional[Any] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def ask(
        self,
        question: str,
        depth: str = "brief",
    ) -> RAGResponse:
        """
        Answer an intelligence question using RAG.

        Args:
            question: Natural language question
            depth: "brief" (2-3 sentences) or "detailed" (full analysis)

        Returns:
            RAGResponse with answer, sources, and metadata
        """
        # Check cache first
        cache_key = _cache_key(question, depth)
        if cache_key in _response_cache:
            cached_response, cached_time = _response_cache[cache_key]
            if time.time() - cached_time < CACHE_TTL:
                logger.info("RAG cache hit", question=question[:50])
                return cached_response

        # Generate response
        response = await self._ask_uncached(question, depth)

        # Cache the response
        _response_cache[cache_key] = (response, time.time())

        # Prune old cache entries
        self._prune_cache()

        return response

    async def _ask_uncached(
        self,
        question: str,
        depth: str = "brief",
    ) -> RAGResponse:
        """Answer without cache (internal implementation)."""
        depth_enum = Depth(depth)

        # Step 1: Semantic search for relevant articles
        articles = await self._semantic_search(
            question,
            limit=5 if depth_enum == Depth.BRIEF else 15
        )

        # Step 2: Get intelligence summary
        intel_summary = await self._get_intelligence_summary()

        # Step 3: Handle no results case
        if not articles:
            return RAGResponse(
                answer=f"No relevant articles found for: '{question}'. Try rephrasing or broadening your query.",
                depth=depth,
                sources=[],
                tokens_used=0,
                context_articles=0,
                metadata={"status": "no_results"}
            )

        # Step 4: Format context
        context = self._format_context(question, articles, intel_summary)

        # Step 5: Generate answer via LLM
        system_prompt = SYSTEM_PROMPT_BRIEF if depth_enum == Depth.BRIEF else SYSTEM_PROMPT_DETAILED
        answer, tokens = await self._generate_answer(system_prompt, context)

        # Step 6: Build response
        sources = [
            RAGSource(
                title=a.get("title", "Untitled"),
                url=a.get("url"),
                similarity=a.get("similarity", 0),
                published_at=a.get("published_at")
            )
            for a in articles[:5]  # Max 5 sources in response
        ]

        return RAGResponse(
            answer=answer,
            depth=depth,
            sources=sources,
            tokens_used=tokens,
            context_articles=len(articles),
            metadata={
                "model": self.llm_model,
                "intel_summary": intel_summary,
            }
        )

    async def _semantic_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform semantic search via search-service."""
        # Check if mock is set (for testing)
        if self.search_client is not None:
            result = await self.search_client.semantic_search(query=query, limit=limit)
            return result.get("results", [])

        try:
            response = await self.http_client.post(
                f"{self.search_url}/api/v1/search/semantic",
                json={
                    "query": query,
                    "limit": limit,
                    "min_similarity": 0.6,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            return []

    async def _get_intelligence_summary(self) -> Dict[str, Any]:
        """Get current intelligence summary (internal call, no auth required)."""
        try:
            response = await self.http_client.get(
                "http://localhost:8107/api/v1/intelligence/summary",
                params={"hours": 24}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Intelligence summary unavailable", error=str(e))
            return {"bursts": {"count": 0}, "momentum": {}, "contrarian": {}}

    def _format_context(
        self,
        question: str,
        articles: List[Dict[str, Any]],
        intel_summary: Dict[str, Any]
    ) -> str:
        """Format context for LLM."""
        # Format articles
        article_texts = []
        for i, a in enumerate(articles[:10], 1):
            title = a.get("title", "Untitled")
            content = a.get("content", "")[:500]  # Truncate
            sentiment = a.get("sentiment", "N/A")
            date = a.get("published_at", "Unknown date")
            article_texts.append(
                f"{i}. [{date}] {title}\n"
                f"   Sentiment: {sentiment}\n"
                f"   {content}..."
            )

        # Extract intel summary fields
        bursts = intel_summary.get("bursts", {})
        burst_count = bursts.get("count", 0)
        top_burst = "None"
        if bursts.get("items"):
            top_burst = bursts["items"][0].get("entity", "Unknown")

        momentum = intel_summary.get("momentum", {})
        improving = len(momentum.get("improving", []))
        deteriorating = len(momentum.get("deteriorating", []))
        sentiment_trend = f"{improving} improving, {deteriorating} deteriorating"

        contrarian = intel_summary.get("contrarian", {})
        risk_level = "elevated" if contrarian.get("count", 0) > 5 else "normal"

        return CONTEXT_TEMPLATE.format(
            question=question,
            article_count=len(articles),
            articles="\n\n".join(article_texts),
            burst_count=burst_count,
            top_burst=top_burst,
            sentiment_trend=sentiment_trend,
            risk_level=risk_level,
        )

    async def _generate_answer(
        self,
        system_prompt: str,
        context: str
    ) -> Tuple[str, int]:
        """Generate answer using LLM."""
        # Check if mock is set (for testing)
        if self.llm_client is not None:
            return await self.llm_client.invoke(system_prompt, context)

        try:
            # Use OpenAI directly
            import openai

            client = openai.AsyncOpenAI(api_key=self.llm_api_key)

            response = await client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context},
                ],
                max_tokens=500 if "brief" in system_prompt.lower()[:100] else 1500,
                temperature=0.3,  # Lower for factual responses
            )

            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0

            return answer, tokens

        except ImportError:
            logger.error("openai package not installed")
            return "OpenAI package not installed. Please add 'openai' to requirements.txt", 0
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return f"Unable to generate answer: {str(e)}", 0

    def _prune_cache(self, max_size: int = 100):
        """Remove old cache entries."""
        if len(_response_cache) > max_size:
            # Remove oldest entries
            sorted_keys = sorted(
                _response_cache.keys(),
                key=lambda k: _response_cache[k][1]
            )
            for key in sorted_keys[:len(sorted_keys) - max_size]:
                del _response_cache[key]


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get singleton RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
