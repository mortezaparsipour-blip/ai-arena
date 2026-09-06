"""Tool registry for AI Arena.

Single source of truth for all available tools. Adding a new tool
only requires registering it here.
"""

from __future__ import annotations

from ..tools.base import BaseTool
from ..tools.file_tools import (
    AppendFileTool,
    PatchFileTool,
    ReadFileTool,
    SummarizeContextTool,
    WriteFileTool,
)


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
            "- Make AT MOST ONE tool call per turn, and it must be `write_file` with the COMPLETE new content of the context file",
            "- The system executes your tool call immediately after your turn ends; you will NOT receive a `tool_result` back — do not wait for one",
            "- There is NO retry: if the tool call fails, the error is recorded for the user and the turn is over. Get the call right the first time",
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

        lines.append("## What Happens After Your Tool Call")
        lines.append("")
        lines.append("- The orchestrator executes the call immediately and records the outcome in the session log for the user")
        lines.append("- You will NOT see a `tool_result` in this conversation — the next agent receives the updated file content directly")
        lines.append("- A failed call is NOT retried and NOT sent back to you; end your turn after a single, correct tool call")
        lines.append("")

        return "\n".join(lines)


# Global registry instance
tool_registry = ToolRegistry()
