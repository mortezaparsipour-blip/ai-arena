"""Context panel for AI Arena UI.

Displays the live shared context file content and progress indicators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from ..tools.file_tools import compute_diff


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

    # Progress indicator
    progress = session.current_round / session.max_rounds if session.max_rounds > 0 else 0.0
    st.progress(min(progress, 1.0), text=f"Round {session.current_round + 1} / {session.max_rounds}")

    active_agents = session.get_active_agents()
    if active_agents and session.is_running:
        current = session.get_current_agent()
        if current:
            st.markdown(f"**Active:** {current.name} ({current.role.value})")
    elif session.is_paused:
        st.warning("Paused")
    elif session.is_complete():
        st.success("Completed!")

    # Read context file
    ctx_path = Path(session.context_file_path)
    if ctx_path.exists():
        content = ctx_path.read_text(encoding="utf-8")
        st.code(content, language="markdown")
    else:
        st.info("Context file not yet created.")
