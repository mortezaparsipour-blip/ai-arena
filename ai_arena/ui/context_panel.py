"""Context panel for AI Arena UI.

Displays the live shared context file content and progress indicators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from .icons import icon


def render_context_panel(
    session: Any,
    orchestrator: Any,
) -> None:
    """Render the shared context file view in the right panel.

    Args:
        session: Current session state.
        orchestrator: The Orchestrator instance.
    """
    st.header("Shared Context")

    if not session:
        st.info("No active session.")
        return

    active_agents = session.get_active_agents()
    if active_agents and session.is_running:
        current = session.get_current_agent()
        if current:
            st.markdown(
                f"<div class='active-agent'>{icon('cpu', 14)} "
                f"<b>Active:</b> {current.name} ({current.role.value})</div>",
                unsafe_allow_html=True,
            )
    elif session.is_paused:
        st.warning("Paused", icon="⏸")
    elif session.is_complete():
        st.success("Completed!", icon="✅")

    # Read context file
    ctx_path = Path(session.context_file_path)
    if ctx_path.exists():
        content = ctx_path.read_text(encoding="utf-8")
        st.code(content, language="markdown")
        st.download_button(
            label="Download Context",
            icon="⬇",
            data=content,
            file_name=f"context_{session.id}.md",
            mime="text/markdown",
            key=f"download_context_{session.id}",
        )
    else:
        st.info("Context file not yet created.")
