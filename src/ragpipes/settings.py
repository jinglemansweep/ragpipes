"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGPipesSettings(BaseSettings):
    """Application settings with Pydantic validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Allow extra fields for compatibility
        case_sensitive=False,
    )

    def __init__(self, **kwargs: Any):
        """Initialize settings with config file and legacy environment variable support."""
        # Map legacy environment variables to new field names
        legacy_mappings = {
            "OPENAI_API_KEY": "openai_api_key",
            "PYDANTIC_AI_MODEL": "default_model",
            "CHROMA_DB_PATH": "chroma_db_path",
            "EMBEDDINGS_PROVIDER": "embeddings_provider",
            "RAG_TOP_K": "default_top_k",
            "RAG_SIMILARITY_THRESHOLD": "similarity_threshold",
            "RAG_MAX_CONTEXT_LENGTH": "max_context_length",
            "CHUNK_SIZE": "chunk_size",
            "CHUNK_OVERLAP": "chunk_overlap",
            "MAX_FILE_SIZE_MB": "max_file_size_mb",
            "PORT": "port",
            "HOST": "host",
            "ENVIRONMENT": "environment",
            "LOG_LEVEL": "log_level",
            "CLI_SERVER_HOST": "cli_server_host",
            "CLI_SERVER_PORT": "cli_server_port",
            "CLI_SERVER_SCHEME": "cli_server_scheme",
        }

        # Check for legacy environment variables and map them
        for legacy_env, field_name in legacy_mappings.items():
            if legacy_env in os.environ and field_name not in kwargs:
                kwargs[field_name] = os.environ[legacy_env]

        # Handle config file loading
        config_file = kwargs.get("config_file") or self._find_config_file()
        if config_file and Path(config_file).exists():
            # Load TOML config file
            try:
                import toml

                with open(config_file, encoding="utf-8") as f:
                    config_data = toml.load(f)

                # Flatten nested TOML structure for Pydantic
                flattened_data = {}
                for section, values in config_data.items():
                    if isinstance(values, dict):
                        for key, value in values.items():
                            flattened_data[f"{section}_{key}"] = value
                    else:
                        flattened_data[section] = values

                # Merge with kwargs (CLI args take precedence)
                kwargs = {**flattened_data, **kwargs}
            except Exception:
                # If config file fails to load, continue with defaults
                pass

        super().__init__(**kwargs)

    # Application Configuration
    version: str = Field("0.1.0", description="Application version")

    # API Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")

    default_model: str = Field("openai:gpt-4o-mini", description="Default AI model")
    embeddings_provider: str = Field("openai", description="Embeddings provider")

    # Ingestion Configuration
    chunk_size: int = Field(
        1000, description="Default chunk size for document processing"
    )
    chunk_overlap: int = Field(200, description="Default chunk overlap")
    max_file_size_mb: int = Field(50, description="Maximum file size in MB")
    supported_formats: list[str] = Field(
        [".txt", ".md", ".py", ".rst"], description="Supported file formats"
    )

    # Query Configuration
    default_top_k: int = Field(5, description="Default number of documents to retrieve")
    similarity_threshold: float = Field(0.7, description="Similarity threshold")
    max_context_length: int = Field(4000, description="Maximum context length")

    # Server Configuration
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    auto_reload: bool = Field(True, description="Enable auto-reload in development")
    environment: str = Field("development", description="Environment")
    log_level: str = Field("INFO", description="Log level")

    # CLI Server Connection
    cli_server_host: str = Field("127.0.0.1", description="CLI server connection host")
    cli_server_port: int = Field(8000, description="CLI server connection port")
    cli_server_scheme: str = Field("http", description="CLI server connection scheme")

    # Database Configuration
    chroma_db_path: str = Field("./data/chroma", description="ChromaDB storage path")

    # CLI Configuration
    output_format: str = Field("rich", description="Output format: rich, plain, json")
    no_color: bool = Field(False, description="Disable colored output")
    verbose: bool = Field(False, description="Enable verbose output")

    # Config file paths
    config_file: str | None = Field(None, description="Path to configuration file")

    def _find_config_file(self) -> str | None:
        """Find configuration file in standard locations."""
        config_paths = [
            ".ragpipes.toml",
            "ragpipes.toml",
            "~/.ragpipes/config.toml",
            "~/.config/ragpipes/config.toml",
        ]

        for path in config_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)

        return None

    def get_output_format(self) -> str:
        """Get effective output format considering environment."""
        if self.no_color or os.environ.get("NO_COLOR"):
            return "plain"
        return self.output_format

    def is_verbose(self) -> bool:
        """Check if verbose output is enabled."""
        return self.verbose or os.environ.get("VERBOSE", "").lower() in (
            "1",
            "true",
            "yes",
        )


def load_settings(config_file: str | None = None, **overrides: Any) -> RAGPipesSettings:
    """Load settings with optional overrides."""
    return RAGPipesSettings(config_file=config_file, **overrides)
