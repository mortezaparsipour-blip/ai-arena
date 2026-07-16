r"""Dry-run 5-round ping-pong smoke test.

No real API calls. Verifies the orchestrator's middleware loop with two
agents alternating for 5 rounds. Reports per-turn state and final assertions.

Run:  .venv\Scripts\python.exe tests\test_dryrun_5rounds.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_arena.engine.orchestrator import Orchestrator
from ai_arena.engine.session import SessionManager
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.providers.openrouter_provider import OpenRouterProvider
from ai_arena.providers.cerebras_provider import CerebrasProvider


def build_agents() -> list[Agent]:
    return [
        Agent(
            id="agent_alice",
            name="Alice",
            role=AgentRole.OPTIMIST,
            system_prompt="You are Alice. Be concise.",
            provider="openrouter",
            model="openrouter/free",
            api_key="sk-or-v1-dryrun-fake",
            color="#6366f1",
        ),
        Agent(
            id="agent_bob",
            name="Bob",
            role=AgentRole.CRITIC,
            system_prompt="You are Bob. Critique briefly.",
            provider="cerebras",
            model="gpt-oss-120b",
            api_key="csk-dryrun-fake",
            color="#f59e0b",
        ),
    ]


def main() -> int:
    print("=" * 70)
    print("DRY-RUN 5-ROUND PING-PONG SMOKE TEST")
    print("=" * 70)
    print()

    # Clean up any prior context/session files from previous dry runs.
    contexts_dir = Path("contexts")
    for f in contexts_dir.glob("session_*.json"):
        f.unlink()
    for f in contexts_dir.glob("*.md"):
        f.unlink()

    sm = SessionManager()
    agents = build_agents()
    session = sm.create_session(
        "DryRun-5Rounds",
        agents,
        max_rounds=5,
        rate_limit=0,
        is_dry_run=True,
    )
    print(f"Session created: id={session.id}")
    print(f"  Agents:        {[a.name for a in agents]}")
    print(f"  Max rounds:    {session.max_rounds}")
    print(f"  Dry run:       {session.is_dry_run}")
    print(f"  Context file:  {session.context_file_path}")
    print()

    orch = Orchestrator(session_manager=sm)
    orch.register_provider("openrouter", OpenRouterProvider())
    orch.register_provider("cerebras", CerebrasProvider())

    print("Starting session with initial prompt...")
    orch.start_session(session, initial_prompt="Design a tiny CLI todo app.")
    print(f"  Initial round: {session.current_round}, agent_idx: {session.current_agent_index}")
    print()

    t0 = time.perf_counter()
    turns = 0
    while not session.is_complete():
        msg = orch.step(session)
        if msg is None:
            print(f"  Turn {turns}: <session ended>")
            break
        elapsed = time.perf_counter() - t0
        preview = msg.content[:80].replace("\n", " ")
        print(
            f"  Turn {turns:>2}: round={msg.round_number} agent={msg.agent_name} "
            f"had_tool={msg.had_tool_call} diff_bytes={len(msg.context_diff or '')} "
            f"t={elapsed:.2f}s"
        )
        print(f"           content: {preview}...")
        turns += 1

    total = time.perf_counter() - t0

    # Re-read session from disk to confirm persistence.
    reloaded = sm.get_session(session.id)
    print()
    print("-" * 70)
    print("FINAL STATE")
    print("-" * 70)
    print(f"  Total turns:        {turns}")
    print(f"  Current round:      {reloaded.current_round}")
    print(f"  Max rounds:         {reloaded.max_rounds}")
    print(f"  Complete:           {reloaded.is_complete()}")
    print(f"  Total messages:     {len(reloaded.messages)}")
    print(f"  Elapsed:            {total:.3f}s")
    print(f"  Context file size:  {Path(reloaded.context_file_path).stat().st_size} bytes")
    print()

    # Assertions (non-zero exit on failure)
    failures = []
    if not reloaded.is_dry_run:
        failures.append("session.is_dry_run should be True")
    if len(reloaded.messages) != 10:
        failures.append(f"expected 10 messages (5 rounds × 2 agents), got {len(reloaded.messages)}")
    if not reloaded.is_complete():
        failures.append("session should be complete after max_rounds")
    if reloaded.current_round != 5:
        failures.append(f"expected current_round=5, got {reloaded.current_round}")
    # Verify alternating pattern between Alice and Bob
    agent_order = [m.agent_name for m in reloaded.messages]
    if len(agent_order) >= 2:
        expected_alternation = ["Alice", "Bob"] * 5  # 10-turn cycle
        if agent_order != expected_alternation:
            failures.append(
                f"expected perfect Alice/Bob alternation over 10 turns, got {agent_order}"
            )
    # Verify all responses contain [DRY RUN] marker
    non_system = [m for m in reloaded.messages if not m.is_system]
    if not all("[DRY RUN]" in m.content for m in non_system):
        failures.append("not all dry-run responses contained [DRY RUN] marker")

    if failures:
        print("FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS — all assertions met")
    print()
    print("Agent order (turn-by-turn):")
    for i, name in enumerate(agent_order, 1):
        print(f"  {i}. {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
