"""Workflow step indicator for AI Arena UI.

A small horizontal progress strip that tells the user where they are in
the orchestration workflow:

    1. Configure  →  2. Session  →  3. Run  →  4. Complete

State detection is intentionally a pure function of (session, orchestrator)
so it can be unit-tested without Streamlit. The render function is a thin
Streamlit wrapper that paints the resulting HTML.

Step semantics (mirrors the existing state logic in ``app.py:render_control_buttons``
and ``session_state.is_complete``):

    0 CONFIGURE  — no session yet
    1 SESSION    — session exists, never started, no messages
    2 RUN        — running, paused, or has at least one message but not complete
    3 COMPLETE   — ``session.is_complete()`` (rounds exhausted)
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from .icons import icon

# Step index constants. Exposed for callers that want to branch on the step
# rather than re-deriving it.
STEP_CONFIGURE = 0
STEP_SESSION = 1
STEP_RUN = 2
STEP_COMPLETE = 3

# (label, icon-name) for each step. Rendered in order.
_STEPS: list[tuple[str, str]] = [
    ("Configure", "sliders_horizontal"),
    ("Session", "users"),
    ("Run", "play_circle"),
    ("Complete", "flag"),
]


def compute_step(session: Any | None, orchestrator: Any | None) -> int:
    """Return the current workflow step (0..3) for a session/orchestrator.

    Defensive: ``session`` may be ``None`` (no session yet) and the
    orchestrator's loop-liveness probe is best-effort.

    Args:
        session: ``SessionState`` or ``None``.
        orchestrator: ``Orchestrator`` or ``None``.

    Returns:
        One of the ``STEP_*`` constants.
    """
    if session is None:
        return STEP_CONFIGURE

    # Complete wins outright — even if flags are stale after the loop dies.
    if session.is_complete():
        return STEP_COMPLETE

    loop_alive = False
    if orchestrator is not None:
        try:
            loop_alive = bool(orchestrator.is_loop_alive())
        except Exception:
            loop_alive = False

    running = bool(getattr(session, "is_running", False)) and loop_alive
    paused = bool(getattr(session, "is_paused", False))

    if running or paused:
        return STEP_RUN

    # Has the user started at all? A session with messages but no live loop
    # (e.g. finished mid-way then stopped, or dry-run finished) is still
    # "in progress" until rounds are exhausted.
    messages = getattr(session, "messages", [])
    if len(messages) > 0:
        return STEP_RUN

    return STEP_SESSION


def _step_state(idx: int, current: int) -> str:
    """Return the CSS state class for step ``idx`` given ``current``."""
    if idx < current:
        return "done"
    if idx == current:
        return "active"
    return "pending"


def render_step_indicator(current: int) -> None:
    """Render the horizontal workflow step indicator.

    Args:
        current: The active step index (one of the ``STEP_*`` constants).
    """
    nodes: list[str] = []
    for idx, (label, icon_name) in enumerate(_STEPS):
        state = _step_state(idx, current)
        # Number badge: checkmark if done, number otherwise.
        if state == "done":
            badge = icon("check_circle", 18)
        else:
            badge = icon(icon_name, 18)
        nodes.append(
            f"<div class='step {state}' data-step='{idx}'>"
            f"<span class='step-badge'>{badge}</span>"
            f"<span class='step-label'>{label}</span>"
            f"</div>"
        )
        if idx < len(_STEPS) - 1:
            done = idx < current
            conn_class = "connector done" if done else "connector"
            nodes.append(f"<div class='{conn_class}'></div>")

    st.markdown(
        f"<div class='step-indicator'>{''.join(nodes)}</div>",
        unsafe_allow_html=True,
    )
