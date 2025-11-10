"""Pydantic AI Agent with RAG integration."""

from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ..rag.retriever import RAGRetriever


class QueryRequest(BaseModel):
    """Request model for queries."""

    query: str = Field(..., description="The user's query")
    max_context_length: int = Field(default=4000, description="Maximum context length")
    top_k: int | None = Field(
        default=None,
        description="Number of documents to retrieve (must be >= 1 if specified)",
    )


class QueryResponse(BaseModel):
    """Response model for query results."""

    answer: str = Field(..., description="The answer to the query")
    sources: list[str] = Field(..., description="List of source documents used")
    confidence: float = Field(
        ..., description="Confidence score of the answer (0.0-1.0)"
    )
    context_used: bool = Field(
        ..., description="Whether context was used in the answer"
    )
    retrieved_documents: int = Field(..., description="Number of documents retrieved")


class DocumentSummary(BaseModel):
    """Model for document summary."""

    document_id: str = Field(..., description="Document ID")
    summary: str = Field(..., description="Document summary")
    key_points: list[str] = Field(..., description="Key points from the document")


class RAGAgent:
    """RAG-enabled AI agent using Pydantic AI."""

    def __init__(
        self,
        retriever: RAGRetriever,
        model: str = "openai:gpt-4o-mini",
        system_prompt: str | None = None,
    ):
        """Initialize the RAG agent.

        Args:
            retriever: RAG retriever for document retrieval
            model: Model to use for generation
            system_prompt: Optional custom system prompt
        """
        self.retriever = retriever
        self.model = model
        self.agent = Agent(
            model,
            output_type=QueryResponse,
            system_prompt=system_prompt or self._get_system_prompt(),
        )
        self.summary_agent = Agent(
            model,
            output_type=DocumentSummary,
            system_prompt="You are a helpful assistant that summarizes documents accurately and extracts key points.",
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """
        You are a helpful AI assistant with access to a knowledge base through RAG (Retrieval-Augmented Generation).
        
        Your task is to answer questions based on the provided context. Follow these guidelines:
        
        1. Use the provided context to answer questions accurately
        2. Always cite your sources by listing the filenames or document IDs
        3. Indicate your confidence level in the answer (0.0-1.0)
        4. If the context doesn't contain sufficient information, say so clearly
        5. If you need to make assumptions, state them explicitly
        6. Provide concise but complete answers
        7. If multiple sources provide conflicting information, acknowledge the conflict
        
        Format your response as a structured answer with sources, confidence, and context usage information.
        """

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Process a query using RAG.

        Args:
            request: Query request with parameters

        Returns:
            Structured query response
        """
        # Update retriever config if provided
        original_top_k = None
        if request.top_k is not None:
            original_top_k = self.retriever.top_k
            # Ensure top_k is at least 1 to avoid ChromaDB errors
            self.retriever.top_k = max(1, request.top_k)

        try:
            # Retrieve relevant documents with context
            retrieval_result = await self.retriever.retrieve_with_context(
                request.query, request.max_context_length
            )

            context = retrieval_result["context"]
            sources = retrieval_result["sources"]
            documents = retrieval_result["documents"]

            # Create prompt with context
            if context.strip():
                prompt = f"""
                Context Information:
                {context}
                
                User Question: {request.query}
                
                Please answer the question based on the provided context. Include your sources, confidence level, and indicate whether you used the context.
                """
                context_used = True
            else:
                prompt = f"""
                User Question: {request.query}
                
                No relevant context was found. Please answer based on your general knowledge, but indicate that no specific context was available.
                """
                context_used = False

            # Get response from agent
            response = await self.agent.run(prompt)

            # The response is the result data directly for structured output
            result_data = response.output

            # Ensure sources are included even if agent doesn't provide them
            if (
                not hasattr(result_data, "sources")
                or not result_data.sources
                and sources
            ):
                # For structured output, we need to create the proper response object
                result_data.sources = sources

            # Update context_used and retrieved_documents
            result_data.context_used = context_used
            result_data.retrieved_documents = len(documents)

            return result_data

        finally:
            # Restore original top_k if it was changed
            if request.top_k is not None:
                self.retriever.top_k = original_top_k

    async def summarize_document(self, document_id: str) -> DocumentSummary:
        """Summarize a document by its ID.

        Args:
            document_id: ID of the document to summarize

        Returns:
            Document summary with key points
        """
        # Retrieve the document
        documents = await self.retriever.retrieve(f"document_id:{document_id}")

        if not documents:
            raise ValueError(f"Document {document_id} not found")

        # Combine content from all chunks
        content = "\n\n".join(doc["content"] for doc in documents)

        # Create summary prompt
        prompt = f"""
        Please summarize the following document and extract the key points:
        
        {content}
        
        Provide a concise summary and list the main key points.
        """

        # Get summary from agent
        response = await self.summary_agent.run(prompt)

        # The response is the result data directly for structured output
        result_data = response.output

        # Ensure document_id is set
        result_data.document_id = document_id

        return result_data

    async def ask_followup(
        self, original_query: str, followup_query: str, previous_response: QueryResponse
    ) -> QueryResponse:
        """Ask a followup question based on previous response.

        Args:
            original_query: The original query
            followup_query: The followup question
            previous_response: Previous response for context

        Returns:
            Response to the followup question
        """
        # Create enhanced prompt with previous context
        prompt = f"""
        Previous Question: {original_query}
        Previous Answer: {previous_response.answer}
        Previous Sources: {", ".join(previous_response.sources)}
        
        Followup Question: {followup_query}
        
        Please answer the followup question, taking into account the previous conversation context.
        """

        # Get response from agent
        response = await self.agent.run(prompt)

        # The response is the result data directly for structured output
        result_data = response.output

        # Update metadata
        result_data.context_used = True
        result_data.retrieved_documents = previous_response.retrieved_documents

        return result_data

    def update_model(self, model: str):
        """Update the model used by the agent.

        Args:
            model: New model to use
        """
        self.model = model
        self.agent = Agent(
            model, result_type=QueryResponse, system_prompt=self._get_system_prompt()
        )
        self.summary_agent = Agent(
            model,
            result_type=DocumentSummary,
            system_prompt="You are a helpful assistant that summarizes documents accurately and extracts key points.",
        )

    def get_agent_info(self) -> dict[str, Any]:
        """Get information about the agent configuration.

        Returns:
            Dictionary with agent information
        """
        return {
            "model": self.model,
            "retriever_config": {
                "top_k": self.retriever.top_k,
                "similarity_threshold": self.retriever.similarity_threshold,
            },
            "capabilities": [
                "query_answering",
                "document_summarization",
                "followup_questions",
                "source_citation",
                "confidence_scoring",
            ],
        }
