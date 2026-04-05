"""
Provider Factory
Creates LLM provider instances based on configuration
"""

from typing import Literal, Optional
from app.providers.base import BaseLLMProvider
from app.providers.gemini.provider import GeminiProvider
from app.providers.openai.provider import OpenAIProvider
from app.core.config import settings


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create(
        provider: Literal["gemini", "openai"],
        model: str,
        api_key: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create a provider instance.

        Args:
            provider: Provider name ("gemini" or "openai")
            model: Model name (e.g., "gemini-2.0-flash-exp", "gpt-4o-mini")
            api_key: Optional API key (uses settings if not provided)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is unknown or API key is missing
        """

        if provider == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            if not key:
                raise ValueError("GEMINI_API_KEY not configured")
            return GeminiProvider(model=model, api_key=key)

        elif provider == "openai":
            key = api_key or settings.OPENAI_API_KEY
            if not key:
                raise ValueError("OPENAI_API_KEY not configured")
            return OpenAIProvider(model=model, api_key=key)

        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def create_for_tier(tier: Literal["tier0", "tier1", "tier2", "tier3"]) -> BaseLLMProvider:
        """
        Create provider based on tier configuration.

        Args:
            tier: Tier name (tier0, tier1, tier2, tier3)

        Returns:
            Configured provider for that tier
        """

        if tier == "tier0":
            return ProviderFactory.create(
                provider=settings.V3_TIER0_PROVIDER,
                model=settings.V3_TIER0_MODEL
            )

        elif tier == "tier1":
            return ProviderFactory.create(
                provider=settings.V3_TIER1_PROVIDER,
                model=settings.V3_TIER1_MODEL
            )

        elif tier == "tier2":
            return ProviderFactory.create(
                provider=settings.V3_TIER2_PROVIDER,
                model=settings.V3_TIER2_MODEL
            )

        elif tier == "tier3":
            return ProviderFactory.create(
                provider=settings.V3_TIER3_PROVIDER,
                model=settings.V3_TIER3_MODEL
            )

        else:
            raise ValueError(f"Unknown tier: {tier}")

    @staticmethod
    def create_with_fallback(
        tier: Literal["tier0", "tier1", "tier2", "tier3"]
    ) -> tuple[BaseLLMProvider, Optional[BaseLLMProvider]]:
        """
        Create provider with optional fallback.

        Args:
            tier: Tier name

        Returns:
            (primary_provider, fallback_provider)
            fallback_provider is None if not configured
        """

        primary = ProviderFactory.create_for_tier(tier)

        # Only Tier3 has fallback configured
        if tier == "tier3" and settings.V3_TIER3_FALLBACK_PROVIDER:
            fallback = ProviderFactory.create(
                provider=settings.V3_TIER3_FALLBACK_PROVIDER,
                model=settings.V3_TIER3_FALLBACK_MODEL
            )
            return primary, fallback

        return primary, None
