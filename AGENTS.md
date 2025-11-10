# RAGPipes Development Agent Instructions

## Project Overview
RAGPipes is a Python 3.12 application with Pydantic AI and RAG (Retrieval-Augmented Generation) capabilities. It provides both a FastAPI web interface and a comprehensive CLI for document ingestion, vector storage, and AI-powered query responses.

## Architecture

### Dual Interface Design
RAGPipes provides two complementary interfaces:

1. **API Server (FastAPI)**: RESTful web interface for programmatic access
2. **CLI Interface (Click)**: Command-line interface for human operators and automation

### Architecture Diagram
```
┌─────────────────┐    HTTP/REST     ┌─────────────────┐
│   CLI Interface │ ◄──────────────► │  API Server     │
│   (Client)      │                  │  (FastAPI)      │
└─────────────────┘                  └─────────┬───────┘
                                           │
                            ┌──────────────▼──────────────┐
                            │        Core Components      │
                            │  ┌───────────────────────┐ │
                            │  │ RAGAgent (Pydantic AI)│ │
                            │  │ RAGRetriever           │ │
                            │  │ ChromaStore (Vector DB) │ │
                            │  │ ExternalEmbeddingsClient │ │
                            │  │ DocumentProcessor      │ │
                            │  └───────────────────────┘ │
                            └───────────────────────────────┘
```

### CLI Architecture
The CLI is designed as a **client** that communicates with the API server via HTTP requests:

- **RAGPipesAPIClient**: HTTP client wrapper for all API operations
- **Configuration Management**: Pydantic Settings with env vars and TOML files
- **Output Formatters**: Rich, Plain, and JSON output for different environments
- **Environment Detection**: Auto-detects CI/CD environments and adjusts output

### API Architecture
The API server provides RESTful endpoints with lazy initialization:

- **Global Instances**: Shared components initialized on first use
- **Error Handling**: Structured HTTP exceptions with proper status codes
- **Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Validation**: Pydantic models for request/response validation

## Development Environment Setup

### Virtual Environment
- **CRITICAL**: The project MUST be run from the `.venv` virtual environment directory
- Always activate the virtual environment before running any commands:
  ```bash
  source .venv/bin/activate  # or: . .venv/bin/activate
  ```

### Package Management
- **REQUIRED**: Use `uv` for all package installations and dependency management
- Install dependencies: `uv sync`
- Add new packages: `uv add package_name`
- Run commands with uv: `uv run python -m module_name`

### Code Quality
- **MANDATORY**: Run `pre-commit` at the end of each unit of work
- ALL pre-commit errors and warnings MUST be fixed before considering work complete
- Run manually: `pre-commit run --all-files`

## Preferred Development Workflow

### 1. Use Makefile Helpers
Always prefer Makefile targets over direct commands:
```bash
make install          # Install dependencies
make run              # Start development server
make test             # Run tests
make lint             # Run linting
make format           # Format code
make clean            # Clean up
```

### 2. Running the Application
```bash
# From project root with activated venv
make run              # Starts server on http://localhost:8000
# OR
uv run uvicorn src.ragpipes.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Testing
```bash
make test             # Run all tests
make test-verbose     # Run with verbose output
```

### 4. Code Quality Checks
```bash
make lint             # Run ruff linting
make format           # Auto-format code
make check            # Run all quality checks
```

## Project Structure

```
src/ragpipes/
├── agent/           # Pydantic AI agent implementation
├── api/             # FastAPI routes and web interface
├── cli/             # Command-line interface (NEW)
│   ├── main.py      # CLI entry point and commands
│   ├── api_client.py # HTTP client for API communication
│   ├── utils.py     # Output formatters (Rich/Plain/JSON)
│   └── env.py       # Environment detection utilities
├── embeddings/      # External embedding client (OpenAI)
├── ingestion/       # Document processing pipeline
├── rag/             # RAG components (ChromaDB, retriever)
├── settings.py      # Configuration management (Enhanced)
└── main.py          # Application entry point
```

## Key Dependencies
- **Python 3.12+**: Required runtime
- **FastAPI**: Web framework
- **Pydantic AI**: AI agent framework
- **ChromaDB**: Vector storage
- **OpenAI**: Embedding provider
- **Click**: CLI framework
- **Rich**: Terminal formatting and progress bars
- **httpx**: Async HTTP client for CLI-API communication
- **Pydantic Settings**: Configuration management
- **uv**: Package management
- **ruff**: Linting and formatting

## Development Guidelines

### Code Style
- Follow Python 3.12+ type annotations (`list` instead of `List`, `dict` instead of `Dict`)
- Use `X | None` instead of `Optional[X]`
- Maintain existing code patterns and conventions
- No comments unless explicitly requested

### Error Handling
- Implement proper exception handling in all API endpoints
- Use structured error responses with FastAPI's HTTPException
- Validate input parameters and provide meaningful error messages

### Testing
- Write comprehensive tests for new features
- Test both success and error scenarios
- Use pytest framework (configured in pyproject.toml)

### API Development
- Follow existing FastAPI patterns in routes.py
- Use Pydantic models for request/response validation
- Implement lazy initialization for global instances
- Include proper OpenAPI documentation

## Common Commands

### Development Server
```bash
make run              # Start with auto-reload
# Access API docs at: http://localhost:8000/docs
```

### Adding Dependencies
```bash
uv add new_package    # Add to dependencies
pre-commit run --all-files  # Fix any new linting issues
```

### Database Operations
```bash
# Clear ChromaDB (if needed)
rm -rf ./data/chroma
```

### Quality Assurance
```bash
make lint             # Check for linting errors
make format           # Auto-format code
pre-commit run --all-files  # Run all quality checks
```

## Critical Reminders

1. **ALWAYS** work from activated `.venv` environment
2. **ALWAYS** use `uv` for package management
3. **ALWAYS** prefer Makefile targets
4. **ALWAYS** run `pre-commit` before completing work
5. **NEVER** commit code with linting errors or warnings
6. **NEVER** use pip directly - use uv instead

## API Endpoints Reference

- `GET /api/v1/health` - Health check
- `POST /api/v1/query` - JSON query with structured request
- `POST /api/v1/query/simple` - Form-based query
- `POST /api/v1/ingest/text` - Ingest text content
- `POST /api/v1/ingest/file` - Ingest file content
- `GET /api/v1/documents` - List document count
- `GET /api/v1/agent/info` - Agent information

## Environment Configuration

Required environment variables (see .env.example):
- `OPENAI_API_KEY` - OpenAI API key for embeddings
- `ENVIRONMENT` - Set to "development" for auto-reload
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
