"""Context panel for AI Arena UI.

Displays the live shared context file, the most recent context diff, and a
download button, organized into tabs so the panel stays compact even as the
context grows. A status header at the top mirrors the chat panel's active-
agent indicator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from .icons import icon


def _status_badge(session: Any) -> str:
    """Return an HTML status chip for the context panel header."""
    if session.is_running:
        return "<span class='status-pill run'>● Running</span>"
    if session.is_paused:
        return "<span class='status-pill pause'>⏸ Paused</span>"
    if session.is_complete():
        return "<span class='status-pill done'>✓ Complete</span>"
    return "<span class='status-pill idle'>○ Idle</span>"


def _last_diff(messages: list[Any]) -> str:
    """Return the most recent non-empty context diff, or '' if none."""
    for msg in reversed(messages):
        diff = getattr(msg, "context_diff", None)
        if diff:
            return diff
    return ""


def render_context_panel(
    session: Any,
    orchestrator: Any,
) -> None:
    """Render the shared context file view in the right panel.

    Args:
        session: Current session state.
        orchestrator: The Orchestrator instance.
    """
    # Header with status pill + active agent.
    active_chip = ""
    current = session.get_current_agent() if session.is_running else None
    if current:
        active_chip = (
            f"<span class='active-agent-chip'>{icon('cpu', 12)} "
            f"{current.name}</span>"
        )
    st.markdown(
        f"<div class='panel-header'>"
        f"<span class='panel-title'>{icon('file_text', 18)} Shared Context</span>"
        f"{_status_badge(session)}"
        f"</div>"
        f"<div class='panel-subheader'>{active_chip}</div>",
        unsafe_allow_html=True,
    )

    if not session:
        st.info("No active session.")
        return

    # Read context file once; reused by both the Context and Download tabs.
    ctx_path = Path(session.context_file_path)
    content = ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else ""
    diff = _last_diff(session.messages)

    tab_ctx, tab_diff, tab_dl = st.tabs(["Context", "Diff", "Download"])

    with tab_ctx:
        if content:
            st.code(content, language="markdown")
        else:
            st.info("Context file not yet created.")

    with tab_diff:
        if diff:
            st.code(diff, language="diff")
        else:
            st.markdown(
                "<div class='chat-empty'><p>No context changes recorded yet.</p></div>",
                unsafe_allow_html=True,
            )

    with tab_dl:
        if content:
            st.download_button(
                label="Download Context",
                icon="⬇",
                data=content,
                file_name=f"context_{session.id}.md",
                mime="text/markdown",
                key=f"download_context_{session.id}",
                use_container_width=True,
            )
        else:
            st.caption("Nothing to download yet.")
