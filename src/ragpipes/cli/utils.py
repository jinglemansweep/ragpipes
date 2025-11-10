"""Output formatter classes for CLI."""

import json
import sys
from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def print(self, message: str, **kwargs: Any) -> None:
        """Print a message."""
        pass

    @abstractmethod
    def success(self, message: str) -> None:
        """Print success message."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Print error message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Print warning message."""
        pass

    @abstractmethod
    def table(self, data: list[dict[str, Any]], headers: list[str]) -> None:
        """Print tabular data."""
        pass

    @abstractmethod
    def json(self, data: Any) -> None:
        """Print JSON data."""
        pass

    @abstractmethod
    def create_progress(self) -> Progress:
        """Create a progress bar."""
        pass


class RichFormatter(OutputFormatter):
    """Rich output formatter with colors and formatting."""

    def __init__(self):
        """Initialize the Rich formatter with a console."""
        self.console = Console()

    def print(self, message: str, **kwargs: Any) -> None:
        """Print a message using Rich console."""
        self.console.print(message, **kwargs)

    def success(self, message: str) -> None:
        """Print a success message with green styling."""
        self.console.print(f"✅ {message}", style="green")

    def error(self, message: str) -> None:
        """Print an error message with red styling."""
        self.console.print(f"❌ {message}", style="red")

    def warning(self, message: str) -> None:
        """Print a warning message with yellow styling."""
        self.console.print(f"⚠️  {message}", style="yellow")

    def table(self, data: list[dict[str, Any]], headers: list[str]) -> None:
        """Print tabular data as a formatted table."""
        table = Table(*headers)
        for row in data:
            table.add_row(*[str(row.get(h, "")) for h in headers])
        self.console.print(table)

    def json(self, data: Any) -> None:
        """Print JSON data with syntax highlighting."""
        self.console.print_json(data=data)

    def create_progress(self) -> Progress:
        """Create a Rich progress bar."""
        return Progress(console=self.console)


class PlainFormatter(OutputFormatter):
    """Plain text formatter for CI/CD environments."""

    def print(self, message: str, **kwargs: Any) -> None:
        """Print a plain text message."""
        print(message)

    def success(self, message: str) -> None:
        """Print a success message with SUCCESS prefix."""
        print(f"[SUCCESS] {message}")

    def error(self, message: str) -> None:
        """Print an error message with ERROR prefix."""
        print(f"[ERROR] {message}")

    def warning(self, message: str) -> None:
        """Print a warning message with WARNING prefix."""
        print(f"[WARNING] {message}")

    def table(self, data: list[dict[str, Any]], headers: list[str]) -> None:
        """Print tabular data as tab-separated values."""
        # Simple tab-separated output
        print("\t".join(headers))
        for row in data:
            print("\t".join([str(row.get(h, "")) for h in headers]))

    def json(self, data: Any) -> None:
        """Print JSON data with indentation."""
        print(json.dumps(data, indent=2))

    def create_progress(self) -> Progress:
        """Create a mock progress bar for non-interactive environments."""
        # Return a mock progress that doesn't display anything
        return MockProgress()


class JSONFormatter(OutputFormatter):
    """JSON-only formatter for programmatic use."""

    def print(self, message: str, **kwargs: Any) -> None:
        """Print a message as JSON."""
        print(json.dumps({"message": message}))

    def success(self, message: str) -> None:
        """Print a success message as JSON."""
        print(json.dumps({"status": "success", "message": message}))

    def error(self, message: str) -> None:
        """Print an error message as JSON."""
        print(json.dumps({"status": "error", "message": message}))

    def warning(self, message: str) -> None:
        """Print a warning message as JSON."""
        print(json.dumps({"status": "warning", "message": message}))

    def table(self, data: list[dict[str, Any]], headers: list[str]) -> None:
        """Print tabular data as JSON."""
        print(json.dumps({"data": data, "headers": headers}))

    def json(self, data: Any) -> None:
        """Print JSON data."""
        print(json.dumps(data))

    def create_progress(self) -> Progress:
        """Create a mock progress bar for JSON output."""
        return MockProgress()


class MockProgress:
    """Mock progress bar for non-interactive environments."""

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass

    def add_task(self, description: str, total: int | None = None) -> TaskID:
        """Add a mock task to the progress bar."""
        return TaskID(0)

    def update(self, task_id: TaskID, advance: int = 1) -> None:
        """Update mock task progress."""
        pass

    def __iter__(self):
        """Return empty iterator."""
        return iter([])


def get_formatter(output_format: str, no_color: bool = False) -> OutputFormatter:
    """Get appropriate output formatter based on settings."""
    if output_format == "json":
        return JSONFormatter()
    elif output_format == "plain" or no_color or not sys.stdout.isatty():
        return PlainFormatter()
    else:
        return RichFormatter()
