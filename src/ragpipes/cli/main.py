"""Main CLI entry point for RAGPipes."""

import click

from ragpipes.cli.env import (
    auto_detect_output_format,
    should_disable_color,
)
from ragpipes.cli.utils import JSONFormatter, get_formatter
from ragpipes.settings import load_settings


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--output-format",
    type=click.Choice(["rich", "plain", "json"]),
    help="Output format",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.version_option(version="0.1.0", prog_name="ragpipes")
@click.pass_context
def cli(
    ctx: click.Context,
    config: str | None,
    output_format: str | None,
    no_color: bool,
    verbose: bool,
) -> None:
    """RAGPipes CLI - RAG (Retrieval-Augmented Generation) command-line interface."""
    try:
        # Auto-detect settings if not specified
        if output_format is None:
            output_format = auto_detect_output_format()
        if no_color is None:
            no_color = should_disable_color()

        # Load settings with proper precedence
        settings = load_settings(config_file=config)

        # Override with command-line options
        if output_format:
            settings.output_format = output_format
        if no_color:
            settings.no_color = True
            settings.output_format = "plain"
        if verbose:
            settings.verbose = True

        # Store settings and formatter in context
        ctx.ensure_object(dict)
        ctx.obj["settings"] = settings
        ctx.obj["formatter"] = get_formatter(settings.output_format, settings.no_color)

        if settings.verbose:
            formatter = ctx.obj["formatter"]
            formatter.print(f"RAGPipes v{settings.version}")
            formatter.print(f"Output format: {settings.output_format}")
            if config:
                formatter.print(f"Config file: {config}")

    except Exception as e:
        raise click.ClickException(f"Failed to initialize CLI: {e}") from e


@cli.command()
@click.argument("query")
@click.option(
    "--top-k",
    type=int,
    help="Number of documents to retrieve",
)
@click.option(
    "--max-context-length",
    type=int,
    help="Maximum context length",
)
@click.option(
    "--no-context",
    is_flag=True,
    help="Disable RAG context",
)
@click.pass_context
def query(
    ctx: click.Context,
    query: str,
    top_k: int | None,
    max_context_length: int | None,
    no_context: bool,
) -> None:
    """Query the RAG system."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Prepare query parameters
        query_top_k = 0 if no_context else (top_k or settings.default_top_k)
        query_max_context = max_context_length or settings.max_context_length

        # Execute query via API
        result = client.query(
            query=query, top_k=query_top_k, max_context_length=query_max_context
        )

        # Format output using global formatter
        if isinstance(formatter, JSONFormatter):
            formatter.json(result)
        else:
            formatter.print(f"Query: {query}")
            formatter.print(f"Answer: {result.get('answer', 'No answer')}")

            sources = result.get("sources", [])
            if sources:
                formatter.print("Sources:")
                for source in sources:
                    formatter.print(f"  - {source}")

            confidence = result.get("confidence")
            if confidence:
                formatter.print(f"Confidence: {confidence}")

            context_used = result.get("context_used")
            if context_used is not None:
                formatter.print(f"Context used: {context_used}")

            retrieved_docs = result.get("retrieved_documents")
            if retrieved_docs is not None:
                formatter.print(f"Documents retrieved: {retrieved_docs}")

    except Exception as e:
        formatter.error(f"Query failed: {e}")
        raise click.ClickException(str(e)) from e


@cli.group()
def ingest() -> None:
    """Document ingestion commands."""
    pass


@ingest.command()
@click.argument("text")
@click.option(
    "--filename",
    help="Filename for the document",
)
@click.option(
    "--metadata",
    help="JSON metadata string",
)
@click.pass_context
def text(
    ctx: click.Context, text: str, filename: str | None, metadata: str | None
) -> None:
    """Ingest raw text content."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        import json

        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Parse metadata
        doc_metadata = {}
        if metadata:
            doc_metadata = json.loads(metadata)

        if filename:
            doc_metadata["filename"] = filename

        # Ingest text via API
        client.ingest_text(text, doc_metadata if doc_metadata else None)

        formatter.success("Text ingested successfully")
        if filename:
            formatter.print(f"Filename: {filename}")

    except Exception as e:
        formatter.error(f"Text ingestion failed: {e}")
        raise click.ClickException(str(e)) from e


@ingest.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def file(ctx: click.Context, file_path: str) -> None:
    """Ingest a single file."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Ingest file via API
        client.ingest_file(file_path)

        formatter.success(f"File ingested successfully: {file_path}")

    except Exception as e:
        formatter.error(f"File ingestion failed: {e}")
        raise click.ClickException(str(e)) from e


@ingest.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--patterns",
    multiple=True,
    default=(),
    help="File patterns to match",
)
@click.pass_context
def dir(ctx: click.Context, directory: str, patterns: tuple[str, ...]) -> None:
    """Ingest all files from a directory."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Use default patterns if none provided
        patterns_list = (
            list(patterns) if patterns else ["*.txt", "*.md", "*.py", "*.rst"]
        )

        # Ingest directory via API
        client.ingest_directory(directory, patterns_list)

        formatter.success(f"Directory ingested successfully: {directory}")
        formatter.print(f"Patterns: {', '.join(patterns_list)}")

    except Exception as e:
        formatter.error(f"Directory ingestion failed: {e}")
        raise click.ClickException(str(e)) from e


@cli.group()
def docs() -> None:
    """Document management commands."""
    pass


@docs.command()
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Maximum number of documents to show (default: all)",
)
@click.pass_context
def list(ctx: click.Context, limit: int | None) -> None:
    """List all documents."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Get documents via API
        result = client.list_documents()

        if settings.output_format == "json":
            formatter.json(result)
        else:
            total_docs = result.get("total_documents", 0)
            collection_info = result.get("collection_info", {})
            collection = collection_info.get("name", "unknown")
            documents = result.get("documents", [])

            formatter.print(f"Total documents: {total_docs}")
            formatter.print(f"Collection: {collection}")

            if documents:
                # Apply limit if specified
                if limit is not None:
                    documents = documents[:limit]

                formatter.print("\nDocuments:")
                for i, doc in enumerate(documents, 1):
                    # Show document ID and metadata
                    metadata_str = ""
                    if doc.get("metadata"):
                        metadata_parts = []
                        for key, value in doc["metadata"].items():
                            if key not in ["embedding"]:  # Skip embedding in display
                                metadata_parts.append(f"{key}={value}")
                        if metadata_parts:
                            metadata_str = f" ({', '.join(metadata_parts)})"

                    # Show content preview (first 100 characters)
                    content_preview = doc.get("content", "")[:100]
                    if len(doc.get("content", "")) > 100:
                        content_preview += "..."

                    formatter.print(f"  {i}. ID: {doc['id']}{metadata_str}")
                    formatter.print(f"     Content: {content_preview}")
                    if i < len(documents):
                        formatter.print("")
            else:
                formatter.print("No documents found.")

    except Exception as e:
        formatter.error(f"Failed to list documents: {e}")
        raise click.ClickException(str(e)) from e


@docs.command()
@click.pass_context
def count(ctx: click.Context) -> None:
    """Count total documents."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Get count via API
        result = client.count_documents()

        if settings.output_format == "json":
            formatter.json(result)
        else:
            count = result.get("total_documents", 0)
            formatter.print(f"Total documents: {count}")

    except Exception as e:
        formatter.error(f"Failed to count documents: {e}")
        raise click.ClickException(str(e)) from e


@docs.command()
@click.confirmation_option(prompt="Are you sure you want to clear all documents?")
@click.pass_context
def clear(ctx: click.Context) -> None:
    """Clear all documents."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    try:
        from ragpipes.cli.api_client import RAGPipesAPIClient

        # Create API client
        base_url = f"{settings.cli_server_scheme}://{settings.cli_server_host}:{settings.cli_server_port}"
        client = RAGPipesAPIClient(base_url)

        # Clear documents via API
        client.clear_documents()

        formatter.success("All documents cleared")

    except Exception as e:
        formatter.error(f"Failed to clear documents: {e}")
        raise click.ClickException(str(e)) from e


@cli.group()
def server() -> None:
    """Server management commands."""
    pass


@server.command()
@click.option(
    "--host",
    help="Server host",
)
@click.option(
    "--port",
    type=int,
    help="Server port",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload",
)
@click.pass_context
def start(
    ctx: click.Context, host: str | None, port: int | None, reload: bool | None
) -> None:
    """Start the API server."""
    settings = ctx.obj["settings"]
    formatter = ctx.obj["formatter"]

    # Override settings with command-line options
    if host:
        settings.host = host
    if port:
        settings.port = port
    if reload is not None:
        settings.auto_reload = reload

    try:
        import uvicorn

        formatter.print(f"Starting RAGPipes server on {settings.host}:{settings.port}")
        formatter.print(f"Documentation: http://{settings.host}:{settings.port}/docs")

        uvicorn.run(
            "ragpipes.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.auto_reload,
        )

    except Exception as e:
        formatter.error(f"Failed to start server: {e}")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
