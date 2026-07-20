"""File manipulation tools for AI Arena agents."""

from __future__ import annotations

import difflib
import threading
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolError, ToolResult


# Project root, computed once. Used as the resolution root for any
# *relative* path an agent hands to a file tool. Without this, ``read_file
# shared_context.txt`` only works when the process's CWD happens to be the
# project root — under Streamlit that was the actual root cause of the
# initial ``No such file or directory`` errors and the subsequent silent
# retry storm.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Sandbox: per-turn write scope
# ---------------------------------------------------------------------------
# Agents collaborate on a single shared context file. Letting them write
# anywhere on disk is both unnecessary and dangerous — a hallucinated
# ``write_file {"path": ".env", ...}`` would silently clobber secrets, and
# even a benign-looking ``poem.txt`` path (which the model often invents
# from prompt examples) pollutes the repo root.
#
# The orchestrator sets the active context path before each turn; mutating
# tools (write/append/patch) refuse to touch anything that doesn't resolve
# to that path. Reads stay unrestricted inside the project root so agents
# can still inspect documentation or their own earlier output.
_lock = threading.Lock()
_active_context_path: Path | None = None


def set_active_context_path(path: str | Path | None) -> None:
    """Set the only file mutating tools may write to for the next turn.

    Called by the orchestrator at the start of every turn with the
    session's context file. Pass ``None`` to disable the sandbox (used by
    tests that exercise tools directly without a session).
    """
    global _active_context_path
    with _lock:
        _active_context_path = Path(path).resolve() if path else None


def get_active_context_path() -> Path | None:
    """Return the currently sandboxed write target, if any."""
    with _lock:
        return _active_context_path


def _resolve_path(raw_path: str) -> Path:
    """Resolve ``raw_path`` against the project root when it is relative.

    Absolute paths are returned unchanged. This makes the file tools
    CWD-independent — a relative agent path like ``shared_context.txt``
    always lands at ``<project_root>/shared_context.txt`` no matter where
    the Streamlit / pytest / CLI process was launched from.
    """
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return _PROJECT_ROOT / p


def _enforce_write_scope(raw_path: str) -> Path | None:
    """Resolve ``raw_path`` and verify it's within the write sandbox.

    Returns:
        The resolved absolute Path if the write is allowed.

    Raises:
        ToolError: Always; ``_enforce_write_scope`` returns the path on
            success but signals rejection by raising so callers can simply
            ``return ToolResult(success=False, ...)`` from the caught
            error. (Kept as a helper so each tool doesn't reimplement the
            check.)
    """
    resolved = _resolve_path(raw_path).resolve()
    target = get_active_context_path()
    if target is None:
        # Sandbox disabled (no session bound) — allow the write so direct
        # tool usage and tests still work. The orchestrator always binds
        # a target in production, so this branch is test-only.
        return resolved
    if resolved == target:
        return resolved
    # Reject. The error text echoes the *allowed* path so the model can
    # self-correct on retry without guessing.
    raise ToolError(
        f"write rejected: '{raw_path}' is outside the session's context "
        f"file. You may only write to: {target}."
    )


def _enforce_read_scope(raw_path: str) -> Path:
    """Resolve ``raw_path`` and verify a read stays inside the project root.

    Reads are intentionally more permissive than writes (agents may inspect
    docs, sys_prompts, etc.), but they still must not escape the project
    tree — that would let a prompted agent exfiltrate ``~/.ssh/id_rsa``
    or ``/etc/passwd`` contents into the context file.

    The check only applies when a session is bound (i.e. the sandbox is
    active). Direct ``ToolExecutor`` usage in tests, without an
    orchestrator binding a context path, skips the check so legacy
    callers can still read arbitrary paths.
    """
    resolved = _resolve_path(raw_path).resolve()
    # Only enforce when the write sandbox is also active — that signals
    # we're inside a real session. Test code and CLI scripts that use
    # the tools standalone shouldn't be constrained.
    if get_active_context_path() is None:
        return resolved
    try:
        resolved.relative_to(_PROJECT_ROOT)
    except ValueError as exc:
        raise ToolError(
            f"read rejected: '{raw_path}' is outside the project root "
            f"({_PROJECT_ROOT})."
        ) from exc
    return resolved


class ReadFileTool(BaseTool):
    """Read the contents of a file."""

    name = "read_file"
    description = "Read the entire contents of a file. Use this to inspect the shared context."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read.",
            }
        },
        "required": ["path"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        try:
            resolved = _enforce_read_scope(path)
            content = resolved.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to read file: {exc}")


class WriteFileTool(BaseTool):
    """Write content to a file, overwriting existing content."""

    name = "write_file"
    description = "Write content to a file, completely replacing existing content. Use this to update the shared context."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file.",
            },
        },
        "required": ["path", "content"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        try:
            resolved = _enforce_write_scope(path)
            if resolved is None:
                return ToolResult(
                    success=False, output="",
                    error="write_file: no session context bound.",
                )
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"Successfully wrote {len(content)} characters to {path}")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to write file: {exc}")


class AppendFileTool(BaseTool):
    """Append content to the end of a file."""

    name = "append_file"
    description = "Append content to the end of a file without removing existing content. Useful for adding sections."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to append to.",
            },
            "content": {
                "type": "string",
                "description": "Content to append to the file.",
            },
        },
        "required": ["path", "content"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        try:
            resolved = _enforce_write_scope(path)
            if resolved is None:
                return ToolResult(
                    success=False, output="",
                    error="append_file: no session context bound.",
                )
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with resolved.open("a", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(success=True, output=f"Successfully appended {len(content)} characters to {path}")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to append to file: {exc}")


class PatchFileTool(BaseTool):
    """Apply a search-and-replace patch to a file."""

    name = "patch_file"
    description = "Apply a search-and-replace patch to a file. Replaces all occurrences of old_text with new_text."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to patch.",
            },
            "old_text": {
                "type": "string",
                "description": "Text to search for and replace.",
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text.",
            },
        },
        "required": ["path", "old_text", "new_text"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        old_text = kwargs.get("old_text", "")
        new_text = kwargs.get("new_text", "")
        try:
            if not old_text:
                return ToolResult(
                    success=False, output="",
                    error="patch_file requires a non-empty 'old_text' argument.",
                )
            resolved = _enforce_write_scope(path)
            if resolved is None:
                return ToolResult(
                    success=False, output="",
                    error="patch_file: no session context bound.",
                )
            if not resolved.exists():
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            content = resolved.read_text(encoding="utf-8")
            count = content.count(old_text)
            if count == 0:
                return ToolResult(success=False, output="", error=f"Pattern not found in file: {old_text[:100]}")
            new_content = content.replace(old_text, new_text)
            resolved.write_text(new_content, encoding="utf-8")
            return ToolResult(success=True, output=f"Patched {count} occurrence(s) in {path}")
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to patch file: {exc}")


class SummarizeContextTool(BaseTool):
    """Generate a summary of the current context file."""

    name = "summarize_context"
    description = "Generate a brief summary of the current context file content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the context file to summarize.",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum summary length in characters (default 500).",
            },
        },
        "required": ["path"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        max_length = kwargs.get("max_length", 500)
        try:
            resolved = _enforce_read_scope(path)
            content = resolved.read_text(encoding="utf-8")
            lines = content.strip().splitlines()
            summary_parts = []
            total = 0
            for line in lines:
                # Account for the "\n" that join() will add between lines.
                line_cost = len(line) + 1
                if total + line_cost > max_length:
                    summary_parts.append("... [truncated]")
                    break
                summary_parts.append(line)
                total += line_cost
            summary = "\n".join(summary_parts) if summary_parts else "[empty context]"
            return ToolResult(success=True, output=summary)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Failed to summarize: {exc}")


def compute_diff(old_content: str, new_content: str) -> str:
    """Compute a unified diff between two strings.

    Args:
        old_content: Original content.
        new_content: New content.

    Returns:
        Unified diff string.
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
    return "\n".join(diff)
