"""Tests for ChromaDB store."""

import shutil
import tempfile

import pytest

from ragpipes.rag.chroma_store import ChromaStore


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def chroma_store(temp_chroma_dir):
    """ChromaDB store fixture."""
    return ChromaStore(persist_directory=temp_chroma_dir)


@pytest.mark.asyncio
async def test_add_documents(chroma_store):
    """Test adding documents to the store."""
    documents = [
        {
            "content": "Test document 1",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"source": "test1.txt"},
        },
        {
            "content": "Test document 2",
            "embedding": [0.4, 0.5, 0.6],
            "metadata": {"source": "test2.txt"},
        },
    ]

    doc_ids = await chroma_store.add_documents(documents)

    assert len(doc_ids) == 2
    assert all(isinstance(doc_id, str) for doc_id in doc_ids)


@pytest.mark.asyncio
async def test_add_empty_documents(chroma_store):
    """Test adding empty document list."""
    doc_ids = await chroma_store.add_documents([])
    assert doc_ids == []


@pytest.mark.asyncio
async def test_query_documents(chroma_store):
    """Test querying documents."""
    # Add test documents
    documents = [
        {
            "content": "Python programming language",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"source": "python.txt"},
        }
    ]
    await chroma_store.add_documents(documents)

    # Query
    results = await chroma_store.query([0.1, 0.2, 0.3], n_results=1)

    assert "ids" in results
    assert "documents" in results
    assert "metadatas" in results
    assert "distances" in results


@pytest.mark.asyncio
async def test_get_document_by_id(chroma_store):
    """Test getting document by ID."""
    # Add test document
    documents = [
        {
            "id": "test_doc_1",
            "content": "Test content",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"source": "test.txt"},
        }
    ]
    await chroma_store.add_documents(documents)

    # Get document
    doc = await chroma_store.get_document_by_id("test_doc_1")

    assert doc is not None
    assert doc["id"] == "test_doc_1"
    assert doc["content"] == "Test content"
    assert doc["metadata"]["source"] == "test.txt"


@pytest.mark.asyncio
async def test_get_nonexistent_document(chroma_store):
    """Test getting non-existent document."""
    doc = await chroma_store.get_document_by_id("nonexistent")
    assert doc is None


@pytest.mark.asyncio
async def test_delete_documents(chroma_store):
    """Test deleting documents."""
    # Add test documents
    documents = [
        {
            "id": "doc_to_delete",
            "content": "Delete me",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {},
        }
    ]
    await chroma_store.add_documents(documents)

    # Delete document
    success = await chroma_store.delete_documents(["doc_to_delete"])
    assert success is True


@pytest.mark.asyncio
async def test_count_documents(chroma_store):
    """Test counting documents."""
    # Initially should be 0
    count = await chroma_store.count_documents()
    assert count == 0

    # Add documents
    documents = [
        {"content": "Doc 1", "embedding": [0.1, 0.2, 0.3], "metadata": {}},
        {"content": "Doc 2", "embedding": [0.4, 0.5, 0.6], "metadata": {}},
    ]
    await chroma_store.add_documents(documents)

    # Count should be 2
    count = await chroma_store.count_documents()
    assert count == 2


def test_get_collection_info(chroma_store):
    """Test getting collection information."""
    info = chroma_store.get_collection_info()

    assert "name" in info
    assert "count" in info
    assert "metadata" in info
    assert info["name"] == "documents"
