"""Perplexity Search Tool for NEXUS Agent.

Provides internet search capabilities using the Perplexity AI API.
"""

import httpx
from datetime import datetime
from typing import Any, Dict, Optional

from app.tools.base import BaseTool, ToolResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PerplexitySearchTool(BaseTool):
    """Search the internet using Perplexity AI API."""

    name: str = "perplexity_search"
    description: str = (
        "Search the internet for current information using Perplexity AI. "
        "Use this tool when you need up-to-date information, news, or research "
        "on any topic. Returns content with citations and sources."
    )

    def __init__(self):
        """Initialize Perplexity search tool."""
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_BASE_URL
        self.timeout = settings.PERPLEXITY_TIMEOUT
        self.model = settings.PERPLEXITY_MODEL

        if not self.api_key:
            logger.warning(
                "perplexity_api_key_missing",
                message="PERPLEXITY_API_KEY not set - search will be unavailable",
            )

    async def execute(
        self,
        query: str,
        recency_filter: str = "week",
        **kwargs,
    ) -> ToolResult:
        """
        Execute a Perplexity search.

        Args:
            query: Search query to research
            recency_filter: Time filter - 'day', 'week', or 'month'
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with search content, citations, and sources
        """
        if not self.api_key:
            return ToolResult(
                success=False,
                error="Perplexity API key not configured",
                tool_name=self.name,
            )

        if not query or not query.strip():
            return ToolResult(
                success=False,
                error="Query cannot be empty",
                tool_name=self.name,
            )

        # Validate recency_filter
        valid_filters = ["day", "week", "month"]
        if recency_filter not in valid_filters:
            recency_filter = "week"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant. Provide comprehensive, "
                        "well-sourced answers with citations. Be factual and concise."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "max_tokens": 1000,
            "temperature": 0.5,
            "return_citations": True,
            "return_images": False,
            "search_recency_filter": recency_filter,
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                response = await client.post(
                    "/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()
                parsed = self._parse_response(result)

                logger.info(
                    "perplexity_search_success",
                    query_length=len(query),
                    tokens_used=parsed.get("tokens_used", 0),
                    sources_count=len(parsed.get("sources", [])),
                )

                return ToolResult(
                    success=True,
                    data=parsed,
                    tool_name=self.name,
                )

        except httpx.HTTPStatusError as exc:
            error_msg = f"Perplexity API error: {exc.response.status_code}"
            if exc.response.status_code == 429:
                error_msg = "Rate limit exceeded. Please try again later."
            elif exc.response.status_code == 401:
                error_msg = "Invalid API key"

            logger.error(
                "perplexity_http_error",
                status_code=exc.response.status_code,
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name,
            )

        except httpx.RequestError as exc:
            logger.error(
                "perplexity_request_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Network error: {str(exc)}",
                tool_name=self.name,
            )

        except Exception as exc:
            logger.error(
                "perplexity_unexpected_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(exc)}",
                tool_name=self.name,
            )

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Perplexity API response."""
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = response.get("usage", {})

        content = message.get("content", "")
        citations = message.get("citations", [])

        # Extract unique sources
        sources = self._extract_sources(citations)

        return {
            "content": content,
            "citations": citations,
            "sources": sources,
            "tokens_used": usage.get("total_tokens", 0),
            "model": self.model,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _extract_sources(self, citations: list) -> list:
        """Extract unique sources from citations."""
        sources = []
        seen_urls = set()

        for citation in citations:
            url = citation.get("url")
            if url and url not in seen_urls:
                sources.append({
                    "url": url,
                    "title": citation.get("title", ""),
                    "snippet": citation.get("snippet", ""),
                })
                seen_urls.add(url)

        return sources
