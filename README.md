# RAGPipes

A Python 3.12 application with Pydantic AI and RAG (Retrieval-Augmented Generation) capabilities.

## Features

- **RAG System**: Complete retrieval-augmented generation pipeline
- **Pydantic AI**: Type-safe AI agent integration
- **ChromaDB**: Local vector storage for embeddings
- **External Embeddings**: Support for OpenAI API
- **FastAPI**: Modern web interface with automatic documentation
- **CLI Interface**: Complete command-line interface for all operations
- **Document Processing**: Automatic text chunking and ingestion
- **Type Safety**: Full Pydantic model validation
- **Production Ready**: Docker deployment, health checks, monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ragpipes
```

2. Install dependencies:
```bash
make install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start the development server:
```bash
make dev
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## Usage

### Command Line Interface

RAGPipes provides a comprehensive CLI for all operations:

#### Query the RAG System
```bash
# Basic query
ragpipes-cli query "What is Python?"

# With custom parameters
ragpipes-cli query "What is FastAPI?" --top-k 3 --max-context-length 2000

# Different output formats (using global option)
ragpipes-cli --output-format json query "Python features"
ragpipes-cli --output-format plain query "Python vs Java"
```

#### Document Ingestion
```bash
# Ingest text directly
ragpipes-cli ingest text "Python is a high-level programming language..." --filename "intro.txt"

# Ingest a file
ragpipes-cli ingest file document.txt

# Ingest entire directory
ragpipes-cli ingest dir ./examples/sample_documents

# Ingest with custom chunking
ragpipes-cli ingest text "Long document..." --chunk-size 500 --chunk-overlap 100
```

#### Document Management
```bash
# List document count
ragpipes-cli docs count

# List all documents with details
ragpipes-cli docs list

# List limited number of documents
ragpipes-cli docs list --limit 5

# List documents in JSON format
ragpipes-cli --output-format json docs list

# Clear all documents
ragpipes-cli docs clear
```

#### Server Management
```bash
# Start the API server
ragpipes-cli server start

# Start with custom host/port
ragpipes-cli server start --host 127.0.0.1 --port 9000

# Start with auto-reload for development
ragpipes-cli server start --reload

# Start in production mode
ragpipes-cli server start --host 0.0.0.0 --port 8000
```

#### CLI Configuration
```bash
# Use configuration file
ragpipes-cli --config ~/.ragpipes.toml query "What is AI?"

# Set output format globally
ragpipes-cli --output-format json docs list

# Disable colors for CI/CD
ragpipes-cli --no-color query "test"

# Enable verbose output
ragpipes-cli --verbose ingest file document.txt
```

### API Endpoints

### API Endpoints

#### Query the RAG System
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "max_context_length": 4000,
    "top_k": 5
  }'
```

#### Ingest Text
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/text" \
  -F "content=Python is a programming language..." \
  -F "metadata={\"source\": \"manual\"}"
```

#### Upload File
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/file" \
  -F "file=@document.txt"
```

#### Load Directory
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/directory" \
  -F "directory_path=./examples/sample_documents" \
  -F "file_patterns=*.txt,*.md"
```

### Python Client

```python
import asyncio
from ragpipes.agent.rag_agent import RAGAgent, QueryRequest
from ragpipes.rag.retriever import RAGRetriever
from ragpipes.rag.chroma_store import ChromaStore
from ragpipes.embeddings.external_client import ExternalEmbeddingsClient

async def main():
    # Initialize components
    embeddings_client = ExternalEmbeddingsClient()
    vector_store = ChromaStore()
    retriever = RAGRetriever(embeddings_client, vector_store)
    agent = RAGAgent(retriever)

    # Query the system
    request = QueryRequest(query="What is Python?")
    response = await agent.query(request)

    print(f"Answer: {response.answer}")
    print(f"Sources: {response.sources}")
    print(f"Confidence: {response.confidence}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Development Commands

```bash
# Install dependencies
make install

# Start development server
make dev

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Run all quality checks
make check

# Build Docker image
make docker-build

# Start with Docker Compose
make docker-up
```

### CLI Commands

```bash
# Show CLI help
ragpipes-cli --help

# Query with different formats (using global option)
ragpipes-cli --output-format rich query "What is Python?"
ragpipes-cli --output-format plain query "What is Python?"
ragpipes-cli --output-format json query "What is Python?"

# Ingest documents
ragpipes-cli ingest text "Content" --filename "doc.txt"
ragpipes-cli ingest file document.txt
ragpipes-cli ingest dir ./docs

# Document management
ragpipes-cli docs count
ragpipes-cli docs list
ragpipes-cli docs clear

# Start server
ragpipes-cli server start
```

### Project Structure

```
ragpipes/
├── src/ragpipes/           # Main package
│   ├── agent/             # Pydantic AI agent
│   ├── api/               # FastAPI routes
│   ├── cli/               # Command-line interface
│   ├── embeddings/        # External embeddings client
│   ├── ingestion/         # Document processing
│   ├── rag/              # RAG components
│   ├── settings.py       # Configuration management
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── examples/              # Sample documents
├── pyproject.toml         # Project configuration
├── Dockerfile            # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── Makefile             # Development commands
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |

| `EMBEDDINGS_PROVIDER` | Embeddings provider | `openai` |
| `CHROMA_DB_PATH` | ChromaDB storage path | `./data/chroma` |
| `PORT` | Server port | `8000` |
| `HOST` | Server host | `0.0.0.0` |
| `RAG_TOP_K` | Number of documents to retrieve | `5` |
| `RAG_SIMILARITY_THRESHOLD` | Minimum similarity score | `0.7` |
| `RAG_MAX_CONTEXT_LENGTH` | Maximum context length | `4000` |
| `CLI_SERVER_HOST` | CLI API server host | `localhost` |
| `CLI_SERVER_PORT` | CLI API server port | `8000` |
| `CLI_SERVER_SCHEME` | CLI API server scheme | `http` |
| `VERBOSE` | Enable verbose output | `false` |

### Configuration Files

You can use TOML configuration files instead of environment variables:

```toml
# ~/.ragpipes.toml or .ragpipes.toml
[api]
openai_api_key = "your-api-key"
embeddings_provider = "openai"

[server]
host = "0.0.0.0"
port = 8000

[query]
default_top_k = 5
max_context_length = 4000

[cli]
output_format = "rich"
verbose = false

[cli_server]
host = "localhost"
port = 8000
scheme = "http"
```

Use with: `ragpipes-cli --config ~/.ragpipes.toml query "What is Python?"`

## Deployment

### Docker

The Docker container runs the API server by default on port 8000.

```bash
# Build image
make docker-build

# Run with Docker Compose
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

The API will be available at `http://localhost:8000` with health check at `http://localhost:8000/api/v1/health`.

### Production

1. Set environment variables for production
2. Build and deploy Docker image
3. Configure reverse proxy (nginx)
4. Set up monitoring and logging

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_agent.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Code Quality

The project uses:
- **Ruff**: Linting and formatting
- **Pre-commit**: Git hooks for quality
- **Pydantic**: Type validation
- **pytest**: Testing framework

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API docs at `/docs`
