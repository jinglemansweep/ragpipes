"""CLI utilities and environment detection."""

import os
import sys
from typing import Any


def is_ci_environment() -> bool:
    """Detect if running in CI/CD environment."""
    ci_indicators = [
        "CI",  # Generic CI
        "CONTINUOUS_INTEGRATION",  # Generic
        "GITHUB_ACTIONS",  # GitHub Actions
        "GITLAB_CI",  # GitLab CI
        "TRAVIS",  # Travis CI
        "CIRCLECI",  # CircleCI
        "JENKINS_URL",  # Jenkins
        "AZURE_PIPELINES",  # Azure DevOps
        "BITBUCKET_BUILD_NUMBER",  # Bitbucket
    ]
    return any(indicator in os.environ for indicator in ci_indicators)


def is_tty() -> bool:
    """Check if running in a TTY."""
    return sys.stdout.isatty()


def auto_detect_output_format() -> str:
    """Auto-detect appropriate output format."""
    if not is_tty() or is_ci_environment():
        return "plain"
    return "rich"


def should_disable_color() -> bool:
    """Check if colors should be disabled."""
    # Check explicit NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return True

    # Check if in CI/CD or not a TTY
    if is_ci_environment() or not is_tty():
        return True

    # Check TERM environment variable
    term = os.environ.get("TERM", "")
    if term in ["dumb", "unknown", ""]:
        return True

    return False


class RAGPipesError(Exception):
    """Base exception for RAGPipes CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        """Initialize the exception.

        Args:
            message: Error message
            exit_code: Exit code for CLI
        """
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class ConfigurationError(RAGPipesError):
    """Configuration-related errors."""

    pass


class APIError(RAGPipesError):
    """API-related errors."""

    pass


class DocumentError(RAGPipesError):
    """Document processing errors."""

    pass


async def run_async(coro: Any) -> Any:
    """Run async coroutine in sync context."""
    return await coro


def get_async_context():
    """Get async context for running coroutines."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
