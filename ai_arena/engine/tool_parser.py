"""Tool call parser for AI Arena.

Parses structured tool calls from AI responses, handling edge cases
like markdown code blocks, extra whitespace, and partial JSON.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..tools.base import BaseTool


class ToolCallParseError(Exception):
    """Raised when a tool call cannot be parsed from a response."""
    pass


class ToolCall:
    """Represents a parsed tool call from an AI response.

    Attributes:
        tool_name: Name of the tool to execute.
        arguments: Dictionary of tool arguments.
        raw_text: Original raw text of the tool call block.
    """

    def __init__(self, tool_name: str, arguments: dict[str, Any], raw_text: str = "") -> None:
        self.tool_name = tool_name
        self.arguments = arguments
        self.raw_text = raw_text

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tool": self.tool_name,
            "arguments": self.arguments,
        }

    def __repr__(self) -> str:
        return f"ToolCall(tool={self.tool_name!r}, args={self.arguments!r})"


def _try_parse_json(json_str: str) -> Any:
    """Try to parse JSON, with fallback fixes for common AI output issues.

    Args:
        json_str: Raw JSON string.

    Returns:
        Parsed JSON data.

    Raises:
        ToolCallParseError: If JSON cannot be parsed after fixes.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fix 1: Replace unescaped backslashes in string values
    # Common issue: Windows paths like C:\Users\... without escaping
    fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', json_str)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Fix 2: Try to extract just the outer object and fix trailing commas
    fixed = re.sub(r',\s*}', '}', json_str)
    fixed = re.sub(r',\s*]', ']', fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ToolCallParseError(
        f"Failed to parse JSON after fixes. Raw: {json_str[:200]}"
    )


def parse_tool_call(response_text: str) -> ToolCall | None:
    """Parse a tool call from an AI response.

    Handles multiple formats:
    - ```tool_call ... ``` fenced code blocks
    - ```json ... ``` fenced code blocks
    - Raw JSON objects with `tool` and `arguments` keys

    Args:
        response_text: Raw text response from the AI.

    Returns:
        Parsed ToolCall, or None if no valid tool call found.

    Raises:
        ToolCallParseError: If a tool call block is found but cannot be parsed.
    """
    if not response_text or not response_text.strip():
        return None

    # Try to find tool_call fenced code blocks first
    tool_call_pattern = re.compile(
        r"```tool_call\s*\n(.*?)\n```",
        re.DOTALL | re.IGNORECASE,
    )
    match = tool_call_pattern.search(response_text)
    if match:
        json_str = match.group(1).strip()
        try:
            data = _try_parse_json(json_str)
            return _build_tool_call(data, match.group(0))
        except ToolCallParseError:
            raise
        except Exception as exc:
            raise ToolCallParseError(
                f"Failed to parse tool_call JSON: {exc}. Raw: {json_str[:200]}"
            ) from exc

    # Try generic JSON code blocks
    json_block_pattern = re.compile(
        r"```(?:json)?\s*\n(\{.*?\})\n```",
        re.DOTALL,
    )
    for match in json_block_pattern.finditer(response_text):
        json_str = match.group(1).strip()
        try:
            data = _try_parse_json(json_str)
            if "tool" in data and "arguments" in data:
                return _build_tool_call(data, match.group(0))
        except (ToolCallParseError, json.JSONDecodeError):
            continue

    # Try raw JSON object in the response
    raw_json_pattern = re.compile(r'\{[^{}]*"tool"[^{}]*\}', re.DOTALL)
    for match in raw_json_pattern.finditer(response_text):
        json_str = match.group(0).strip()
        try:
            data = _try_parse_json(json_str)
            if "tool" in data and "arguments" in data:
                return _build_tool_call(data, match.group(0))
        except (ToolCallParseError, json.JSONDecodeError):
            continue

    return None


def _build_tool_call(data: dict[str, Any], raw_text: str) -> ToolCall:
    """Build a ToolCall from parsed JSON data.

    Args:
        data: Parsed JSON dictionary.
        raw_text: Original raw text block.

    Returns:
        ToolCall instance.

    Raises:
        ToolCallParseError: If required fields are missing.
    """
    tool_name = data.get("tool", "")
    arguments = data.get("arguments", {})

    if not tool_name or not isinstance(tool_name, str):
        raise ToolCallParseError("Tool call must include a 'tool' field with the tool name.")

    if not isinstance(arguments, dict):
        raise ToolCallParseError("Tool call 'arguments' must be a JSON object.")

    return ToolCall(tool_name=tool_name, arguments=arguments, raw_text=raw_text)


def has_tool_call(response_text: str) -> bool:
    """Check if a response contains a tool call.

    Args:
        response_text: Raw text response from the AI.

    Returns:
        True if a tool call is detected.
    """
    if not response_text:
        return False
    return "```tool_call" in response_text or bool(
        re.search(r'\{[^{}]*"tool"[^{}]*\}', response_text)
    )
