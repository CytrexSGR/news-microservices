"""
OpenAI Provider Implementation
Supports: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
"""

import json
import time
import asyncio
from typing import Optional, Type
from pydantic import BaseModel
from openai import AsyncOpenAI
import httpx

from app.providers.base import BaseLLMProvider, ProviderMetadata, ProviderError, ProviderTimeoutError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider."""

    # Pricing (as of 2025-11, per 1M tokens)
    PRICING = {
        "gpt-4o": {
            "input": 2.50,
            "output": 10.00
        },
        "gpt-4o-mini": {
            "input": 0.15,
            "output": 0.60
        },
        "gpt-3.5-turbo": {
            "input": 0.50,
            "output": 1.50
        }
    }

    def __init__(self, model: str, api_key: str, timeout: int = 60):
        super().__init__(model, api_key, timeout)
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(timeout, connect=10.0)
        )

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        response_format: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0
    ) -> tuple[str, ProviderMetadata]:
        """Generate response from OpenAI."""

        start_time = time.time()

        try:
            # Build request parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # Add structured output if requested (OpenAI native support)
            if response_format:
                # Use JSON mode (not strict - allows flexible responses)
                schema = response_format.model_json_schema()
                schema_str = json.dumps(schema, indent=2)

                params["messages"][0]["content"] = f"""{prompt}

CRITICAL: Respond with ONLY a JSON object matching this schema.
NO explanations, NO markdown formatting, NO code fences.

{schema_str}

Your JSON response (start with {{ and end with }}):
"""
                params["response_format"] = {"type": "json_object"}

            # Generate
            response = await self.client.chat.completions.create(**params)

            # Extract response
            message = response.choices[0].message
            response_text = message.content

            # Post-process response (remove markdown, backticks, etc.)
            if response_format:
                # Remove markdown code fences
                response_text = response_text.strip()
                if response_text.startswith("```"):
                    # Remove ```json or ``` prefix
                    response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]

                # Extract JSON object (from first { to last })
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    response_text = response_text[start:end+1]

            # Get usage
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Validate JSON if structured output
            if response_format:
                try:
                    response_format.model_validate_json(response_text)
                except Exception as e:
                    # Log the actual response for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Invalid JSON response from {self.model}: {response_text[:500]}")
                    raise ProviderError(f"Invalid JSON response: {e}")

            metadata = ProviderMetadata(
                tokens_used=total_tokens,
                cost_usd=cost_usd,
                model=self.model,
                latency_ms=latency_ms,
                provider="openai"
            )

            return response_text, metadata

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"OpenAI request timed out after {self.timeout}s")
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"OpenAI request timed out after {self.timeout}s")
        except Exception as e:
            raise ProviderError(f"OpenAI generation failed: {e}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on OpenAI pricing."""

        pricing = self.PRICING.get(self.model)
        if not pricing:
            # Default to gpt-4o-mini pricing
            pricing = self.PRICING["gpt-4o-mini"]

        # Convert from per-1M to per-token
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    # Embedding model pricing (per 1M tokens)
    EMBEDDING_PRICING = {
        "text-embedding-3-small": 0.02,
        "text-embedding-3-large": 0.13,
        "text-embedding-ada-002": 0.10,
    }

    async def generate_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> list[float]:
        """
        Generate embedding vector for text using OpenAI Embeddings API.

        Uses text-embedding-3-small by default (1536 dimensions, $0.02/1M tokens).
        Text is truncated to 8000 characters to stay within token limits.

        Args:
            text: Text to embed (will be truncated if > 8000 chars)
            model: Embedding model to use (default: text-embedding-3-small)

        Returns:
            List of 1536 floats representing the embedding vector

        Raises:
            ProviderError: If embedding generation fails
            ProviderTimeoutError: If request times out
        """
        try:
            # Truncate to avoid token limits (~8000 chars ≈ 2000 tokens)
            truncated_text = text[:8000]

            response = await self.client.embeddings.create(
                model=model,
                input=truncated_text
            )

            return response.data[0].embedding

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(
                f"Embedding request timed out after {self.timeout}s"
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(
                f"Embedding request timed out after {self.timeout}s"
            )
        except Exception as e:
            raise ProviderError(f"Embedding generation failed: {e}")
