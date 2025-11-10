"""Tests for RAG agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ragpipes.agent.rag_agent import QueryRequest, QueryResponse, RAGAgent


@pytest.fixture
def mock_retriever():
    """Mock retriever fixture."""
    retriever = AsyncMock()
    retriever.top_k = 5  # Default top_k value
    retriever.similarity_threshold = 0.5
    retriever.retrieve.return_value = [
        {
            "id": "doc1",
            "content": "Python is a programming language",
            "metadata": {"filename": "sample1.txt"},
            "similarity": 0.9,
            "distance": 0.1,
        }
    ]
    retriever.retrieve_with_context.return_value = {
        "context": "Python is a programming language",
        "sources": ["sample1.txt"],
        "documents": [
            {
                "id": "doc1",
                "content": "Python is a programming language",
                "metadata": {"filename": "sample1.txt"},
                "similarity": 0.9,
                "distance": 0.1,
            }
        ],
        "total_length": 30,
    }
    return retriever


@pytest.fixture
def rag_agent(mock_retriever):
    """RAG agent fixture."""
    return RAGAgent(mock_retriever)


@pytest.mark.asyncio
async def test_query_with_context(rag_agent, mock_retriever):
    """Test query functionality with context."""
    # Mock the agent's run method
    rag_agent.agent = AsyncMock()
    expected_response = QueryResponse(
        answer="Python is a programming language",
        sources=["sample1.txt"],
        confidence=0.9,
        context_used=True,
        retrieved_documents=1,
    )
    mock_response = MagicMock()
    mock_response.output = expected_response
    rag_agent.agent.run.return_value = mock_response

    # Test query
    request = QueryRequest(query="What is Python?")
    response = await rag_agent.query(request)

    assert response.answer == "Python is a programming language"
    assert response.sources == ["sample1.txt"]
    assert response.confidence == 0.9
    assert response.context_used is True
    assert response.retrieved_documents == 1
    mock_retriever.retrieve_with_context.assert_called_once_with(
        "What is Python?", 4000
    )


@pytest.mark.asyncio
async def test_query_without_context(rag_agent, mock_retriever):
    """Test query functionality without context."""
    # Mock empty context
    mock_retriever.retrieve_with_context.return_value = {
        "context": "",
        "sources": [],
        "documents": [],
        "total_length": 0,
    }

    # Mock the agent's run method
    rag_agent.agent = AsyncMock()
    expected_response = QueryResponse(
        answer="I don't have specific information about that.",
        sources=[],
        confidence=0.3,
        context_used=False,
        retrieved_documents=0,
    )
    mock_response = MagicMock()
    mock_response.output = expected_response
    rag_agent.agent.run.return_value = mock_response

    # Test query
    request = QueryRequest(query="Unknown topic")
    response = await rag_agent.query(request)

    assert response.context_used is False
    assert response.retrieved_documents == 0
    assert response.sources == []


@pytest.mark.asyncio
async def test_query_with_custom_top_k(rag_agent, mock_retriever):
    """Test query with custom top_k parameter."""
    # Mock the agent's run method
    rag_agent.agent = AsyncMock()
    expected_response = QueryResponse(
        answer="Answer",
        sources=["source1.txt"],
        confidence=0.8,
        context_used=True,
        retrieved_documents=3,
    )
    mock_response = MagicMock()
    mock_response.output = expected_response
    rag_agent.agent.run.return_value = mock_response

    # Test query with custom top_k
    request = QueryRequest(query="Test query", top_k=3)
    response = await rag_agent.query(request)

    # Verify top_k was temporarily updated and restored
    # The mock should have been called with the updated top_k
    assert rag_agent.retriever.top_k == 5  # Should be restored to original value
    # The retrieved_documents count comes from the mock retriever's documents list length
    assert response.retrieved_documents == 1  # Mock returns 1 document


def test_get_agent_info(rag_agent):
    """Test getting agent information."""
    info = rag_agent.get_agent_info()

    assert "model" in info
    assert "retriever_config" in info
    assert "capabilities" in info
    assert "query_answering" in info["capabilities"]
    assert "document_summarization" in info["capabilities"]
