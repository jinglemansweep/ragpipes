"""RAG retriever for similarity search."""

from typing import Any

from ..embeddings.external_client import ExternalEmbeddingsClient
from .chroma_store import ChromaStore


class RAGRetriever:
    """Retrieval-Augmented Generation retriever."""

    def __init__(
        self,
        embeddings_client: ExternalEmbeddingsClient,
        vector_store: ChromaStore,
        top_k: int = 5,
        similarity_threshold: float = 0.3,  # Lowered for testing
    ):
        """Initialize the RAG retriever.

        Args:
            embeddings_client: Client for generating embeddings
            vector_store: Vector store for document retrieval
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity threshold
        """
        self.embeddings_client = embeddings_client
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    async def retrieve(self, query: str) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: Query string

        Returns:
            List of relevant documents with metadata
        """
        # Generate embedding for the query
        query_embeddings = await self.embeddings_client.embed_texts([query])
        if not query_embeddings:
            return []

        query_embedding = query_embeddings[0]

        # Search vector store
        results = await self.vector_store.query(query_embedding, self.top_k)

        # Format and filter results
        documents = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []
            for i in range(len(results["ids"][0])):
                # Calculate similarity score (convert distance to similarity)
                distance = results["distances"][0][i] if results["distances"] else 1.0
                similarity = 1.0 - distance  # Convert cosine distance to similarity

                # Filter by similarity threshold
                if similarity >= self.similarity_threshold:
                    doc = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i]
                        if results["documents"]
                        else "",
                        "metadata": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "similarity": similarity,
                        "distance": distance,
                    }
                    documents.append(doc)

        return documents

    async def retrieve_with_context(
        self, query: str, max_context_length: int = 4000
    ) -> dict[str, Any]:
        """Retrieve documents and build context string.

        Args:
            query: Query string
            max_context_length: Maximum length of context string

        Returns:
            Dictionary with context string and source information
        """
        documents = await self.retrieve(query)

        # Build context string
        context_parts = []
        current_length = 0
        sources = []

        for doc in documents:
            # Format document text
            source_name = doc["metadata"].get("filename", doc["id"])
            doc_text = f"Source: {source_name}\n{doc['content']}\n\n"

            # Check if adding this document would exceed the limit
            if current_length + len(doc_text) > max_context_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)
            sources.append(source_name)

        context = "".join(context_parts)

        return {
            "context": context,
            "sources": sources,
            "documents": documents,
            "total_length": current_length,
        }

    async def hybrid_search(
        self, query: str, keywords: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search.

        Args:
            query: Query string
            keywords: Optional list of keywords to boost

        Returns:
            List of relevant documents
        """
        # Get semantic search results
        semantic_docs = await self.retrieve(query)

        # If no keywords provided, return semantic results
        if not keywords:
            return semantic_docs

        # Boost documents that contain keywords
        boosted_docs = []
        for doc in semantic_docs:
            content_lower = doc["content"].lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in content_lower)

            # Boost score based on keyword matches
            boosted_doc = doc.copy()
            if keyword_matches > 0:
                boosted_doc["similarity"] = min(
                    1.0, doc["similarity"] + (keyword_matches * 0.1)
                )
                boosted_doc["keyword_matches"] = keyword_matches
            else:
                boosted_doc["keyword_matches"] = 0

            boosted_docs.append(boosted_doc)

        # Sort by boosted similarity
        boosted_docs.sort(key=lambda x: x["similarity"], reverse=True)

        return boosted_docs

    def update_config(
        self, top_k: int | None = None, similarity_threshold: float | None = None
    ):
        """Update retriever configuration.

        Args:
            top_k: New top_k value
            similarity_threshold: New similarity threshold
        """
        if top_k is not None:
            self.top_k = top_k
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
