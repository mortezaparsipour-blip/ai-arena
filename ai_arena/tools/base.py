"""Base tool abstraction and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ToolError(Exception):
    """Raised when a tool execution fails."""
    pass


@dataclass
class ToolResult:
    """Result of a tool execution.

    Attributes:
        success: Whether the tool executed successfully.
        output: Result output string.
        error: Error message if execution failed.
        metadata: Additional metadata about the execution.
    """

    success: bool
    output: str
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for AI agent tools.

    Each tool encapsulates a capability that agents can use to
    interact with the file system or perform computations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name for function calling."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Return JSON schema for the tool parameters."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with success status and output.
        """
        pass
