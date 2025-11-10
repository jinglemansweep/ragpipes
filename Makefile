.PHONY: help install dev test lint format clean build docker-build docker-up docker-down docker-logs pre-commit-setup check

# Default target
help:
	@echo "Available commands:"
	@echo "  install         Install dependencies"
	@echo "  dev             Start development server"
	@echo "  test            Run tests"
	@echo "  lint            Run linting"
	@echo "  format          Format code"
	@echo "  clean           Clean build artifacts"
	@echo "  build           Build package"
	@echo "  docker-build    Build Docker image"
	@echo "  docker-up       Start services with Docker Compose"
	@echo "  docker-down     Stop services"
	@echo "  docker-logs     Show service logs"
	@echo "  pre-commit-setup Install pre-commit hooks"
	@echo "  check           Run all quality checks"

# Development
install:
	pip install -e ".[dev]"

dev:
	uvicorn src.ragpipes.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	pytest -v --cov=src --cov-report=term-missing

test-fast:
	pytest -v -x --ff

# Code quality
lint:
	ruff check src tests

format:
	ruff format src tests

format-check:
	ruff format --check src tests

pre-commit-setup:
	pre-commit install
	pre-commit install --hook-type commit-msg

check: lint format-check test

# Build and clean
clean:
	rm -rf .pytest_cache dist build *.egg-info .coverage htmlcov
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

# Docker
docker-build:
	docker build -t ragpipes:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart: docker-down docker-up

# Development helpers
reset-db:
	rm -rf data/chroma
	mkdir -p data/chroma

load-examples:
	python -c "import asyncio; from src.ragpipes.ingestion.document_processor import DocumentProcessor; from src.ragpipes.rag.chroma_store import ChromaStore; \
	async def main(): processor = DocumentProcessor(); store = ChromaStore(); await processor.load_documents_from_directory('examples/sample_documents', store); print('Example documents loaded successfully!'); asyncio.run(main())"
