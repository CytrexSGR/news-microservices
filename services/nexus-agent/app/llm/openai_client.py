"""OpenAI LLM Client for NEXUS Agent."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API calls."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.OPENAI_MODEL
        self.client = ChatOpenAI(
            model=self.model,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=settings.MAX_TOKENS_PER_REQUEST,
        )
        logger.info("openai_client_initialized", model=self.model)

    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
    ) -> tuple[str, int]:
        """
        Invoke the LLM with a system prompt and user message.

        Returns:
            Tuple of (response_text, tokens_used)
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        response = await self.client.ainvoke(messages)

        tokens_used = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

        logger.info(
            "llm_invoked",
            model=self.model,
            tokens=tokens_used,
        )

        return response.content, tokens_used


# Singleton instance
_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    """Get or create OpenAI client singleton."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client
