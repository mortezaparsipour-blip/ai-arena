"""File manipulation tools for AI Arena agents."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolError, ToolResult


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
            content = Path(path).read_text(encoding="utf-8")
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
            Path(path).write_text(content, encoding="utf-8")
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
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as f:
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
            p = Path(path)
            if not p.exists():
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            content = p.read_text(encoding="utf-8")
            count = content.count(old_text)
            if count == 0:
                return ToolResult(success=False, output="", error=f"Pattern not found in file: {old_text[:100]}")
            new_content = content.replace(old_text, new_text)
            p.write_text(new_content, encoding="utf-8")
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
            content = Path(path).read_text(encoding="utf-8")
            lines = content.strip().splitlines()
            summary_parts = []
            total = 0
            for line in lines:
                if total + len(line) > max_length:
                    summary_parts.append("... [truncated]")
                    break
                summary_parts.append(line)
                total += len(line)
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
