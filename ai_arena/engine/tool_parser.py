"""Tool call parser for AI Arena.

Parses structured tool calls from AI responses, handling edge cases
like markdown code blocks, extra whitespace, and nested arguments.

Implementation note: previous versions used ``re`` to find JSON objects,
but ``r'\{[^{}]*"tool"[^{}]*\}'`` cannot match the nested ``arguments`` dict
that every real tool call has. We now use ``json.JSONDecoder.raw_decode`` to
walk the response and extract the next valid top-level JSON object wherever
it appears.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterator

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


# Patterns used to locate candidate tool-call blocks. We don't rely on these
# to *parse* the JSON — raw_decode handles the actual JSON work.
_TOOL_CALL_FENCE = re.compile(
    r"```tool_call\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)
_JSON_FENCE = re.compile(
    r"```(?:json)?\s*\n(.*?)\n```",
    re.DOTALL,
)


def _iter_json_objects(text: str) -> Iterator[tuple[dict[str, Any], int, int]]:
    """Yield every valid top-level JSON object found anywhere in ``text``.

    Each yielded tuple is ``(parsed_object, start_index, end_index)`` where
    ``end_index`` is exclusive (Python slice semantics).
    """
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        # Fast-forward to the next plausible object start.
        next_brace = text.find("{", idx)
        if next_brace < 0:
            return
        try:
            obj, end = decoder.raw_decode(text, next_brace)
        except json.JSONDecodeError:
            # Advance one char and keep looking — the LLM may have written
            # prose before the actual JSON object.
            idx = next_brace + 1
            continue
        if isinstance(obj, dict):
            yield obj, next_brace, end
        idx = end


def _coerce_to_dict(value: Any) -> dict[str, Any] | None:
    """Return ``value`` if it is a dict, else None.

    ``raw_decode`` may return a list, string, or number when the LLM writes
    something that starts with ``{`` but isn't a JSON object.
    """
    return value if isinstance(value, dict) else None


def _try_parse_object(json_str: str) -> dict[str, Any]:
    """Parse a JSON object string, with light-touch recovery for common LLM
    issues like trailing commas or unescaped Windows paths.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fix Windows-style paths (e.g. C:\Users\foo) by escaping lone backslashes.
    fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r"\\\\", json_str)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Strip trailing commas inside objects/arrays.
    fixed = re.sub(r",\s*([}\]])", r"\1", json_str)
    return json.loads(fixed)


def _build_tool_call(data: dict[str, Any], raw_text: str) -> ToolCall:
    """Validate a parsed dict and construct a ToolCall."""
    tool_name = data.get("tool", "")
    arguments = data.get("arguments", {})

    if not tool_name or not isinstance(tool_name, str):
        raise ToolCallParseError("Tool call must include a 'tool' field with the tool name.")

    if not isinstance(arguments, dict):
        raise ToolCallParseError("Tool call 'arguments' must be a JSON object.")

    return ToolCall(tool_name=tool_name, arguments=arguments, raw_text=raw_text)


def parse_tool_call(response_text: str) -> ToolCall | None:
    """Parse a tool call from an AI response.

    Tries, in order:
    1. ``\`\`\`tool_call ... \`\`\``` fenced block (preferred format).
    2. ``\`\`\`json ... \`\`\``` fenced block, validated as a tool call object.
    3. Raw JSON object with ``tool`` and ``arguments`` keys anywhere in the text.

    Args:
        response_text: Raw text response from the AI.

    Returns:
        Parsed ToolCall, or None if no valid tool call found.

    Raises:
        ToolCallParseError: If a tool call block is found but cannot be parsed.
    """
    if not response_text or not response_text.strip():
        return None

    # 1) Preferred: explicit tool_call fence.
    match = _TOOL_CALL_FENCE.search(response_text)
    if match:
        json_str = match.group(1).strip()
        try:
            data = _try_parse_object(json_str)
        except json.JSONDecodeError as exc:
            raise ToolCallParseError(
                f"Failed to parse tool_call JSON: {exc}. Raw: {json_str[:200]}"
            ) from exc
        return _build_tool_call(data, match.group(0))

    # 2) Generic JSON fence — only accept if it has the tool-call shape.
    for match in _JSON_FENCE.finditer(response_text):
        json_str = match.group(1).strip()
        try:
            data = _try_parse_object(json_str)
        except json.JSONDecodeError:
            continue
        if "tool" in data and "arguments" in data:
            return _build_tool_call(data, match.group(0))

    # 3) Raw JSON object anywhere in the response. Use raw_decode so nested
    #    objects/arrays don't trip up the previous regex-based approach.
    for obj, _start, _end in _iter_json_objects(response_text):
        if "tool" in obj and "arguments" in obj:
            return _build_tool_call(obj, response_text[_start:_end])

    return None


def has_tool_call(response_text: str) -> bool:
    """Check if a response contains a tool call.

    A response is considered to have a tool call if it contains a
    ``\`\`\`tool_call``` fence OR a JSON object with a ``tool`` field anywhere
    in the text.
    """
    if not response_text:
        return False
    if "```tool_call" in response_text.lower():
        return True
    for obj, _start, _end in _iter_json_objects(response_text):
        if "tool" in obj:
            return True
    return False
