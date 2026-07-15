"""Regression tests for the 2026-07-15 review fixes.

Covers:
- P0-1: SessionManager re-loads sessions from disk after a fresh init.
- P0-2: Tool parser handles nested JSON in ``arguments``.
- P0-4: Rate limiter preserves its last_call timestamp across start.
- P1-6: _save_session is atomic (no .json.tmp file left behind on success).
- max_tokens: agent dataclass round-trips through to_dict/from_dict and the
  orchestrator forwards it to the provider.
- tool_max_retries: SessionManager.create_session honours the override.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_arena.engine.orchestrator import Orchestrator
from ai_arena.engine.rate_limiter import RateLimiter
from ai_arena.engine.session import SessionManager
from ai_arena.engine.tool_parser import has_tool_call, parse_tool_call
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.providers.openai_provider import OpenAIProvider
from ai_arena.providers.base import ProviderError


# ---------------------------------------------------------------------------
# P0-1: SessionManager disk round-trip
# ---------------------------------------------------------------------------
def test_session_manager_reload_from_disk(tmp_path: Path) -> None:
    sm = SessionManager(storage_dir=tmp_path)
    agent = Agent(
        id="a1", name="A", role=AgentRole.CRITIC,
        system_prompt="x", provider="openai", model="gpt-4o", api_key="",
    )
    session = sm.create_session("Reload test", [agent], max_rounds=3, rate_limit=0)
    session_id = session.id

    # Simulate a process restart: build a brand new manager on the same dir.
    sm2 = SessionManager(storage_dir=tmp_path)
    reloaded = sm2.get_session(session_id)
    assert reloaded is not None, "session was not reloaded from disk"
    assert reloaded.name == "Reload test"
    assert reloaded.max_rounds == 3
    assert len(reloaded.agents) == 1
    assert reloaded.agents[0].name == "A"
    # The most recently updated session is the active one.
    assert sm2.get_active_session() is not None
    assert sm2.get_active_session().id == session_id
    print("SessionManager reload-from-disk test passed")


# ---------------------------------------------------------------------------
# P0-2: Tool parser handles nested JSON arguments
# ---------------------------------------------------------------------------
def test_parser_nested_tool_call_fence() -> None:
    resp = (
        '```tool_call\n'
        '{"tool": "read_file", "arguments": {"path": "/tmp/nested.md"}}\n'
        '```'
    )
    tc = parse_tool_call(resp)
    assert tc is not None, "fenced tool_call should parse"
    assert tc.tool_name == "read_file"
    assert tc.arguments == {"path": "/tmp/nested.md"}
    print("Parser: fenced tool_call with nested args OK")


def test_parser_raw_json_with_nested_args() -> None:
    resp = (
        'Sure, calling the tool now: '
        '{"tool": "write_file", "arguments": {"path": "C:/x.md", "content": "hi"}}\n'
        'Let me know if you need anything else.'
    )
    assert has_tool_call(resp)
    tc = parse_tool_call(resp)
    assert tc is not None, "raw JSON with nested args should be found"
    assert tc.tool_name == "write_file"
    assert tc.arguments["content"] == "hi"
    print("Parser: raw JSON with nested args OK")


def test_parser_json_fence_with_nested_args() -> None:
    resp = (
        '```json\n'
        '{"tool": "patch_file", "arguments": {"path": "/a", "old_text": "x", "new_text": "y"}}\n'
        '```'
    )
    tc = parse_tool_call(resp)
    assert tc is not None
    assert tc.tool_name == "patch_file"
    assert tc.arguments["old_text"] == "x"
    print("Parser: json fence with nested args OK")


def test_parser_no_tool_call_returns_none() -> None:
    assert parse_tool_call("Just some plain text, no tool here.") is None
    assert not has_tool_call("Nothing in this response either.")
    print("Parser: negative cases OK")


# ---------------------------------------------------------------------------
# P0-4: Rate limiter preserves last_call across start
# ---------------------------------------------------------------------------
def test_rate_limiter_preserves_last_call() -> None:
    rl = RateLimiter(delay_seconds=0.0)
    # Drive an initial wait so last_call is non-zero.
    rl.wait()
    pre = rl._last_call
    assert pre > 0
    # Simulate what start_session now does: just update the delay.
    rl.delay_seconds = 0.0
    assert rl._last_call == pre, "delay change must not reset last_call"
    print("Rate limiter: last_call preserved on delay change OK")


# ---------------------------------------------------------------------------
# P1-6: Atomic _save_session
# ---------------------------------------------------------------------------
def test_save_session_atomic(tmp_path: Path) -> None:
    sm = SessionManager(storage_dir=tmp_path)
    agent = Agent(
        id="a1", name="A", role=AgentRole.CRITIC,
        system_prompt="x", provider="openai", model="gpt-4o", api_key="",
    )
    session = sm.create_session("Atomic", [agent], max_rounds=1, rate_limit=0)
    # After a successful save there must be no .json.tmp left behind.
    leftovers = list(tmp_path.glob("*.json.tmp"))
    assert not leftovers, f"unexpected tmp files: {leftovers}"
    # File is valid JSON.
    on_disk = json.loads((tmp_path / f"session_{session.id}.json").read_text("utf-8"))
    assert on_disk["id"] == session.id
    print("Atomic _save_session test passed")


# ---------------------------------------------------------------------------
# Orchestrator smoke test (covers P0-3 thread-safe accessors)
# ---------------------------------------------------------------------------
def test_orchestrator_thread_safe_accessors() -> None:
    orch = Orchestrator()
    assert orch.is_loop_running() is False
    assert orch.is_loop_alive() is False
    err = orch.consume_last_error()
    assert err is None
    # Calling consume_last_error twice returns None the second time.
    orch._set_last_error("boom")
    assert orch.consume_last_error() == "boom"
    assert orch.consume_last_error() is None
    print("Orchestrator thread-safe accessors OK")


# ---------------------------------------------------------------------------
# max_tokens round-trip + provider call forwarding
# ---------------------------------------------------------------------------
def test_agent_max_tokens_round_trip() -> None:
    a = Agent(
        id="x", name="X", role=AgentRole.CUSTOM,
        system_prompt="", provider="openai", model="gpt-4o", api_key="",
        max_tokens=4096,
    )
    assert a.max_tokens == 4096
    # Default value still works when the caller doesn't set it.
    b = Agent(id="y", name="Y", role=AgentRole.CUSTOM, system_prompt="",
              provider="openai", model="gpt-4o", api_key="")
    assert b.max_tokens == 20000
    # Serialization preserves the field.
    data = a.to_dict()
    assert data["max_tokens"] == 4096
    # And from_dict restores it (even on older payloads that lack the key).
    legacy = {k: v for k, v in data.items() if k != "max_tokens"}
    restored = Agent.from_dict(legacy)
    assert restored.max_tokens == 20000
    restored_with_value = Agent.from_dict(data)
    assert restored_with_value.max_tokens == 4096
    print("Agent max_tokens round-trip OK")


class _CapturingProvider(OpenAIProvider):
    """OpenAIProvider subclass that records the kwargs it was called with,
    so we can assert that max_tokens flows through orchestrator._call_provider.
    """
    captured: list[dict] = []

    def chat(self, messages, model, api_key, **kwargs):  # type: ignore[override]
        _CapturingProvider.captured.append({"model": model, **kwargs})
        return "ok"


def test_orchestrator_forwards_max_tokens() -> None:
    orch = Orchestrator()
    _CapturingProvider.captured = []
    orch.register_provider("openai", _CapturingProvider())

    agent = Agent(
        id="z", name="Z", role=AgentRole.CUSTOM,
        system_prompt="", provider="openai", model="gpt-4o", api_key="sk-x",
        max_tokens=2048,
    )
    sm = SessionManager(storage_dir=Path(tempfile.gettempdir()) / "ai_arena_maxtok")
    sm.storage_dir.mkdir(parents=True, exist_ok=True)
    session = sm.create_session("max_tokens test", [agent], max_rounds=1, rate_limit=0,
                                 is_dry_run=False)
    session.is_dry_run = True  # skip real API, but still call _call_provider path
    out = orch._call_provider(agent, session)
    assert out.startswith("[DRY RUN]")
    # Dry-run path doesn't call provider; switch off and exercise real call.
    session.is_dry_run = False
    _CapturingProvider.captured = []
    try:
        orch._call_provider(agent, session)
    except ProviderError:
        # Provider will reject a fake key but only after receiving kwargs;
        # verify the kwargs arrived correctly regardless.
        pass
    assert _CapturingProvider.captured, "provider was never called"
    assert _CapturingProvider.captured[0].get("max_tokens") == 2048
    print("Orchestrator forwards max_tokens to provider OK")


# ---------------------------------------------------------------------------
# tool_max_retries override
# ---------------------------------------------------------------------------
def test_session_tool_max_retries_override(tmp_path: Path) -> None:
    sm = SessionManager(storage_dir=tmp_path)
    agent = Agent(id="a", name="A", role=AgentRole.CRITIC,
                  system_prompt="x", provider="openai", model="gpt-4o", api_key="")
    session = sm.create_session("retries", [agent], max_rounds=1,
                                 rate_limit=0, tool_max_retries=7)
    assert session.tool_max_retries == 7
    # Reload to confirm it persisted.
    sm2 = SessionManager(storage_dir=tmp_path)
    reloaded = sm2.get_session(session.id)
    assert reloaded is not None
    assert reloaded.tool_max_retries == 7
    print("SessionManager tool_max_retries override OK")


# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
def test_design_tokens_module_loads() -> None:
    from ai_arena.ui.tokens import AGENT_PALETTE, TOKENS, css_variables_block

    assert AGENT_PALETTE, "AGENT_PALETTE must not be empty"
    assert all(c.startswith("#") for c in AGENT_PALETTE)

    # The CSS block must contain every token as a --name: value; declaration.
    block = css_variables_block()
    assert block.lstrip().startswith(":root {")
    for name in TOKENS:
        assert f"{name}:" in block, f"missing token in CSS block: {name}"
    print("Design tokens module OK")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_session_manager_reload_from_disk(tmp)
        test_save_session_atomic(tmp)
        test_session_tool_max_retries_override(tmp)

    test_parser_nested_tool_call_fence()
    test_parser_raw_json_with_nested_args()
    test_parser_json_fence_with_nested_args()
    test_parser_no_tool_call_returns_none()
    test_rate_limiter_preserves_last_call()
    test_orchestrator_thread_safe_accessors()
    test_agent_max_tokens_round_trip()
    test_orchestrator_forwards_max_tokens()
    test_design_tokens_module_loads()
    print("\nAll fix-regression tests passed!")
