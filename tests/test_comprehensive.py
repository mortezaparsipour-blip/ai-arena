"""Comprehensive test of the middleware orchestration flow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_arena.engine.tool_registry import ToolRegistry
from ai_arena.engine.tool_executor import ToolExecutor
from ai_arena.engine.session import SessionManager
from ai_arena.engine.orchestrator import Orchestrator
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.providers.openai_provider import OpenAIProvider


def test_full_middleware_flow(tmp_path: Path):
    """Test a complete middleware flow with tool calls."""
    sm = SessionManager(storage_dir=tmp_path / "sessions")
    agent1 = Agent(
        id="a1", name="Critic", role=AgentRole.CRITIC,
        system_prompt="You are a critic. Analyze the context.",
        provider="openai", model="gpt-4o", api_key="sk-test"
    )
    agent2 = Agent(
        id="a2", name="Optimist", role=AgentRole.OPTIMIST,
        system_prompt="You are an optimist. Build on the context.",
        provider="openai", model="gpt-4o", api_key="sk-test"
    )

    session = sm.create_session(
        "Middleware Test", [agent1, agent2],
        max_rounds=2, rate_limit=0, is_dry_run=True,
        context_file=str(tmp_path / "ctx.md"),
    )

    orch = Orchestrator(session_manager=sm)
    orch.register_provider("openai", OpenAIProvider())

    # Start session with initial prompt
    orch.start_session(session, initial_prompt="Test initial prompt")
    assert session.is_running
    assert session.current_round == 0
    assert session.current_agent_index == 0

    # Step 1: Agent A's first turn
    msg1 = orch.step(session)
    assert msg1 is not None
    assert session.current_agent_index == 1
    assert session.current_round == 0
    print(f"Step 1: Agent A responded, round={session.current_round}, agent_idx={session.current_agent_index}")

    # Step 2: Agent B's first turn
    msg2 = orch.step(session)
    assert msg2 is not None
    assert session.current_agent_index == 0
    assert session.current_round == 1
    print(f"Step 2: Agent B responded, round={session.current_round}, agent_idx={session.current_agent_index}")

    # Step 3: Agent A's second turn (round 2)
    msg3 = orch.step(session)
    assert msg3 is not None
    assert session.current_agent_index == 1
    assert session.current_round == 1
    print(f"Step 3: Agent A responded, round={session.current_round}, agent_idx={session.current_agent_index}")

    # Verify context file exists and has content
    ctx_path = Path(session.context_file_path)
    assert ctx_path.exists()
    content = ctx_path.read_text(encoding="utf-8")
    assert "Initial Task" in content
    assert "Test initial prompt" in content
    print("Context file verified")

    # Verify messages were recorded. Dry-run agents reply with prose
    # (no write_file), so each turn now also emits a [WARNING] system
    # message about the context not being updated — 2 messages per
    # step × 3 steps = 6 total.
    assert len(session.messages) == 6
    agent_msgs = [m for m in session.messages if not m.is_system]
    assert len(agent_msgs) == 3
    print(f"Messages recorded: {len(session.messages)} ({len(agent_msgs)} agent, "
          f"{len(session.messages) - len(agent_msgs)} system warnings)")

    # Verify dry-run responses
    assert "[DRY RUN]" in msg1.content
    assert "[DRY RUN]" in msg2.content
    assert "[DRY RUN]" in msg3.content
    print("Dry-run responses verified")

    print("\nFull middleware flow test passed!")


def test_tool_manual_injection():
    """Test that tool manual is properly generated and injected."""
    reg = ToolRegistry()
    manual = reg.get_manual()

    # Verify manual contains all required sections
    assert "# Tool Usage Manual" in manual
    assert "## Tool Call Format" in manual
    assert "## Available Tools" in manual
    assert "## What Happens After Your Tool Call" in manual
    # The manual must NOT promise a result/retry back to the agent —
    # in the one-shot flow the model never sees a tool_result.
    assert "should retry" not in manual
    assert "you will receive a result" not in manual

    # Verify all tools are documented
    for tool in reg.list_tools():
        assert tool.name in manual, f"Tool {tool.name} not in manual"
        assert tool.description in manual, f"Tool {tool.name} description not in manual"

    # Verify example calls are present
    assert "```tool_call" in manual

    print("Tool manual injection test passed!")


def test_tool_failure_single_attempt(tmp_path: Path):
    """A failing tool call is executed once and yields an error envelope."""
    reg = ToolRegistry()
    executor = ToolExecutor(registry=reg, session_id="retry_test")

    # Test with nonexistent file - should fail once, no retries
    resp = "```tool_call\n{\"tool\": \"read_file\", \"arguments\": {\"path\": \"" + (tmp_path / "missing.md").as_posix() + "\"}}\n```"
    processed, had_tool, _last_result = executor.process_response(resp)
    assert had_tool
    assert processed != ""  # Error envelope returned
    assert "failed" in processed.lower() or "error" in processed.lower()
    print("Single-attempt tool failure test passed!")


def test_context_diff_tracking():
    """Test that context diffs are properly computed."""
    from ai_arena.tools.file_tools import compute_diff

    old = "Line 1\nLine 2\nLine 3"
    new = "Line 1\nLine 2 modified\nLine 3\nLine 4 added"

    diff = compute_diff(old, new)
    assert "Line 2 modified" in diff or "Line 4 added" in diff
    print(f"Diff computed successfully:\n{diff}")
    print("Context diff tracking test passed!")


if __name__ == "__main__":
    import tempfile

    test_tool_manual_injection()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_tool_failure_single_attempt(tmp)
        test_full_middleware_flow(tmp)
    test_context_diff_tracking()
    print("\n=== ALL COMPREHENSIVE TESTS PASSED ===")
