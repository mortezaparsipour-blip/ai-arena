"""Smoke tests for the "one-shot per turn" orchestrator refactor.

Covers:
1. _build_messages injects the current file content as a fenced code
   block in the user message — agent does NOT need to call read_file.
2. _process_tool_calls executes AT MOST ONE tool call and returns,
   without re-calling the provider.
3. After a successful write_file, run_turn does NOT call
   _append_agent_turn_to_context (no double-append).
4. start_session still seeds the file with header + initial task +
   working-draft section.
5. {ctx_path} substitution works, {round} is no longer substituted.
6. session.initial_prompt persists across save/load.
"""
import sys
import json
import tempfile
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from datetime import datetime
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.models.message import Message
from ai_arena.models.session_state import SessionState
from ai_arena.engine.orchestrator import Orchestrator
from ai_arena.engine.session import SessionManager


class _NoToolRegistry:
    def get_manual(self) -> str:
        return ""


def _make_orch():
    orch = Orchestrator.__new__(Orchestrator)
    orch.tool_registry = _NoToolRegistry()
    orch._stop_event = False
    class _NoSave:
        def _save_session(self, s):
            pass
    orch.session_manager = _NoSave()
    return orch


def _make_session(tmp, agents, prompt):
    return SessionState(
        id="oneshot",
        name="OneShot",
        agents=agents,
        context_file_path=str(tmp / "ctx.md"),
        initial_prompt=prompt,
    )


def test_1_start_session_seeds_file(tmp_path):
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="Touch {ctx_path}.", provider="cerebras",
        model="m", api_key="k",
    )
    session = _make_session(tmp_path, [agent], "tell a short story")
    orch = _make_orch()

    class FakeSM:
        def _save_session(self, s):
            pass
    orch.session_manager = FakeSM()
    orch.rate_limiter = type("L", (), {"delay_seconds": 0})()
    orch._stop_event = True
    orch.start_session(session, initial_prompt="tell a short story")

    on_disk = (tmp_path / "ctx.md").read_text(encoding="utf-8")
    assert "# Shared Context" in on_disk
    assert "## Initial Task" in on_disk
    assert "tell a short story" in on_disk
    assert "---" in on_disk
    assert "## Working Draft" in on_disk
    assert session.initial_prompt == "tell a short story"
    assert session.is_running is True
    assert session.current_round == 0
    print("PASS\n")


def test_2_build_messages_inlines_file_content(tmp_path):
    """The user message must contain the file content as a fenced block —
    that's how the orchestrator injects it without the agent calling
    read_file."""
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="Touch {ctx_path}.", provider="cerebras",
        model="m", api_key="k",
    )
    session = _make_session(tmp_path, [agent], "do the thing")
    # Pre-seed the file with some working draft so we can verify it
    # shows up in the user message.
    (tmp_path / "ctx.md").write_text(
        "# Shared Context\n\n## Initial Task\ndo the thing\n\n---\n\n"
        "## Working Draft\n\ncurrent draft\n",
        encoding="utf-8",
    )
    orch = _make_orch()
    msgs = orch._build_messages(agent, session)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    user_text = msgs[1]["content"]
    assert "```" in user_text, "file content must be in a fenced code block"
    assert "current draft" in user_text, "working draft must be injected"
    assert "do the thing" in user_text, "initial task must be injected"
    assert "Read the context file" not in user_text, (
        "we tell the agent NOT to read — content is provided"
    )
    print("PASS\n")


def test_3_process_tool_calls_one_shot(tmp_path):
    """_process_tool_calls must NOT re-call the provider. It returns
    after exactly one tool call (or zero if the response has no tool)."""
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="x", provider="cerebras", model="m", api_key="k",
    )
    session = _make_session(tmp_path, [agent], "x")
    orch = _make_orch()

    # Build a fake executor that records how many times it ran.
    class FakeExecutor:
        def __init__(self):
            self.process_response_calls = 0

        def process_response(self, response_text):
            self.process_response_calls += 1
            # Pretend the model called write_file.
            from ai_arena.tools.base import ToolResult
            return (
                '```tool_result\n{"success": true, "output": "wrote 100 chars"}\n```',
                True,
                ToolResult(success=True, output="wrote 100 chars"),
            )

    fake_exec = FakeExecutor()
    response = (
        '```tool_call\n'
        '{"tool": "write_file", "arguments": {"path": "x", "content": "y"}}\n'
        '```'
    )
    final, last_result = orch._process_tool_calls(
        agent, session, fake_exec, response
    )
    assert fake_exec.process_response_calls == 1, (
        "executor must be called exactly once (no inner loop)"
    )
    assert final is not None
    assert last_result is not None
    assert last_result.success is True
    # The envelope was recorded as a system message in session.messages.
    assert any("wrote 100 chars" in m.content for m in session.messages)
    print("PASS\n")


def test_4_run_turn_no_double_append(tmp_path):
    """When the agent already called write_file, run_turn must NOT
    call _append_agent_turn_to_context — that would re-append a
    section after the agent's clean rewrite."""
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="x", provider="cerebras", model="m", api_key="k",
    )
    session = _make_session(tmp_path, [agent], "x")
    (tmp_path / "ctx.md").write_text(
        "# Shared Context\n\n## Initial Task\nx\n\n---\n\n## Working Draft\n\n",
        encoding="utf-8",
    )
    orch = _make_orch()

    # Build a fake provider that returns a write_file call.
    from ai_arena.tools.base import ToolResult

    class FakeProvider:
        def __init__(self):
            self.call_count = 0

        def __call__(self, agent, session, tool_result_envelope=None):
            self.call_count += 1
            if tool_result_envelope is not None:
                # If the orchestrator re-calls us with the envelope, we
                # would loop. With the one-shot flow this must NOT happen.
                raise AssertionError(
                    "Provider was re-called with a tool envelope — "
                    "the inner loop is back!"
                )
            return (
                '```tool_call\n'
                '{"tool": "write_file", "arguments": {"path": "'
                + session.context_file_path.replace("\\", "\\\\")
                + '", "content": "# Shared Context\\n\\n## Initial Task\\nx\\n\\n---\\n\\n## Working Draft\\n\\nNEW"}}\n'
                '```'
            )

    class FakeExecutor:
        def process_response(self, response_text):
            # Parse the write_file call from the response and actually
            # run the real WriteFileTool against the file. This is what
            # would happen in production; we want the test to see the
            # real file state, not a mocked one.
            from ai_arena.engine.tool_parser import parse_tool_call
            from ai_arena.engine.tool_executor import build_tool_result_envelope
            from ai_arena.tools.file_tools import WriteFileTool
            call = parse_tool_call(response_text)
            if call is None or call.tool_name != "write_file":
                return (response_text, False, None)
            tool = WriteFileTool()
            res = tool.execute(**call.arguments)
            envelope = build_tool_result_envelope(res)
            return (envelope, True, res)

    class FakeSM:
        def _save_session(self, s):
            pass

    orch.session_manager = FakeSM()
    orch.rate_limiter = type("L", (), {"delay_seconds": 0, "wait": lambda self: None})()
    orch._call_provider = FakeProvider()
    orch._process_tool_calls = lambda agent, session, executor, response: (
        # Call the real process_tool_calls via the orchestrator's
        # bound method, but with a fake executor.
        Orchestrator._process_tool_calls(
            orch, agent, session, FakeExecutor(), response
        )
    )

    # The agent index is 0; current_round is 0.
    session.is_running = True
    orch._stop_event = False
    msg = orch.run_turn(session)
    assert msg is not None

    # The fake provider was called EXACTLY ONCE.
    assert orch._call_provider.call_count == 1, (
        "Provider must be called once per turn — no inner re-call"
    )

    # The file should NOT have a "## A (Round" appended section —
    # the agent's write_file was the only update.
    on_disk = (tmp_path / "ctx.md").read_text(encoding="utf-8")
    assert "## A (Round" not in on_disk, (
        "no double-append: orchestrator must not append after write_file"
    )
    assert "NEW" in on_disk
    print("PASS\n")


def test_5_ctx_path_substituted_round_dropped(tmp_path):
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="Path: {ctx_path} / round={round}.",
        provider="cerebras", model="m", api_key="k",
    )
    session = _make_session(tmp_path, [agent], "x")
    orch = _make_orch()
    sys_only = orch._build_system_prompt(
        agent, session=session, inject_tools=False
    )
    assert str(tmp_path / "ctx.md") in sys_only
    assert "{round}" in sys_only
    assert "round=0" not in sys_only
    print("PASS\n")


def test_6_initial_prompt_round_trips(tmp_path):
    agent = Agent(
        id="a0", name="A", role=AgentRole.CRITIC,
        system_prompt="x", provider="cerebras", model="m", api_key="k",
    )
    sm = SessionManager(storage_dir=tmp_path)
    s = SessionState(
        id="zz", name="T", agents=[agent],
        context_file_path=str(tmp_path / "ctx.md"),
        initial_prompt="the task brief",
    )
    sm._sessions["zz"] = s
    sm._save_session(s)
    on_disk = json.loads((tmp_path / "session_zz.json").read_text(encoding="utf-8"))
    assert on_disk.get("initial_prompt") == "the task brief"
    sm2 = SessionManager(storage_dir=tmp_path)
    loaded = sm2.get_session("zz")
    assert loaded.initial_prompt == "the task brief"
    print("PASS\n")


def run_all():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        for fn in (
            test_1_start_session_seeds_file,
            test_2_build_messages_inlines_file_content,
            test_3_process_tool_calls_one_shot,
            test_4_run_turn_no_double_append,
            test_5_ctx_path_substituted_round_dropped,
            test_6_initial_prompt_round_trips,
        ):
            print(f"=== {fn.__name__} ===")
            fn(tmp_path)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    run_all()
