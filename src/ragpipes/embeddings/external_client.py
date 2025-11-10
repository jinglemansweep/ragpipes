"""External embeddings client for API-based embeddings."""

import os

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""

    embeddings: list[list[float]]
    usage: dict[str, int]


class ExternalEmbeddingsClient:
    """Client for OpenAI embeddings API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the OpenAI embeddings client.

        Args:
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.base_url = "https://api.openai.com/v1"
        self.model = "text-embedding-3-small"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using OpenAI's API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        async with httpx.AsyncClient() as client:
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
