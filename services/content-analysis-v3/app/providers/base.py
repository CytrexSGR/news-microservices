"""
Base LLM Provider Abstract Class
Provides unified interface for Gemini, OpenAI, and future providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Type, Any
from pydantic import BaseModel
import time


class ProviderMetadata(BaseModel):
    """Metadata returned by all providers."""
    tokens_used: int
    cost_usd: float
    model: str
    latency_ms: int
    provider: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    # Default timeout for LLM requests (seconds)
    DEFAULT_TIMEOUT = 60

    def __init__(self, model: str, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        response_format: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0
    ) -> tuple[str, ProviderMetadata]:
        """
        Generate response from LLM.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens to generate
            response_format: Optional Pydantic model for structured output
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Tuple of (response_text, metadata)
            - response_text: The generated text (JSON if response_format provided)
            - metadata: ProviderMetadata with tokens, cost, latency, etc.

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for given token counts."""
        pass

    async def generate_with_fallback(
        self,
        prompt: str,
        max_tokens: int,
        fallback_provider: Optional["BaseLLMProvider"] = None,
        response_format: Optional[Type[BaseModel]] = None
    ) -> tuple[str, ProviderMetadata]:
        """
        Generate with automatic fallback on failure.

        Args:
            prompt: The prompt
            max_tokens: Max tokens
            fallback_provider: Provider to use if primary fails
            response_format: Optional structured output format

        Returns:
            (response, metadata) from either primary or fallback provider
        """
        try:
            return await self.generate(prompt, max_tokens, response_format)
        except Exception as e:
            if fallback_provider:
                # Log primary failure
                print(f"[{self.provider_name}] Failed: {e}, trying fallback...")
                return await fallback_provider.generate(prompt, max_tokens, response_format)
            else:
                raise


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded."""
    pass


class ProviderCostLimitError(ProviderError):
    """Cost limit exceeded."""
    pass


class ProviderTimeoutError(ProviderError):
    """Request timed out."""
    pass
