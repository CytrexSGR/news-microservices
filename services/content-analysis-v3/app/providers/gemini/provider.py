"""
Gemini Provider Implementation
Supports: gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro
"""

import json
import time
import asyncio
from typing import Optional, Type
from pydantic import BaseModel
import google.generativeai as genai

from app.providers.base import BaseLLMProvider, ProviderMetadata, ProviderError, ProviderTimeoutError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider."""

    # Pricing (as of 2025-11, per 1M tokens)
    PRICING = {
        "gemini-2.0-flash-exp": {
            "input": 0.01875,   # $0.00001875 per 1K tokens
            "output": 0.075     # $0.000075 per 1K tokens
        },
        "gemini-1.5-flash": {
            "input": 0.075,
            "output": 0.30
        },
        "gemini-1.5-pro": {
            "input": 1.25,
            "output": 5.00
        }
    }

    def __init__(self, model: str, api_key: str, timeout: int = 60):
        super().__init__(model, api_key, timeout)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        response_format: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0
    ) -> tuple[str, ProviderMetadata]:
        """Generate response from Gemini."""

        start_time = time.time()

        try:
            # Configure generation
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add JSON response format if structured output requested
            if response_format:
                # Add JSON schema instruction to prompt
                schema = response_format.model_json_schema()
                schema_str = json.dumps(schema, indent=2)

                enhanced_prompt = f"""{prompt}

IMPORTANT: Respond with ONLY a valid JSON object matching this schema:

{schema_str}

Do not include any explanatory text, markdown formatting, or code blocks.
Return ONLY the raw JSON object.
"""
                # Note: response_mime_type requires google-generativeai >= 0.4.0
                # For now, we rely on prompt instructions for JSON output
            else:
                enhanced_prompt = prompt

            # Generate with timeout (Gemini SDK is sync, wrap in thread with timeout)
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.generate_content,
                        enhanced_prompt,
                        generation_config=generation_config
                    ),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise ProviderTimeoutError(f"Gemini request timed out after {self.timeout}s")

            # Extract response text
            response_text = response.text

            # Strip markdown code blocks if present (Gemini sometimes wraps JSON in ```json...```)
            if response_text.startswith("```"):
                # Remove first line (```json or ```)
                lines = response_text.split("\n")
                if lines[0].strip() in ["```json", "```"]:
                    lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            # Calculate tokens (Gemini provides usage metadata)
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Validate JSON if structured output
            if response_format:
                try:
                    # Validate against Pydantic model
                    response_format.model_validate_json(response_text)
                except Exception as e:
                    raise ProviderError(f"Invalid JSON response: {e}")

            metadata = ProviderMetadata(
                tokens_used=total_tokens,
                cost_usd=cost_usd,
                model=self.model,
                latency_ms=latency_ms,
                provider="gemini"
            )

            return response_text, metadata

        except Exception as e:
            raise ProviderError(f"Gemini generation failed: {e}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on Gemini pricing."""

        pricing = self.PRICING.get(self.model)
        if not pricing:
            # Default to gemini-2.0-flash-exp pricing
            pricing = self.PRICING["gemini-2.0-flash-exp"]

        # Convert from per-1M to per-token, then multiply
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
