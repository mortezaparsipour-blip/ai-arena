"""Tool executor with retry logic and audit logging for AI Arena.

Executes tool calls, handles retries on failure, logs all attempts,
and wraps results in envelopes for AI consumption.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from ..engine.tool_registry import ToolRegistry, tool_registry
from ..tools.base import ToolError, ToolResult
from .tool_parser import ToolCall, ToolCallParseError, has_tool_call, parse_tool_call


# Module-level logger so audit-log IO failures are visible in the console
# (and therefore in Streamlit logs) instead of being silently swallowed.
_log = logging.getLogger("ai_arena.audit")


class ToolExecutorError(Exception):
    """Raised when a tool cannot be executed after max retries."""
    pass


TOOL_RESULT_ENVELOPE_TEMPLATE = """```tool_result
{result_json}
```"""


def build_tool_result_envelope(result: ToolResult) -> str:
    """Wrap a tool result in a labeled envelope for AI consumption.

    Args:
        result: Tool execution result.

    Returns:
        Formatted tool result envelope string.
    """
    envelope = {
        "success": result.success,
        "output": result.output,
        "error": result.error,
    }
    return TOOL_RESULT_ENVELOPE_TEMPLATE.format(result_json=json.dumps(envelope, indent=2))


def build_tool_error_envelope(
    tool_call: ToolCall,
    error_message: str,
    attempt: int,
    max_attempts: int,
) -> str:
    """Build an error envelope for a failed tool call.

    Args:
        tool_call: The tool call that failed.
        error_message: Error description.
        attempt: Current attempt number.
        max_attempts: Maximum allowed attempts.

    Returns:
        Formatted error envelope string.
    """
    envelope = {
        "success": False,
        "tool": tool_call.tool_name,
        "arguments": tool_call.arguments,
        "error": error_message,
        "retry": {
            "attempt": attempt,
            "max_attempts": max_attempts,
            "message": f"Attempt {attempt}/{max_attempts} failed. Please correct the tool call and retry.",
        },
    }
    return TOOL_RESULT_ENVELOPE_TEMPLATE.format(result_json=json.dumps(envelope, indent=2))


class AuditLogger:
    """Logs all tool call attempts to a session-specific audit file."""

    def __init__(self, session_id: str) -> None:
        """Initialize audit logger for a session.

        Args:
            session_id: Session identifier for log file naming.
        """
        self.session_id = session_id
        self.log_path = config.context_storage_dir / f"audit_{session_id}.log"

    def log(self, event: str, details: dict[str, Any]) -> None:
        """Append an audit log entry.

        Args:
            event: Event type (e.g., 'tool_call', 'tool_result', 'error').
            details: Event details dictionary.
        """
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{event}] {json.dumps(details, default=str)}"
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError as exc:
            # Surface the failure: a full disk or permission error should
            # never be invisible. ``sys.stderr`` is captured by Streamlit
            # so the operator can still see it in the server log.
            _log.error("audit log write failed for %s: %s", self.log_path, exc)
            print(f"[audit-log] {exc}", file=sys.stderr)

    def log_tool_call(self, tool_call: ToolCall, attempt: int) -> None:
        """Log a tool call attempt."""
        self.log("tool_call", {
            "tool": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "attempt": attempt,
        })

    def log_tool_result(self, tool_call: ToolCall, result: ToolResult, attempt: int) -> None:
        """Log a tool execution result."""
        self.log("tool_result", {
            "tool": tool_call.tool_name,
            "success": result.success,
            "output_preview": result.output[:200] if result.output else "",
            "error": result.error,
            "attempt": attempt,
        })

    def log_error(self, error_message: str, context: dict[str, Any]) -> None:
        """Log an error event."""
        self.log("error", {"message": error_message, **context})


class ToolExecutor:
    """Executes tool calls with retry logic and audit logging.

    The executor:
    1. Receives an AI response
    2. Detects and parses any tool calls
    3. Executes the tool via the registry
    4. Retries on failure up to max_attempts
    5. Returns a result envelope or error envelope
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        max_retries: int = 3,
        session_id: str = "default",
    ) -> None:
        """Initialize tool executor.

        Args:
            registry: Tool registry instance. Uses global if not provided.
            max_retries: Maximum retry attempts for failed tool calls.
            session_id: Session ID for audit logging.
        """
        self.registry = registry or tool_registry
        self.max_retries = max_retries
        self.audit_logger = AuditLogger(session_id)

    def process_response(self, response_text: str) -> tuple[str, bool]:
        """Process an AI response for tool calls.

        Args:
            response_text: Raw response text from the AI.

        Returns:
            Tuple of (processed_response_text, had_tool_call).
            - If no tool call: returns original text, False
            - If tool call succeeds silently: returns "", True
            - If tool call fails after retries: returns error envelope, True
        """
        try:
            tool_call = parse_tool_call(response_text)
        except ToolCallParseError as exc:
            self.audit_logger.log_error("parse_error", {"error": str(exc), "response_preview": response_text[:200]})
            return response_text, False

        if tool_call is None:
            return response_text, False

        self.audit_logger.log_tool_call(tool_call, attempt=1)

        # Execute with retries
        result = self._execute_with_retry(tool_call)

        if result.success:
            self.audit_logger.log_tool_result(tool_call, result, attempt=1)
            return "", True
        else:
            error_envelope = build_tool_error_envelope(
                tool_call, result.error, attempt=self.max_retries, max_attempts=self.max_retries
            )
            self.audit_logger.log_error("max_retries_exceeded", {
                "tool": tool_call.tool_name,
                "error": result.error,
            })
            return error_envelope, True

    def _execute_with_retry(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call with retry logic.

        Args:
            tool_call: Parsed tool call.

        Returns:
            Final tool result (success or failure).
        """
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            tool = self.registry.get(tool_call.tool_name)
            if tool is None:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown tool: {tool_call.tool_name}. Available tools: {', '.join(t.name for t in self.registry.list_tools())}",
                )

            result = tool.execute(**tool_call.arguments)

            if result.success:
                return result

            last_error = result.error
            self.audit_logger.log_tool_result(tool_call, result, attempt=attempt)

        return ToolResult(
            success=False,
            output="",
            error=f"Tool '{tool_call.tool_name}' failed after {self.max_retries} attempts. Last error: {last_error}",
        )

    def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool directly by name.

        Args:
            tool_name: Name of the tool to execute.
            **kwargs: Tool arguments.

        Returns:
            Tool execution result.
        """
        tool = self.registry.get(tool_name)
        if tool is None:
            return ToolResult(success=False, output="", error=f"Unknown tool: {tool_name}")
        return tool.execute(**kwargs)
