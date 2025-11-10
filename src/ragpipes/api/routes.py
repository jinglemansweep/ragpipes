"""FastAPI routes for RAG API."""

import os
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from ..agent.rag_agent import QueryRequest, QueryResponse, RAGAgent
from ..embeddings.external_client import ExternalEmbeddingsClient
from ..ingestion.document_processor import DocumentProcessor
from ..rag.chroma_store import ChromaStore
from ..rag.retriever import RAGRetriever

router = APIRouter()

# Global instances (lazy initialization)
embeddings_client = None
vector_store = None
retriever = None
agent = None
processor = None


def get_instances():
    """Get or initialize global instances."""
    global embeddings_client, vector_store, retriever, agent, processor
    if embeddings_client is None:
        embeddings_client = ExternalEmbeddingsClient()
        vector_store = ChromaStore()
        retriever = RAGRetriever(embeddings_client, vector_store)
        agent = RAGAgent(retriever)
        processor = DocumentProcessor(embeddings_client)
    return embeddings_client, vector_store, retriever, agent, processor


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ragpipes", "version": "0.1.0"}


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system.

    Args:
        request: Query request with parameters

    Returns:
        Structured query response
    """
    try:
        _, _, _, agent_instance, _ = get_instances()
        response = await agent_instance.query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/query/simple")
async def simple_query(query: str = Form(...), max_context_length: int = Form(4000)):
    """Simple query endpoint for form data.

    Args:
        query: The query string
        max_context_length: Maximum context length

    Returns:
        Query response
    """
    try:
        _, _, _, agent_instance, _ = get_instances()
        request = QueryRequest(query=query, max_context_length=max_context_length)
        response = await agent_instance.query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/ingest/text")
async def ingest_text(
    content: str = Form(...),
    metadata: str | None = Form(None),
    filename: str | None = Form(None),
):
    """Ingest raw text content.

    Args:
        content: Text content to ingest
        metadata: JSON string of metadata
        filename: Optional filename for the document

    Returns:
        Ingestion result
    """
    try:
        import json

        # Parse metadata if provided
        doc_metadata = {}
        if metadata:
            doc_metadata = json.loads(metadata)

        # Add filename if provided
        if filename:
            doc_metadata["filename"] = filename

        # Add document ID
        doc_metadata["document_id"] = str(uuid.uuid4())

        # Get instances
        embeddings_client_instance, vector_store_instance, _, _, processor_instance = (
            get_instances()
        )

        # Process the text
        processed_docs = await processor_instance.process_text(content, doc_metadata)

        # Add to vector store
        doc_ids = await vector_store_instance.add_documents(processed_docs)

        return {
            "message": "Text ingested successfully",
            "document_id": doc_metadata["document_id"],
            "chunks_created": len(processed_docs),
            "chunk_ids": doc_ids,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """Ingest a text file.

    Args:
        file: Uploaded file

    Returns:
        Ingestion result
    """
    try:
        # Read file content
        try:
            content = await file.read()
            text_content = content.decode("utf-8")

            # Check file size (limit to 50MB)
            if len(content) > 50 * 1024 * 1024:  # 50MB limit
                raise HTTPException(status_code=413, detail="File too large")

        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400, detail="File must be UTF-8 encoded text"
            ) from e

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="File is empty")

        # Create metadata
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(text_content),
            "document_id": str(uuid.uuid4()),
        }

        # Get instances
        embeddings_client_instance, vector_store_instance, _, _, processor_instance = (
            get_instances()
        )

        # Process the document
        processed_docs = await processor_instance.process_text(text_content, metadata)

        # Add to vector store
        doc_ids = await vector_store_instance.add_documents(processed_docs)

        return {
            "message": "File ingested successfully",
            "document_id": metadata["document_id"],
            "filename": file.filename,
            "chunks_created": len(processed_docs),
            "chunk_ids": doc_ids,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/ingest/directory")
async def ingest_directory(
    background_tasks: BackgroundTasks,
    directory_path: str = Form(...),
    file_patterns: str | None = Form("*.txt,*.md,*.rst"),
):
    """Ingest all documents from a directory (background task).

    Args:
        background_tasks: FastAPI background tasks
        directory_path: Path to directory
        file_patterns: Comma-separated file patterns

    Returns:
        Task information
    """
    try:
        if not os.path.exists(directory_path):
            raise HTTPException(status_code=404, detail="Directory not found")

        if not os.path.isdir(directory_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Parse file patterns
        patterns = [p.strip() for p in (file_patterns or "*.txt,*.md,*.rst").split(",")]

        # Start background task
        task_id = str(uuid.uuid4())
        background_tasks.add_task(
            load_directory_task, task_id, directory_path, patterns
        )

        return {
            "message": "Directory ingestion started",
            "task_id": task_id,
            "directory": directory_path,
            "patterns": patterns,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


async def load_directory_task(task_id: str, directory_path: str, patterns: list[str]):
    """Background task to load directory."""
    try:
        _, vector_store_instance, _, _, processor_instance = get_instances()
        count = await processor_instance.load_documents_from_directory(
            directory_path, vector_store_instance, patterns
        )
        print(f"Task {task_id} completed: {count} chunks loaded")
    except Exception as e:
        print(f"Task {task_id} failed: {e}")


@router.get("/documents")
async def list_documents():
    """List all documents in the vector store.

    Returns:
        Document count, collection info, and document list
    """
    try:
        _, vector_store_instance, _, _, _ = get_instances()
        count = await vector_store_instance.count_documents()
        collection_info = vector_store_instance.get_collection_info()
        documents = await vector_store_instance.list_documents()

        return {
            "total_documents": count,
            "collection_info": collection_info,
            "documents": documents,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get a document by its ID.

    Args:
        document_id: Document ID

    Returns:
        Document information
    """
    try:
        _, vector_store_instance, _, _, _ = get_instances()
        document = await vector_store_instance.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document by its ID.

    Args:
        document_id: Document ID

    Returns:
        Deletion result
    """
    try:
        # Delete all chunks for this document
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(1000)]
        _, vector_store_instance, _, _, _ = get_instances()
        success = await vector_store_instance.delete_documents(chunk_ids)

        if success:
            return {
                "message": "Document deleted successfully",
                "document_id": document_id,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.delete("/documents")
async def clear_all_documents():
    """Clear all documents from the vector store.

    Returns:
        Clear result
    """
    try:
        import shutil

        from ..settings import load_settings

        settings = load_settings()
        chroma_path = settings.chroma_db_path

        # Remove ChromaDB directory
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            os.makedirs(chroma_path, exist_ok=True)

        # Re-initialize all global instances
        global embeddings_client, vector_store, retriever, agent, processor
        embeddings_client = None
        vector_store = None
        retriever = None
        agent = None
        processor = None

        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/agent/info")
async def get_agent_info():
    """Get information about the agent configuration.

    Returns:
        Agent configuration information
    """
    try:
        _, _, _, agent_instance, _ = get_instances()
        return agent_instance.get_agent_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/agent/summarize/{document_id}")
async def summarize_document(document_id: str):
    """Summarize a document.

    Args:
        document_id: Document ID to summarize

    Returns:
        Document summary
    """
    try:
        _, _, _, agent_instance, _ = get_instances()
        summary = await agent_instance.summarize_document(document_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/collections")
async def list_collections():
    """List all available collections.

    Returns:
        List of collection names
    """
    try:
        _, vector_store_instance, _, _, _ = get_instances()
        collections = await vector_store_instance.list_collections()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None
