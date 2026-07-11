import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

print("test_tool_manual_injection start")
from ai_arena.engine.tool_registry import ToolRegistry
reg = ToolRegistry()
manual = reg.get_manual()
assert "# Tool Usage Manual" in manual
print("test_tool_manual_injection passed")

print("test_retry_logic start")
from ai_arena.engine.tool_executor import ToolExecutor
executor = ToolExecutor(registry=reg, max_retries=2, session_id="retry_test")
resp = "```tool_call\n{\"tool\": \"read_file\", \"arguments\": {\"path\": \"C:/nonexistent/file.md\"}}\n```"
processed, had_tool = executor.process_response(resp)
assert had_tool
assert processed != ""
print("test_retry_logic passed")

print("test_context_diff_tracking start")
from ai_arena.tools.file_tools import compute_diff
old = "Line 1\nLine 2\nLine 3"
new = "Line 1\nLine 2 modified\nLine 3\nLine 4 added"
diff = compute_diff(old, new)
assert "Line 2 modified" in diff or "Line 4 added" in diff
print("test_context_diff_tracking passed")

print("All non-orchestrator tests passed")
