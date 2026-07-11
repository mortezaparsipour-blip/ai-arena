"""Tool registry for AI Arena.

Single source of truth for all available tools. Adding a new tool
only requires registering it here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..tools.base import BaseTool, ToolResult
from ..tools.file_tools import (
    AppendFileTool,
    PatchFileTool,
    ReadFileTool,
    SummarizeContextTool,
    WriteFileTool,
    compute_diff,
)

if TYPE_CHECKING:
    pass


class ToolRegistry:
    """Central registry for all available agent tools.

    Tools are registered once and used by the parser, executor,
    manual generator, and audit logger.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the default file manipulation tools."""
        self.register(ReadFileTool())
        self.register(WriteFileTool())
        self.register(AppendFileTool())
        self.register(PatchFileTool())
        self.register(SummarizeContextTool())

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its name.

        Args:
            tool: Tool instance to register.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def get_manual(self) -> str:
        """Generate the tool usage manual for injection into system prompts.

        Returns:
            Markdown-formatted tool manual.
        """
        lines = [
            "# Tool Usage Manual",
            "",
            "You have access to the following tools. Use them to interact with the shared context file.",
            "",
            "## Tool Call Format",
            "",
            "To call a tool, output a JSON block wrapped in a code fence with the label `tool_call`:",
            "",
            "```tool_call",
            '{"tool": "<tool_name>", "arguments": {"param1": "value1", "param2": "value2"}}',
            "```",
            "",
            "Rules for tool calls:",
            "- Output ONLY the tool call JSON when you want to use a tool",
            "- Do NOT wrap the JSON in extra prose",
            "- Use valid JSON syntax with double quotes",
            "- After a successful tool call, the system will return a `tool_result` block with the outcome",
            "- If a tool call fails, you will receive an error message and should retry with corrected arguments",
            "",
            "## Available Tools",
            "",
        ]

        for tool in self.list_tools():
            lines.append(f"### {tool.name}")
            lines.append(f"{tool.description}")
            lines.append("")
            lines.append("**Parameters:**")
            params = tool.parameters.get("properties", {})
            required = tool.parameters.get("required", [])
            for param_name, param_schema in params.items():
                req_mark = " *(required)*" if param_name in required else ""
                desc = param_schema.get("description", "")
                lines.append(f"- `{param_name}`{req_mark}: {desc}")
            lines.append("")
            lines.append("**Example call:**")
            example_args = {}
            for param_name, param_schema in params.items():
                example_args[param_name] = f"<{param_name}_value>"
            example_json = '{"tool": "' + tool.name + '", "arguments": ' + str(example_args).replace("'", '"') + '}'
            lines.append("```tool_call")
            lines.append(example_json)
            lines.append("```")
            lines.append("")

        lines.append("## Tool Result Format")
        lines.append("")
        lines.append("After a tool call, you will receive a result in this format:")
        lines.append("")
        lines.append("```tool_result")
        lines.append('{"success": true, "output": "<result content>", "error": ""}')
        lines.append("```")
        lines.append("")
        lines.append("- `success: true` means the tool executed successfully")
        lines.append("- `success: false` means the tool failed; `error` contains the reason")
        lines.append("- Always check the result and proceed accordingly")
        lines.append("")

        return "\n".join(lines)


# Global registry instance
tool_registry = ToolRegistry()
