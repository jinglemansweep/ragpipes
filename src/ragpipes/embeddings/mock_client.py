"""Mock embeddings client for testing."""

import random
from typing import list


class MockEmbeddingsClient:
    """Mock embeddings client for testing purposes."""

    def __init__(self, provider: str = "mock", api_key: str | None = None):
        """Initialize mock embeddings client."""
        self.provider = provider
        self.api_key = api_key

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for texts."""
        # Generate random embeddings of dimension 1536 (same as OpenAI)
        embeddings = []
        for text in texts:
            # Generate deterministic but pseudo-random embeddings based on text hash
            random.seed(hash(text) % (2**32))
            embedding = [random.random() for _ in range(1536)]
            embeddings.append(embedding)
        return embeddings
