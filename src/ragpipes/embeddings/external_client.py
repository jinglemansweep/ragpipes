"""External embeddings client for API-based embeddings."""

import os

import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""

    embeddings: list[list[float]]
    usage: dict[str, int]


class ExternalEmbeddingsClient:
    """Client for external embedding APIs (OpenAI, Cohere, etc.)."""

    def __init__(self, provider: str = "openai", api_key: str | None = None):
        """Initialize the embeddings client.

        Args:
            provider: The embedding provider ("openai" or "cohere")
            api_key: API key for the provider (if not provided, will use environment variable)
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        if not self.api_key:
            raise ValueError(f"API key not provided for {provider}")

        self.base_url = self._get_base_url()
        self.model = self._get_default_model()

    def _get_base_url(self) -> str:
        """Get the base URL for the provider."""
        if self.provider == "openai":
            return "https://api.openai.com/v1"
        elif self.provider == "cohere":
            return "https://api.cohere.ai/v1"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_default_model(self) -> str:
        """Get the default model for the provider."""
        if self.provider == "openai":
            return "text-embedding-3-small"
        elif self.provider == "cohere":
            return "embed-english-v3.0"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using the external API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        async with httpx.AsyncClient() as client:
            if self.provider == "openai":
                return await self._embed_openai(client, texts)
            elif self.provider == "cohere":
                return await self._embed_cohere(client, texts)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

    async def _embed_openai(
        self, client: httpx.AsyncClient, texts: list[str]
    ) -> list[list[float]]:
        """Embed texts using OpenAI's API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "input": texts,
            "model": self.model,
        }

        response = await client.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json=data,
            timeout=30.0,
        )
        response.raise_for_status()

        result = response.json()
        return [item["embedding"] for item in result["data"]]

    async def _embed_cohere(
        self, client: httpx.AsyncClient, texts: list[str]
    ) -> list[list[float]]:
        """Embed texts using Cohere's API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "texts": texts,
            "model": self.model,
            "input_type": "search_document",
        }

        response = await client.post(
            f"{self.base_url}/embed",
            headers=headers,
            json=data,
            timeout=30.0,
        )
        response.raise_for_status()

        result = response.json()
        return result["embeddings"]
