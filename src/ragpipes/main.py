"""Main application entry point."""

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("Initializing RAGPipes application...")
    print("RAGPipes application started successfully")
    yield
    print("RAGPipes application shutting down")


# Create FastAPI app
app = FastAPI(
    title="RAGPipes",
    description="A Python 3.12 application with Pydantic AI and RAG capabilities",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RAGPipes API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
    }


@app.get("/info")
async def app_info():
    """Application information endpoint."""
    return {
        "name": "RAGPipes",
        "version": "0.1.0",
        "description": "A Python 3.12 application with Pydantic AI and RAG capabilities",
        "python_version": "3.12+",
        "features": [
            "RAG (Retrieval-Augmented Generation)",
            "Pydantic AI integration",
            "ChromaDB vector storage",
            "External embeddings (OpenAI)",
            "FastAPI web interface",
            "Document ingestion pipeline",
            "Type-safe responses",
        ],
        "endpoints": {
            "health": "/api/v1/health",
            "query": "/api/v1/query",
            "ingest_text": "/api/v1/ingest/text",
            "ingest_file": "/api/v1/ingest/file",
            "documents": "/api/v1/documents",
            "agent_info": "/api/v1/agent/info",
        },
    }


def main():
    """Main entry point for the application."""
    # Get configuration from environment
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print(f"Starting RAGPipes server on {host}:{port}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Documentation available at: http://{host}:{port}/docs")

    # Run the server
    uvicorn.run(
        "ragpipes.main:app", host=host, port=port, reload=reload, log_level=log_level
    )


if __name__ == "__main__":
    main()
