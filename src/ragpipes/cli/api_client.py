"""HTTP client for RAGPipes API."""

import json
from pathlib import Path
from typing import Any

import httpx


class RAGPipesAPIClient:
    """HTTP client for RAGPipes API."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize API client.

        Args:
            base_url: Base URL of RAGPipes API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()

            # Handle different response types
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return {"content": response.text}

    # Query endpoints
    def query(
        self, query: str, top_k: int = 5, max_context_length: int = 4000
    ) -> dict[str, Any]:
        """Query the RAG system.

        Args:
            query: Query text
            top_k: Number of documents to retrieve
            max_context_length: Maximum context length

        Returns:
            Query response
        """
        data = {
            "query": query,
            "top_k": top_k,
            "max_context_length": max_context_length,
        }
        return self._make_request("POST", "/api/v1/query", json=data)

    def simple_query(self, query: str) -> dict[str, Any]:
        """Simple query endpoint.

        Args:
            query: Query text

        Returns:
            Query response
        """
        data = {"query": query}
        return self._make_request("POST", "/api/v1/query/simple", data=data)

    # Ingestion endpoints
    def ingest_text(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Ingest text content.

        Args:
            content: Text content to ingest
            metadata: Optional metadata

        Returns:
            Ingestion response
        """
        data = {"content": content}
        if metadata:
            data["metadata"] = json.dumps(metadata)

        return self._make_request("POST", "/api/v1/ingest/text", data=data)

    def ingest_file(self, file_path: str) -> dict[str, Any]:
        """Ingest a file.

        Args:
            file_path: Path to file to ingest

        Returns:
            Ingestion response
        """
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "application/octet-stream")}
            return self._make_request("POST", "/api/v1/ingest/file", files=files)

    def ingest_directory(
        self, directory_path: str, file_patterns: list[str]
    ) -> dict[str, Any]:
        """Ingest a directory.

        Args:
            directory_path: Path to directory
            file_patterns: File patterns to match

        Returns:
            Ingestion response
        """
        data = {
            "directory_path": directory_path,
            "file_patterns": ",".join(file_patterns),
        }
        return self._make_request("POST", "/api/v1/ingest/directory", data=data)

    # Document management endpoints
    def list_documents(self) -> dict[str, Any]:
        """List documents.

        Returns:
            Documents list response
        """
        return self._make_request("GET", "/api/v1/documents")

    def count_documents(self) -> dict[str, Any]:
        """Count documents.

        Returns:
            Document count response
        """
        # Use list_documents endpoint and extract count
        result = self.list_documents()
        return {"total_documents": result.get("total_documents", 0)}

    def clear_documents(self) -> dict[str, Any]:
        """Clear all documents.

        Returns:
            Clear response
        """
        return self._make_request("DELETE", "/api/v1/documents")

    # Agent endpoints
    def get_agent_info(self) -> dict[str, Any]:
        """Get agent information.

        Returns:
            Agent info response
        """
        return self._make_request("GET", "/api/v1/agent/info")

    # Health check
    def health_check(self) -> dict[str, Any]:
        """Check API health.

        Returns:
            Health status
        """
        return self._make_request("GET", "/api/v1/health")

    def get_base_url(self) -> str:
        """Get the base URL.

        Returns:
            Base URL
        """
        return self.base_url
