"""Embedding provider using DGX Spark Qwen3-VL-Embedding-2B (OpenAI-compatible API)."""
import httpx


class DGXEmbeddingProvider:
    def __init__(
        self,
        base_url: str = "http://localhost:8766",
        model: str = "Qwen/Qwen3-Embedding-0.6B",
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _prepare_text(self, text: str) -> str:
        return text[:8000]

    async def generate_embedding(self, text: str) -> list[float]:
        prepared = self._prepare_text(text)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/embeddings",
                json={"input": prepared, "model": self.model},
            )
            resp.raise_for_status()
            data = resp.json()
            return [float(x) for x in data["data"][0]["embedding"]]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        prepared = [self._prepare_text(t) for t in texts]
        async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
            resp = await client.post(
                f"{self.base_url}/v1/embeddings",
                json={"input": prepared, "model": self.model},
            )
            resp.raise_for_status()
            data = resp.json()
            return [[float(x) for x in item["embedding"]] for item in data["data"]]
