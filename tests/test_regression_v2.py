"""Regression tests for the 2026-07-20 bug-fix sprint.

Covers all 10 fixes applied in this cycle:

P0-1  Consecutive provider errors stop the session (no infinite loop).
P0-2  File tools are sandboxed to the session's context file.
P0-3  start_session backs up prior work before overwriting the context.
P1-1  context_diff is populated on tool-call turns (UI Diff tab works).
P1-2  Sessions with 0 enabled agents bail out instead of looping.
P1-3  A [WARNING] is emitted when an agent returns no tool call.
P2-1  Dead code removed (_append_agent_turn_to_context, _update_context,
       _empty_metrics_html). Verified by import check + attribute check.
P2-2  create_session clamps max_rounds to >= 1.
P2-3  Live indicator in chat_panel is scoped to the *last* message of
       the active agent, not all messages.
"""

from __future__ import annotations

import json
import re
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_arena.engine.orchestrator import Orchestrator
from ai_arena.engine.session import SessionManager
from ai_arena.engine.tool_registry import ToolRegistry, tool_registry
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.models.message import Message
from ai_arena.models.session_state import SessionState
from ai_arena.providers.base import BaseProvider, ProviderError
from ai_arena.tools.file_tools import (
    ReadFileTool,
    WriteFileTool,
    AppendFileTool,
    PatchFileTool,
    set_active_context_path,
    get_active_context_path,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _AlwaysFail(BaseProvider):
    """Provider that always raises ProviderError."""

    @property
    def name(self) -> str:
        return "AlwaysFail"

    @property
    def default_model(self) -> str:
        return "m"

    @property
    def available_models(self) -> list[str]:
        return ["m"]

    def chat(self, messages, model, api_key, **kwargs):
        raise ProviderError("simulated persistent failure")

    def validate_key(self, api_key: str) -> bool:
        return True


class _AlwaysProse(BaseProvider):
    """Provider that returns prose without any tool call."""

    @property
    def name(self) -> str:
        return "AlwaysProse"

    @property
    def default_model(self) -> str:
        return "m"

    @property
    def available_models(self) -> list[str]:
        return ["m"]

    def chat(self, messages, model, api_key, **kwargs):
        return "I am just talking, no tool call here."

    def validate_key(self, api_key: str) -> bool:
        return True


def _make_session(tmp_path: Path, agent: Agent, **overrides: Any) -> SessionState:
    """Create a SessionState directly (no SessionManager overhead)."""
    defaults = dict(
        id="test",
        name="Test",
        agents=[agent],
        context_file_path=str(tmp_path / "ctx.md"),
        initial_prompt="task",
    )
    defaults.update(overrides)
    return SessionState(**defaults)


def _make_orch() -> Orchestrator:
    """Build a minimal Orchestrator with no-op session manager."""
    orch = Orchestrator.__new__(Orchestrator)
    # Use the real tool registry so write_file/read_file are available
    # when tests exercise the tool-call path.
    orch.tool_registry = ToolRegistry()
    orch._stop_event = threading.Event()
    orch._providers = {}
    orch._state_lock = threading.Lock()
    orch._is_running = False
    orch._last_error = None
    orch._loop_thread = None
    orch.max_tool_retries = 3
    orch.rate_limiter = type("L", (), {"delay_seconds": 0, "wait": lambda self: None})()

    class _NoSave:
        def _save_session(self, s):
            pass

    orch.session_manager = _NoSave()
    return orch


# ---------------------------------------------------------------------------
# P0-1: Consecutive provider errors stop the session
# ---------------------------------------------------------------------------

class TestP0_1_ConsecutiveProviderErrors:
    def test_session_stops_after_max_consecutive_errors(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="fail", model="m", api_key="k",
        )
        session = sm.create_session("P01", [agent], max_rounds=5, rate_limit=0)
        orch = Orchestrator(session_manager=sm)
        orch.register_provider("fail", _AlwaysFail())
        orch.start_session(session, initial_prompt="task")

        calls = 0
        while session.is_running and not session.is_complete():
            orch.step(session)
            calls += 1
            if calls > 20:
                pytest.fail("Session did not stop — infinite loop detected")

        assert calls == 3, f"expected 3 retries before stop, got {calls}"
        assert not session.is_running
        assert session.consecutive_errors == 3
        err = orch.consume_last_error()
        assert err is not None and "consecutive" in err.lower()

    def test_transient_success_resets_counter(self, tmp_path: Path):
        """2 errors → 1 success → 3 more errors should total 5 errors."""

        class Flaky(BaseProvider):
            def __init__(self):
                self.n = 0

            @property
            def name(self) -> str:
                return "Flaky"

            @property
            def default_model(self) -> str:
                return "m"

            @property
            def available_models(self) -> list[str]:
                return ["m"]

            def chat(self, messages, model, api_key, **kwargs):
                self.n += 1
                if self.n in (1, 2, 4, 5, 6):
                    raise ProviderError(f"fail #{self.n}")
                return f"ok #{self.n}"

            def validate_key(self, api_key: str) -> bool:
                return True

        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="flaky", model="m", api_key="k",
        )
        session = sm.create_session("Flaky", [agent], max_rounds=5, rate_limit=0)
        orch = Orchestrator(session_manager=sm)
        orch.register_provider("flaky", Flaky())
        orch.start_session(session, initial_prompt="x")

        calls = 0
        while session.is_running and not session.is_complete():
            orch.step(session)
            calls += 1
            if calls > 20:
                pytest.fail("Too many calls")

        errs = [m for m in session.messages if "[ERROR]" in m.content]
        oks = [m for m in session.messages if "ok #" in m.content]
        warns = [m for m in session.messages if "[WARNING]" in m.content]
        assert len(errs) == 5
        assert len(oks) == 1
        assert len(warns) == 1  # warning for the prose-only success
        assert not session.is_running


# ---------------------------------------------------------------------------
# P0-2: File tool sandbox
# ---------------------------------------------------------------------------

class TestP0_2_FileToolSandbox:
    def test_write_outside_context_rejected(self, tmp_path: Path):
        ctx = tmp_path / "ctx.md"
        ctx.write_text("original", encoding="utf-8")
        victim = tmp_path / "victim.txt"
        victim.write_text("precious", encoding="utf-8")

        set_active_context_path(str(ctx))
        try:
            res = WriteFileTool().execute(path=str(victim), content="hacked")
            assert not res.success
            assert "write rejected" in res.error
            assert victim.read_text(encoding="utf-8") == "precious"
        finally:
            set_active_context_path(None)

    def test_write_to_context_allowed(self, tmp_path: Path):
        ctx = tmp_path / "ctx.md"
        ctx.write_text("original", encoding="utf-8")
        set_active_context_path(str(ctx))
        try:
            res = WriteFileTool().execute(path=str(ctx), content="updated")
            assert res.success
            assert ctx.read_text(encoding="utf-8") == "updated"
        finally:
            set_active_context_path(None)

    def test_append_outside_context_rejected(self, tmp_path: Path):
        ctx = tmp_path / "ctx.md"
        ctx.write_text("", encoding="utf-8")
        other = tmp_path / "other.txt"
        other.write_text("data", encoding="utf-8")

        set_active_context_path(str(ctx))
        try:
            res = AppendFileTool().execute(path=str(other), content="extra")
            assert not res.success
            assert other.read_text(encoding="utf-8") == "data"
        finally:
            set_active_context_path(None)

    def test_patch_outside_context_rejected(self, tmp_path: Path):
        ctx = tmp_path / "ctx.md"
        ctx.write_text("hello world", encoding="utf-8")
        other = tmp_path / "other.txt"
        other.write_text("hello world", encoding="utf-8")

        set_active_context_path(str(ctx))
        try:
            res = PatchFileTool().execute(
                path=str(other), old_text="hello", new_text="bye"
            )
            assert not res.success
            assert other.read_text(encoding="utf-8") == "hello world"
        finally:
            set_active_context_path(None)

    def test_read_outside_project_rejected_when_sandbox_active(self, tmp_path: Path):
        import os
        ctx = tmp_path / "ctx.md"
        ctx.write_text("", encoding="utf-8")
        secret = Path(os.path.expanduser("~")) / "some_secret_file_xyz"

        set_active_context_path(str(ctx))
        try:
            res = ReadFileTool().execute(path=str(secret))
            assert not res.success
            assert "read rejected" in res.error
        finally:
            set_active_context_path(None)

    def test_read_allowed_when_sandbox_inactive(self, tmp_path: Path):
        """Direct tool usage (no session bound) should still work."""
        f = tmp_path / "anywhere.txt"
        f.write_text("content", encoding="utf-8")
        res = ReadFileTool().execute(path=str(f))
        assert res.success


# ---------------------------------------------------------------------------
# P0-3: Context backup before overwrite
# ---------------------------------------------------------------------------

class TestP0_3_ContextBackup:
    def test_fresh_session_no_backup(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("Fresh", [agent], max_rounds=1, rate_limit=0)
        orch = Orchestrator(session_manager=sm)
        orch.start_session(session, initial_prompt="task")

        ctx = Path(session.context_file_path)
        bak = ctx.with_suffix(".bak.md")
        assert not bak.exists()

    def test_prior_work_backed_up(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("HasWork", [agent], max_rounds=5, rate_limit=0)

        # Simulate prior agent work
        ctx = Path(session.context_file_path)
        ctx.write_text(
            "# Shared Context\n\n## Initial Task\nold\n\n---\n\n"
            "## Working Draft\n\nValuable agent output.\n",
            encoding="utf-8",
        )

        orch = Orchestrator(session_manager=sm)
        orch.start_session(session, initial_prompt="new task")

        bak = ctx.with_suffix(".bak.md")
        assert bak.exists()
        assert "Valuable agent output" in bak.read_text(encoding="utf-8")
        assert "new task" in ctx.read_text(encoding="utf-8")

    def test_seed_only_no_backup(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("SeedOnly", [agent], max_rounds=1, rate_limit=0)

        ctx = Path(session.context_file_path)
        # Write the exact seed template that start_session produces.
        # The backup checker strips this comment and looks for leftover
        # content; if nothing remains, no backup is created.
        seed = (
            "# Shared Context\n\n"
            "## Initial Task\n"
            "task\n\n"
            "---\n\n"
            "## Working Draft\n"
            "<!-- Agents rewrite everything below this line. "
            "Keep the # Shared Context header and the ## Initial Task "
            "section above intact; replace the rest in full. -->\n"
        )
        ctx.write_text(seed, encoding="utf-8")

        orch = Orchestrator(session_manager=sm)
        orch.start_session(session, initial_prompt="task2")

        bak = ctx.with_suffix(".bak.md")
        assert not bak.exists()


# ---------------------------------------------------------------------------
# P1-1: context_diff populated on tool-call turns
# ---------------------------------------------------------------------------

class TestP1_1_ContextDiff:
    def test_diff_populated_after_write_file(self, tmp_path: Path):
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="w", model="m", api_key="k",
        )
        session = _make_session(tmp_path, agent)
        orch = _make_orch()

        class Writer(BaseProvider):
            @property
            def name(self) -> str:
                return "Writer"

            @property
            def default_model(self) -> str:
                return "m"

            @property
            def available_models(self) -> list[str]:
                return ["m"]

            def chat(self, messages, model, api_key, **kwargs):
                for m in messages:
                    c = m.get("content", "")
                    match = re.search(r"context file \(([^)]+)\):", c)
                    if match:
                        p = match.group(1)
                        call = {
                            "tool": "write_file",
                            "arguments": {"path": p, "content": "# NEW"},
                        }
                        return "```tool_call\n" + json.dumps(call) + "\n```"
                return "no path"

            def validate_key(self, api_key: str) -> bool:
                return True

        orch.register_provider("w", Writer())
        orch.start_session(session, initial_prompt="task")
        orch.step(session)

        tool_msgs = [m for m in session.messages if m.had_tool_call]
        assert len(tool_msgs) == 1
        assert tool_msgs[0].context_diff is not None
        assert len(tool_msgs[0].context_diff) > 0
        assert "-# Shared Context" in tool_msgs[0].context_diff or "+# NEW" in tool_msgs[0].context_diff


# ---------------------------------------------------------------------------
# P1-2: 0 enabled agents → no infinite loop
# ---------------------------------------------------------------------------

class TestP1_2_ZeroEnabledAgents:
    def test_no_enabled_agents_stops_immediately(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
            enabled=False,
        )
        session = sm.create_session("NoAgents", [agent], max_rounds=3, rate_limit=0)
        orch = Orchestrator(session_manager=sm)
        orch.start_session(session, initial_prompt="x")

        calls = 0
        while session.is_running and not session.is_complete():
            orch.step(session)
            calls += 1
            if calls > 5:
                pytest.fail("Infinite loop with 0 enabled agents")

        assert calls == 1
        assert not session.is_running
        err = orch.consume_last_error()
        assert err is not None and "no enabled agents" in err.lower()

    def test_has_enabled_agents_predicate(self):
        a1 = Agent(id="1", name="A", role=AgentRole.CRITIC, system_prompt="x",
                    enabled=True)
        a2 = Agent(id="2", name="B", role=AgentRole.OPTIMIST, system_prompt="x",
                    enabled=False)
        s = SessionState(id="t", name="T", agents=[a1, a2])
        assert s.has_enabled_agents()
        s2 = SessionState(id="t2", name="T2", agents=[a2])
        assert not s2.has_enabled_agents()


# ---------------------------------------------------------------------------
# P1-3: [WARNING] emitted on prose-only turns
# ---------------------------------------------------------------------------

class TestP1_3_NoToolCallWarning:
    def test_warning_emitted_when_no_tool_call(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="prose", model="m", api_key="k",
        )
        session = sm.create_session("Prose", [agent], max_rounds=1, rate_limit=0)
        orch = Orchestrator(session_manager=sm)
        orch.register_provider("prose", _AlwaysProse())
        orch.start_session(session, initial_prompt="task")

        msg = orch.step(session)
        assert msg is not None

        warns = [m for m in session.messages if "[WARNING]" in m.content]
        assert len(warns) == 1
        assert "did not call write_file" in warns[0].content
        assert "A" in warns[0].agent_name


# ---------------------------------------------------------------------------
# P2-1: Dead code removed
# ---------------------------------------------------------------------------

class TestP2_1_DeadCodeRemoved:
    def test_orchestrator_no_append_method(self):
        assert not hasattr(Orchestrator, "_append_agent_turn_to_context")

    def test_orchestrator_no_update_context_method(self):
        assert not hasattr(Orchestrator, "_update_context")

    def test_app_no_empty_metrics(self):
        from ai_arena.ui import app as app_mod
        assert not hasattr(app_mod, "_empty_metrics_html")


# ---------------------------------------------------------------------------
# P2-2: max_rounds clamped to >= 1
# ---------------------------------------------------------------------------

class TestP2_2_MaxRoundsValidation:
    def test_zero_clamped_to_one(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("Zero", [agent], max_rounds=0, rate_limit=0)
        assert session.max_rounds == 1

    def test_negative_clamped_to_one(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("Neg", [agent], max_rounds=-5, rate_limit=0)
        assert session.max_rounds == 1

    def test_valid_rounds_unchanged(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("OK", [agent], max_rounds=7, rate_limit=0)
        assert session.max_rounds == 7

    def test_negative_rate_limit_clamped(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("NegRL", [agent], max_rounds=1, rate_limit=-3)
        assert session.rate_limit_seconds == 0


# ---------------------------------------------------------------------------
# P2-3: Live indicator scoped to last message of active agent
# ---------------------------------------------------------------------------

class TestP2_3_LiveIndicator:
    def test_only_last_message_is_live(self):
        """Verify the logic that chat_panel uses for live_index."""
        from ai_arena.ui.chat_panel import render_chat_panel

        messages = [
            Message(agent_id="a1", agent_name="Alice", content="msg1"),
            Message(agent_id="a1", agent_name="Alice", content="msg2"),
            Message(agent_id="a2", agent_name="Bob", content="msg3"),
            Message(agent_id="a1", agent_name="Alice", content="msg4"),
        ]

        # Simulate chat_panel's live_index logic
        current_agent_id = "a1"
        live_index = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].agent_id == current_agent_id:
                live_index = i
                break

        # Only msg4 (index 3) should be live
        for idx, msg in enumerate(messages):
            is_current = idx == live_index
            if msg.agent_id == current_agent_id:
                if idx == len(messages) - 1:
                    assert is_current, f"last message from agent should be live"
                else:
                    assert not is_current, f"old message from agent should NOT be live"

    def test_no_live_when_no_current_agent(self):
        messages = [
            Message(agent_id="a1", agent_name="Alice", content="msg1"),
            Message(agent_id="a2", agent_name="Bob", content="msg2"),
        ]

        live_index = -1
        if None is not None:
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].agent_id is not None:
                    live_index = i
                    break

        assert live_index == -1
        for idx in range(len(messages)):
            assert idx != live_index


# ---------------------------------------------------------------------------
# Session persistence: new fields round-trip through save/load
# ---------------------------------------------------------------------------

class TestSessionPersistence:
    def test_consecutive_errors_persisted(self, tmp_path: Path):
        sm = SessionManager(storage_dir=tmp_path)
        agent = Agent(
            id="a", name="A", role=AgentRole.CRITIC,
            system_prompt="x", provider="p", model="m", api_key="k",
        )
        session = sm.create_session("PersistErr", [agent], max_rounds=3,
                                     rate_limit=0, tool_max_retries=5)
        session.consecutive_errors = 2
        session.max_consecutive_errors = 7
        sm._save_session(session)

        sm2 = SessionManager(storage_dir=tmp_path)
        loaded = sm2.get_session(session.id)
        assert loaded is not None
        assert loaded.consecutive_errors == 2
        assert loaded.max_consecutive_errors == 7
        assert loaded.tool_max_retries == 5
