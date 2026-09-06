"""Tool executor with audit logging for AI Arena.

Executes tool calls — exactly one attempt each. In the one-shot flow the
model never sees the tool result, so re-running identical arguments on a
deterministic failure (rejected path, malformed arguments) is pure waste.
Every attempt is logged, and results are wrapped in envelopes for the
session message log.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any

from ..config import config
from ..engine.tool_registry import ToolRegistry, tool_registry
from ..tools.base import ToolResult
from .tool_parser import ToolCall, ToolCallParseError, parse_tool_call


# Module-level logger so audit-log IO failures are visible in the console
# (and therefore in Streamlit logs) instead of being silently swallowed.
_log = logging.getLogger("ai_arena.audit")

# Long values are clipped in the audit log. ``write_file`` arguments carry
# the entire context file, so logging them raw would make the log grow
# unbounded and duplicate anything an agent exfiltrated into a write call.
# The log is for auditing tool activity, not for mirroring file contents.
MAX_AUDIT_ARG_CHARS = 300


def _truncate(value: Any) -> Any:
    """Return ``value`` clipped to ``MAX_AUDIT_ARG_CHARS`` when it is a long string."""
    if isinstance(value, str) and len(value) > MAX_AUDIT_ARG_CHARS:
        return value[:MAX_AUDIT_ARG_CHARS] + f"...[truncated, {len(value)} chars total]"
    return value


def _truncate_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Return tool-call arguments with every long string value clipped."""
    return {key: _truncate(value) for key, value in arguments.items()}


TOOL_RESULT_ENVELOPE_TEMPLATE = """```tool_result
{result_json}
```"""


def build_tool_result_envelope(result: ToolResult) -> str:
    """Wrap a tool result in a labeled envelope for the message log.

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


def build_tool_error_envelope(tool_call: ToolCall, error_message: str) -> str:
    """Build an error envelope for a failed tool call.

    In the one-shot flow the failing agent never sees this envelope — it is
    recorded in the message log for the user. The wording must not promise
    a retry that never happens.

    Args:
        tool_call: The tool call that failed.
        error_message: Error description.

    Returns:
        Formatted error envelope string.
    """
    envelope = {
        "success": False,
        "tool": tool_call.tool_name,
        "arguments": _truncate_arguments(tool_call.arguments),
        "error": error_message,
        "note": (
            "The tool call failed and was NOT retried. The error was recorded "
            "for the user; the session continues with the current file state."
        ),
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
        """Log a tool call attempt (long argument values clipped)."""
        self.log("tool_call", {
            "tool": tool_call.tool_name,
            "arguments": _truncate_arguments(tool_call.arguments),
            "attempt": attempt,
        })

    def log_tool_result(self, tool_call: ToolCall, result: ToolResult, attempt: int) -> None:
        """Log a tool execution result (long output/error clipped)."""
        self.log("tool_result", {
            "tool": tool_call.tool_name,
            "success": result.success,
            "output_preview": _truncate(result.output) if result.output else "",
            "error": _truncate(result.error),
            "attempt": attempt,
        })

    def log_error(self, error_message: str, context: dict[str, Any]) -> None:
        """Log an error event."""
        self.log("error", {"message": error_message, **context})


class ToolExecutor:
    """Executes tool calls — one attempt each — with audit logging.

    The executor:
    1. Receives an AI response
    2. Detects and parses any tool calls
    3. Executes the tool exactly once via the registry
    4. Returns a result envelope or error envelope for the message log
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        session_id: str = "default",
    ) -> None:
        """Initialize tool executor.

        Args:
            registry: Tool registry instance. Uses global if not provided.
            session_id: Session ID for audit logging.
        """
        self.registry = registry or tool_registry
        self.audit_logger = AuditLogger(session_id)

    def process_response(
        self, response_text: str
    ) -> tuple[str, bool, ToolResult | None]:
        """Process an AI response for tool calls.

        Args:
            response_text: Raw response text from the AI.

        Returns:
            Tuple of (processed_response_text, had_tool_call, last_result).
            - If no tool call: returns (original_text, False, None)
            - If tool call succeeds: returns (success_envelope, True, result)
            - If tool call fails: returns (error_envelope, True, result)

            The envelope is the *envelope string* recorded in the session
            message log for the user — in the one-shot flow it is never fed
            back to the agent that produced it. Returning the ``ToolResult``
            lets the orchestrator branch on ``result.success`` without
            re-parsing the envelope.
        """
        try:
            tool_call = parse_tool_call(response_text)
        except ToolCallParseError as exc:
            self.audit_logger.log_error("parse_error", {"error": str(exc), "response_preview": response_text[:200]})
            return response_text, False, None

        if tool_call is None:
            return response_text, False, None

        self.audit_logger.log_tool_call(tool_call, attempt=1)

        result = self._execute_tool_call(tool_call)
        self.audit_logger.log_tool_result(tool_call, result, attempt=1)

        if result.success:
            return build_tool_result_envelope(result), True, result

        error_envelope = build_tool_error_envelope(tool_call, result.error)
        self.audit_logger.log_error("tool_execution_failed", {
            "tool": tool_call.tool_name,
            "error": result.error,
        })
        return error_envelope, True, result

    def _execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call exactly once, without retrying.

        Tool operations are local file operations; their failures (bad
        path, rejected scope, malformed arguments) are deterministic, and
        the one-shot flow never returns a result to the model — retrying
        identical arguments would only burn I/O.

        Args:
            tool_call: Parsed tool call.

        Returns:
            The tool result, success or failure.
        """
        tool = self.registry.get(tool_call.tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_call.tool_name}. Available tools: {', '.join(t.name for t in self.registry.list_tools())}",
            )
        return tool.execute(**tool_call.arguments)

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
