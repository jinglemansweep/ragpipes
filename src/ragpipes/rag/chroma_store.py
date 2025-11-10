"""ChromaDB vector store implementation."""

import os
import uuid
from typing import Any

import chromadb


class ChromaStore:
    """ChromaDB implementation for vector storage."""

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str | None = None,
    ):
        """Initialize ChromaDB store.

        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_DB_PATH", "./data/chroma"
        )

        # Ensure the persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    async def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to the vector store.

        Args:
            documents: List of document dictionaries with 'content', 'embedding', and optional 'metadata'

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        # Generate IDs if not provided
        ids = []
        embeddings = []
        metadatas = []
        contents = []

        for i, doc in enumerate(documents):
            # Generate unique ID if not provided
            doc_id = doc.get("id") or str(uuid.uuid4())
            ids.append(doc_id)

            # Extract embedding
            if "embedding" not in doc:
                raise ValueError(f"Document {i} missing required 'embedding' field")
            embeddings.append(doc["embedding"])

            # Extract content
            if "content" not in doc:
                raise ValueError(f"Document {i} missing required 'content' field")
            contents.append(doc["content"])

            # Extract metadata (exclude embedding and content)
            metadata = {
                k: v for k, v in doc.items() if k not in ["embedding", "content", "id"]
            }
            metadatas.append(metadata)

        # Add to ChromaDB
        self.collection.add(
            ids=ids, embeddings=embeddings, metadatas=metadatas, documents=contents
        )

        return ids

    async def query(
        self, query_embedding: list[float], n_results: int = 5
    ) -> dict[str, Any]:
        """Query the vector store for similar documents.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return

        Returns:
            Dictionary containing query results
        """
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=n_results
        )

        return results

    async def get_document_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found
        """
        try:
            results = self.collection.get(ids=[doc_id])
            if not results["ids"]:
                return None

            # Return the first (and only) result
            return {
                "id": results["ids"][0],
                "content": results["documents"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {},
            }
        except Exception:
            return None

    async def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete documents by their IDs.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=doc_ids)
            return True
        except Exception:
            return False

    async def count_documents(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            Number of documents
        """
        return self.collection.count()

    async def list_collections(self) -> list[str]:
        """List all available collections.

        Returns:
            List of collection names
        """
        return [collection.name for collection in self.client.list_collections()]

    def get_collection_info(self) -> dict[str, Any]:
        """Get information about the current collection.

        Returns:
            Collection information
        """
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata,
        }
