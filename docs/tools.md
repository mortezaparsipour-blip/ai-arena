# Tool System Documentation

AI Arena agents interact with the shared context file through a set of typed tools. Each tool has a clear interface, validation, and error handling.

## Architecture Overview

The tool system is designed around a **middleware pattern** where the app acts as an intelligent intermediary between AI agents and the file system:

```
AI Agent A → App (Middleware) → Tool Registry → Tool Execution → Result Envelope → AI Agent A
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|---------------|
| **Tool Registry** | `ai_arena/engine/tool_registry.py` | Single source of truth for all tools |
| **Tool Parser** | `ai_arena/engine/tool_parser.py` | Parses tool calls from AI responses |
| **Tool Executor** | `ai_arena/engine/tool_executor.py` | Executes tools with retry logic and audit logging |
| **Base Tool** | `ai_arena/tools/base.py` | Abstract base class for all tools |
| **File Tools** | `ai_arena/tools/file_tools.py` | Concrete file manipulation tools |

## Tool Call Format

The app uses a structured JSON format wrapped in a `tool_call` code fence. This format is:
- **Unambiguous** — the parser can reliably detect it
- **Structured** — JSON allows precise parameter passing
- **Robust** — handles edge cases like extra whitespace, markdown wrapping, and malformed JSON

### Format Specification

````markdown
```tool_call
{
  "tool": "<tool_name>",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```
````

### Rules for Tool Calls
- Output ONLY the tool call JSON when you want to use a tool
- Do NOT wrap the JSON in extra prose
- Use valid JSON syntax with double quotes
- After a successful tool call, the system will return a `tool_result` block
- If a tool call fails, you will receive an error message and should retry with corrected arguments

## Tool Result Envelope

When returning results to an AI, the app wraps them in a clearly labeled structure:

````markdown
```tool_result
{
  "success": true,
  "output": "<result content>",
  "error": ""
}
```
````

- `success: true` means the tool executed successfully
- `success: false` means the tool failed; `error` contains the reason
- The AI checks the result and proceeds accordingly

## Middleware Flow

For each agent turn, the app follows this middleware flow:

1. **Call the agent** with system prompt + conversation history
2. **Detect tool calls** in the response using the parser
3. **If tool call detected:**
   - Execute the tool via the registry
   - If success → silently continue (no message injected)
   - If failure → retry up to `tool_max_retries` times (default: 3)
   - If max retries exceeded → return error envelope, degrade gracefully
4. **If no tool call** → forward response to next agent
5. **Update context file** with the final response
6. **Advance to next agent** in the ping-pong loop

### Retry Logic

- **Max retries:** Configurable per session via `tool_max_retries` (default: 3)
- **Retry trigger:** Malformed tool call OR tool execution failure
- **Retry mechanism:** Return error envelope to the same agent with retry instructions
- **Graceful degradation:** If max retries exceeded, log warning and continue loop with current response

## Available Tools

### read_file

Read the entire contents of a file.

**Parameters:**
- `path` (string, required) — Path to the file to read

**Returns:**
- `success: true, output: "<file contents>"`

**Example:**
```python
ReadFileTool().execute(path="shared_context.md")
```

---

### write_file

Write content to a file, completely replacing existing content.

**Parameters:**
- `path` (string, required) — Path to the file to write
- `content` (string, required) — Content to write

**Returns:**
- `success: true, output: "Successfully wrote N characters to <path>"`

**Example:**
```python
WriteFileTool().execute(path="shared_context.md", content="# New content\n...")
```

---

### append_file

Append content to the end of a file without removing existing content.

**Parameters:**
- `path` (string, required) — Path to the file to append to
- `content` (string, required) — Content to append

**Returns:**
- `success: true, output: "Successfully appended N characters to <path>"`

**Example:**
```python
AppendFileTool().execute(path="shared_context.md", content="## New Section\n...")
```

---

### patch_file

Apply a search-and-replace patch to a file.

**Parameters:**
- `path` (string, required) — Path to the file to patch
- `old_text` (string, required) — Text to search for and replace
- `new_text` (string, required) — Replacement text

**Returns:**
- `success: true, output: "Patched N occurrence(s) in <path>"`

**Example:**
```python
PatchFileTool().execute(
    path="shared_context.md",
    old_text="## Draft",
    new_text="## Final Version"
)
```

---

### summarize_context

Generate a brief summary of a file's content.

**Parameters:**
- `path` (string, required) — Path to the context file to summarize
- `max_length` (integer, optional) — Maximum summary length in characters (default: 500)

**Returns:**
- `success: true, output: "<summary text>"`

**Example:**
```python
SummarizeContextTool().execute(path="shared_context.md", max_length=300)
```

---

## Tool Result Structure

All tools return a `ToolResult` object:

```python
@dataclass
class ToolResult:
    success: bool       # Whether execution succeeded
    output: str         # Result output text
    error: str          # Error message if failed
    metadata: dict      # Additional execution metadata
```

## Creating Custom Tools

To add a new tool:

1. Create a class inheriting from `BaseTool`
2. Implement `name`, `description`, `parameters`, and `execute`
3. Register it in `ToolRegistry._register_defaults()` or via `registry.register()`

```python
from ai_arena.tools.base import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"}
        },
        "required": ["param1"],
    }

    def execute(self, **kwargs):
        param1 = kwargs.get("param1", "")
        try:
            result = do_something(param1)
            return ToolResult(success=True, output=result)
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))
```

Then register it:
```python
from ai_arena.engine.tool_registry import tool_registry
tool_registry.register(MyCustomTool())
```

## Tool Security

Tools execute on the local file system. To prevent abuse:
- All paths are resolved relative to the project root
- Write operations create parent directories automatically
- No path traversal outside the project directory is allowed

## Audit Logging

Every tool call attempt is logged to a session-specific audit file:

```
contexts/audit_<session_id>.log
```

Log entries include:
- Timestamp
- Event type (`tool_call`, `tool_result`, `error`)
- Tool name and arguments
- Success/failure status
- Error details if applicable

This enables full debugging and traceability of all tool interactions.

## Tool Manual Injection

Before round 1 of each session, the app automatically injects a tool usage manual into each agent's system prompt. This manual is dynamically generated from the registered tools and includes:

- Available tool names and descriptions
- Exact call format/syntax
- Expected response format
- What happens if a call is malformed

The manual ensures every AI knows how to use tools before the session starts, eliminating ambiguity.
