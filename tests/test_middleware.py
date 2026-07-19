"""Test middleware components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_arena.engine.tool_registry import ToolRegistry
from ai_arena.engine.tool_parser import parse_tool_call, has_tool_call
from ai_arena.engine.tool_executor import (
    ToolExecutor,
    build_tool_result_envelope,
    build_tool_error_envelope,
)


def test_tool_registry():
    reg = ToolRegistry()
    tools = reg.list_tools()
    print(f"Registered tools: {[t.name for t in tools]}")
    assert len(tools) == 5

    manual = reg.get_manual()
    assert "tool_call" in manual
    assert "read_file" in manual
    assert "write_file" in manual
    print("Tool manual generated successfully")


def test_parser():
    resp1 = "Some text before\n```tool_call\n{\"tool\": \"read_file\", \"arguments\": {\"path\": \"/tmp/test.md\"}}\n```"
    tc = parse_tool_call(resp1)
    assert tc is not None
    assert tc.tool_name == "read_file"
    print(f"Parsed tool call: {tc}")

    resp2 = "Just some text without a tool call"
    assert not has_tool_call(resp2)
    print("has_tool_call works correctly")


def test_executor():
    reg = ToolRegistry()
    executor = ToolExecutor(registry=reg, max_retries=2, session_id="test")

    p = Path("C:/Users/Mahmoud/AppData/Local/Temp/kilo/test_arena.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("hello world", encoding="utf-8")

    result = executor.execute_tool("read_file", path=str(p))
    assert result.success
    assert result.output == "hello world"
    print(f"Tool execution result: {result.output}")

    envelope = build_tool_result_envelope(result)
    assert "tool_result" in envelope
    print("Tool result envelope generated")

    # Use as_posix() to avoid backslash JSON escaping issues on Windows
    resp1 = "Some text before\n```tool_call\n{\"tool\": \"read_file\", \"arguments\": {\"path\": \"" + p.as_posix() + "\"}}\n```"
    processed, had_tool, last_result = executor.process_response(resp1)
    assert had_tool
    # On success the executor now returns the success envelope (with the
    # tool output) plus the underlying ToolResult — never an empty string.
    # Returning "" used to silently swallow the result and break the
    # orchestrator's main loop; see the 2026-07-19 debug report.
    assert processed != ""
    assert last_result is not None
    assert last_result.success
    assert "hello world" in processed
    print(f"Processed response: had_tool={had_tool}, envelope_len={len(processed)}")

    p.unlink()
    print("Executor tests passed")


def test_retry_on_failure():
    reg = ToolRegistry()
    executor = ToolExecutor(registry=reg, max_retries=2, session_id="test2")

    resp = "```tool_call\n{\"tool\": \"read_file\", \"arguments\": {\"path\": \"C:/nonexistent/file.md\"}}\n```"
    processed, had_tool, last_result = executor.process_response(resp)
    assert had_tool
    assert processed != ""  # Should return error envelope
    assert last_result is not None
    assert not last_result.success
    assert "error" in processed.lower() or "failed" in processed.lower()
    print(f"Retry test: error envelope returned correctly")


if __name__ == "__main__":
    test_tool_registry()
    test_parser()
    test_executor()
    test_retry_on_failure()
    print("\nAll middleware component tests passed!")
