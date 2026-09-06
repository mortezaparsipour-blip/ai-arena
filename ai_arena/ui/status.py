"""Shared session-status helpers for the UI panels.

Single source of truth for status priority so the run bar and the context
panel badge can never disagree again (they used to rank ``complete`` vs
``running`` differently).
"""

from __future__ import annotations

from typing import Any


def session_status(session: Any, loop_alive: bool = True) -> str:
    """Return a short status keyword for a session.

    One of: ``running``, ``paused``, ``complete``, ``idle``. Priority:

    - ``complete`` wins over a stale ``is_running`` flag (e.g. a crashed
      worker that never cleared it),
    - ``running`` requires a live background loop, not just the flag,
    - ``paused`` before ``idle``.
    """
    if session.is_complete():
        return "complete"
    if session.is_running and loop_alive:
        return "running"
    if session.is_paused:
        return "paused"
    return "idle"


def status_pill_html(status: str) -> str:
    """Return an HTML status pill for a status keyword."""
    label = {
        "running":  ("● Running",   "run"),
        "paused":   ("⏸ Paused",    "pause"),
        "complete": ("✓ Complete",  "done"),
        "idle":     ("○ Idle",      "idle"),
    }.get(status, ("○ Idle", "idle"))
    text, cls = label
    return f"<span class='status-pill {cls}'>{text}</span>"


def status_badge_html(session: Any, loop_alive: bool = True) -> str:
    """Return an HTML status pill for a session, resolving its status first."""
    return status_pill_html(session_status(session, loop_alive))
