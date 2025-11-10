"""Document processor for ingestion pipeline."""

import uuid
from pathlib import Path
from typing import Any

import aiofiles

from ..embeddings.external_client import ExternalEmbeddingsClient
from ..rag.chroma_store import ChromaStore


class DocumentProcessor:
    """Process and ingest documents into the RAG system."""

    def __init__(self, embeddings_client: ExternalEmbeddingsClient | None = None):
        """Initialize the document processor.

        Args:
            embeddings_client: Client for generating embeddings
        """
        self.embeddings_client = embeddings_client or ExternalEmbeddingsClient()

    async def process_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> list[dict[str, Any]]:
        """Process a single text document.

        Args:
            text: Text content to process
            metadata: Optional metadata for the document
            chunk_size: Size of text chunks for large documents
            chunk_overlap: Overlap between chunks

        Returns:
            List of processed document chunks
        """
        if not text.strip():
            return []

        # Split text into chunks if it's too long
        chunks = self._split_text(text, chunk_size, chunk_overlap)

        processed_docs = []
        for i, chunk in enumerate(chunks):
            # Generate embedding for the chunk
            embedding = await self.embeddings_client.embed_texts([chunk])
            if not embedding:
                continue

            # Create metadata
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata.update(
                {"chunk_index": i, "chunk_count": len(chunks), "chunk_size": len(chunk)}
            )

            document_id = chunk_metadata.get("document_id", str(uuid.uuid4()))

            processed_doc = {
                "id": f"{document_id}_chunk_{i}",
                "content": chunk,
                "embedding": embedding[0],
                # Flatten metadata to individual fields for ChromaDB
                "filename": chunk_metadata.get("filename", ""),
                "source": chunk_metadata.get("source", ""),
                "file_extension": chunk_metadata.get("file_extension", ""),
                "file_size": chunk_metadata.get("file_size", 0),
                "document_id": document_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
                "chunk_size": len(chunk),
            }
            processed_docs.append(processed_doc)

        return processed_docs

    async def load_documents_from_directory(
        self,
        directory: str,
        vector_store: ChromaStore,
        file_patterns: list[str] | None = None,
    ) -> int:
        """Load all text files from a directory.

        Args:
            directory: Directory path to load documents from
            vector_store: Vector store to add documents to
            file_patterns: List of file patterns to match (default: ["*.txt", "*.md"])

        Returns:
            Number of documents loaded
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"Directory {directory} does not exist")

        if not directory_path.is_dir():
            raise ValueError(f"{directory} is not a directory")

        # Default file patterns
        if file_patterns is None:
            file_patterns = ["*.txt", "*.md", "*.rst"]

        documents = []
        total_files = 0

        # Find all matching files
        for pattern in file_patterns:
            for file_path in directory_path.glob(pattern):
                if file_path.is_file():
                    try:
                        # Read file content
                        async with aiofiles.open(file_path, encoding="utf-8") as f:
                            content = await f.read()

                        if not content.strip():
                            continue

                        # Create metadata
                        metadata = {
                            "source": str(file_path),
                            "filename": file_path.name,
                            "file_extension": file_path.suffix,
                            "file_size": len(content),
                            "document_id": str(uuid.uuid4()),
                        }

                        # Process the document
                        processed_docs = await self.process_text(content, metadata)
                        documents.extend(processed_docs)
                        total_files += 1

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        continue

        # Add all documents to vector store
        if documents:
            await vector_store.add_documents(documents)
            print(
                f"Loaded {len(documents)} chunks from {total_files} files in {directory}"
            )

        return len(documents)

    async def ingest_text_file(
        self, file_path: str, vector_store: ChromaStore
    ) -> list[str]:
        """Ingest a single text file.

        Args:
            file_path: Path to the text file
            vector_store: Vector store to add documents to

        Returns:
            List of document IDs
        """
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File {file_path} does not exist")

        # Read file content
        async with aiofiles.open(path, encoding="utf-8") as f:
            content = await f.read()

        if not content.strip():
            return []

        # Create metadata
        metadata = {
            "source": str(path),
            "filename": path.name,
            "file_extension": path.suffix,
            "file_size": len(content),
            "document_id": str(uuid.uuid4()),
        }

        # Process the document
        processed_docs = await self.process_text(content, metadata)

        # Add to vector store
        doc_ids = await vector_store.add_documents(processed_docs)

        return doc_ids

    def _split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        """Split text into chunks.

        Args:
            text: Text to split
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Find the end of the current chunk
            end = start + chunk_size

            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break

            # Try to break at a sentence boundary
            chunk = text[start:end]

            # Look for sentence endings near the chunk boundary
            sentence_endings = [".", "!", "?", "\n\n"]
            best_break = -1

            for i in range(len(chunk) - 1, max(0, len(chunk) - 200), -1):
                if chunk[i] in sentence_endings:
                    best_break = i + 1
                    break

            if best_break > 0:
                chunks.append(chunk[:best_break])
                start = start + best_break - chunk_overlap
            else:
                # No good break point, just split at chunk_size
                chunks.append(chunk)
                start = end - chunk_overlap

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    async def update_document(
        self, doc_id: str, new_content: str, vector_store: ChromaStore
    ) -> bool:
        """Update an existing document.

        Args:
            doc_id: Document ID to update
            new_content: New content for the document
            vector_store: Vector store to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing document chunks
            chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(100)]  # Reasonable limit
            await vector_store.delete_documents(chunk_ids)

            # Process and add new content
            metadata = {"document_id": doc_id, "updated": True}
            processed_docs = await self.process_text(new_content, metadata)
            await vector_store.add_documents(processed_docs)

            return True
        except Exception:
            return False
