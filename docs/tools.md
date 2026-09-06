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
| **Tool Executor** | `ai_arena/engine/tool_executor.py` | Executes tools (one attempt each) and audit logs every call |
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
- Make AT MOST ONE tool call per turn — the current prompt design expects a
  single `write_file` with the COMPLETE new context content
- The orchestrator executes the call right after the turn ends; the agent
  does NOT receive a `tool_result` back and must not wait for one
- There is NO retry: a failed call is logged for the user and the turn is over

## Tool Result Envelope

Tool outcomes are recorded in the session message log (visible to the user)
wrapped in a clearly labeled structure:

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
- In the one-shot flow this envelope is NOT fed back to the agent that
  produced the call — the next agent simply receives the updated file content

## Middleware Flow

For each agent turn, the app follows this one-shot middleware flow:

1. **Call the agent** with system prompt + tool manual + file content inlined in user message
2. **Detect tool calls** in the response using the parser
3. **If tool call detected (one shot — no re-call, no retry):**
   - Execute the tool once via the registry
   - Success → record envelope as system message → advance to next agent
   - Failure → record error envelope for the user → advance to next agent
4. **If no tool call** → record agent message + `[WARNING]` (no file change), advance to next agent
5. **Context file is already updated** by the tool (e.g. `write_file`)
6. **Advance to next agent** in the ping-pong loop

> **Note:** The orchestrator does NOT re-call the provider after executing a
> tool. Each turn is exactly one provider call. This prevents the "read loop"
> bug where an agent would repeatedly call `read_file` in an inner loop.

### Failure Handling

- **Attempts:** Every tool call is executed exactly once — the file
  operations are local and deterministic, so re-running identical arguments
  cannot change the outcome
- **On failure:** An error envelope is recorded in the message log (with a
  note that the call was NOT retried) and the loop advances to the next agent
- **Malformed calls:** An unparseable `tool_call` fence is treated as prose
  and triggers the standard no-write warning

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
- `old_text` (string, required) — Text to search for and replace (must be non-empty)
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

- **Writes are sandboxed to the session's context file** — while a session
  runs, `write_file` / `append_file` / `patch_file` refuse any path that
  does not resolve to the bound context file
- **Reads stay inside the project root** — `read_file` and
  `summarize_context` reject paths that escape the root (no `~/.ssh`,
  `/etc/passwd`, ...)
- **Sensitive paths are denied even inside the root** — `.env*`, `*.pem`,
  `*.key`, `secrets.toml`, the `.git` / `.streamlit` / `.venv` directories,
  and the session files under `contexts/` (`session_*.json` carries every
  agent's API key, `audit_*.log`) can never be read by agents
- All paths are resolved against the project root and symlinks/traversals
  are normalized via `Path.resolve()` before checks
- Write operations create parent directories automatically

## Audit Logging

Every tool call attempt is logged to a session-specific audit file:

```
contexts/audit_<session_id>.log
```

Log entries include:
- Timestamp
- Event type (`tool_call`, `tool_result`, `error`)
- Tool name and arguments (long string values — e.g. the full content of a
  `write_file` call — are clipped to 300 characters to keep the log bounded)
- Success/failure status
- Error details if applicable

This enables full debugging and traceability of all tool interactions.

## Tool Manual Injection

On every round, the app injects a tool usage manual into each agent's system prompt. This manual is dynamically generated from the registered tools and includes:

- Available tool names and descriptions
- Exact call format/syntax
- Expected response format
- What happens if a call is malformed

The manual ensures every AI knows how to use tools on every turn, eliminating ambiguity.
