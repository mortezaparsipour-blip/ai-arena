"""Main Streamlit application for AI Arena.

Layout (responsive, collapses gracefully on mobile):
    +---------------------------------------------+
    |              hero banner                    |
    +---------------------------------------------+
    | config (sidebar) |  chat | metrics | ctx    |
    +---------------------------------------------+
    |   initial prompt    |   controls / export   |
    +---------------------------------------------+
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from ..config import config
from ..engine.orchestrator import Orchestrator
from ..engine.session import SessionManager
from ..models.session_state import SessionState
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.cerebras_provider import CerebrasProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.openrouter_provider import OpenRouterProvider
from .chat_panel import render_chat_panel
from .config_panel import render_config_panel
from .context_panel import render_context_panel
from .icons import icon
from .tokens import css_variables_block


# Inline SVG favicon. Shipped as a data URI so the page icon never
# depends on a file existing on disk (the old code had an emoji
# fallback that fired when ``favicon.svg`` was missing).
_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" '
    'stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="6" y="10" width="20" height="14" rx="3" fill="#1e1b4b"/>'
    '<path d="M12 10V6h8v4" fill="none"/>'
    '<circle cx="12" cy="17" r="1.5" fill="#a78bfa" stroke="none"/>'
    '<circle cx="20" cy="17" r="1.5" fill="#a78bfa" stroke="none"/>'
    '<line x1="3" y1="17" x2="6" y2="17"/>'
    '<line x1="26" y1="17" x2="29" y2="17"/>'
    '<line x1="16" y1="18" x2="16" y2="22"/>'
    '</svg>'
)
# ``st.set_page_config`` accepts a URL for ``page_icon`` and ``data:`` URIs
# render correctly in the browser tab.
_FAVICON_DATA_URI = (
    "data:image/svg+xml;utf8," + _FAVICON_SVG.replace('"', "'").replace("#", "%23")
)


def _init_session_state() -> None:
    """Initialize Streamlit session state defaults.

    Only the *Streamlit-side* state lives here. The orchestrator's own
    thread-safe flags (loop running, last error) live on the Orchestrator
    instance, never in ``st.session_state``.
    """
    defaults = {
        "current_session_id": None,
        "initialized": False,
        "_orchestrator": None,
        "_session_manager": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator, persisting it in session state."""
    if st.session_state.get("_orchestrator") is None:
        orchestrator = Orchestrator()
        orchestrator.register_provider("openai", OpenAIProvider())
        orchestrator.register_provider("anthropic", AnthropicProvider())
        orchestrator.register_provider("openrouter", OpenRouterProvider())
        orchestrator.register_provider("cerebras", CerebrasProvider())
        st.session_state["_orchestrator"] = orchestrator
    return st.session_state["_orchestrator"]


def _get_session_manager() -> SessionManager:
    """Get or create the session manager, persisting it in session state."""
    if st.session_state.get("_session_manager") is None:
        st.session_state["_session_manager"] = SessionManager()
    return st.session_state["_session_manager"]


def _consume_loop_error(orchestrator: Orchestrator) -> str | None:
    """Pull the latest background-loop error (one-shot) and surface it."""
    return orchestrator.consume_last_error()


def render_control_buttons(orchestrator: Orchestrator, session: SessionState | None) -> None:
    """Render start, pause, resume, stop, and export buttons."""
    if not session:
        return

    # Live "is the background loop currently alive?" comes from the orchestrator
    # so the main thread doesn't have to read state set by the worker thread.
    loop_alive = orchestrator.is_loop_alive()
    running = session.is_running and loop_alive
    paused = session.is_paused

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "Start",
            icon="▶",
            disabled=running,
            key="btn_start",
            help="Start the orchestration loop",
        ):
            initial_prompt = st.session_state.get("initial_prompt", "").strip()
            if not initial_prompt:
                st.error("Please enter an initial prompt before starting.")
                st.stop()
            orchestrator.start_session(session, initial_prompt=initial_prompt)
            orchestrator.start_background(session)
            st.rerun()

    with col2:
        if st.button(
            "Pause",
            icon="⏸",
            disabled=not running,
            key="btn_pause",
            help="Pause after the current step",
        ):
            orchestrator.pause_session(session)
            st.rerun()

    with col3:
        if st.button(
            "Resume",
            icon="▶",
            disabled=not paused,
            key="btn_resume",
            help="Resume a paused session",
        ):
            orchestrator.resume_session(session)
            orchestrator.start_background(session)
            st.rerun()

    with col4:
        if st.button(
            "Stop",
            icon="⏹",
            disabled=not (running or paused),
            key="btn_stop",
            help="Stop the orchestration loop",
        ):
            orchestrator.stop_session(session)
            st.rerun()

    _render_export_button(session)


def _render_export_button(session: SessionState) -> None:
    """Render download button for session export."""
    lines = [
        f"# AI Arena Session: {session.name}",
        f"ID: {session.id}",
        f"Rounds: {session.current_round}/{session.max_rounds}",
        f"Dry run: {session.is_dry_run}",
        "",
        "## Agents",
    ]
    for agent in session.agents:
        lines.append(f"- **{agent.name}** ({agent.role.value}) — {agent.provider}/{agent.model}")
    lines.append("")
    lines.append("## Conversation")
    for msg in session.messages:
        lines.append(f"### {msg.agent_name} (Round {msg.round_number + 1})")
        lines.append(msg.content)
        lines.append("")
    lines.append("## Shared Context")
    ctx_path = Path(session.context_file_path)
    if ctx_path.exists():
        lines.append(ctx_path.read_text(encoding="utf-8"))

    content = "\n".join(lines)
    st.download_button(
        label="Export Session",
        icon="⬇",
        data=content,
        file_name=f"ai_arena_session_{session.id}.md",
        mime="text/markdown",
        key="btn_export",
    )


def _render_metrics(session: SessionState) -> None:
    """Render the center status column with metrics and progress."""
    active_agent = session.get_current_agent() if session.is_running else None
    status_label = "Idle"
    if session.is_running:
        status_label = "Running"
    elif session.is_paused:
        status_label = "Paused"
    elif session.is_complete():
        status_label = "Complete"

    progress = session.current_round / session.max_rounds if session.max_rounds else 0.0
    st.progress(min(progress, 1.0), text=f"Round {session.current_round + 1} / {session.max_rounds}")

    st.metric("Session", session.name)
    st.metric("Round", f"{session.current_round} / {session.max_rounds}")
    st.metric("Status", status_label)
    st.metric("Dry Run", "Yes" if session.is_dry_run else "No")
    st.metric("Agents", len(session.agents))
    if active_agent:
        st.markdown(
            f"<div class='active-agent'>{icon('cpu', 16)} "
            f"<b>Active:</b> {active_agent.name} ({active_agent.role.value})</div>",
            unsafe_allow_html=True,
        )


def _render_empty_state() -> None:
    """Render the onboarding card shown when no session is active."""
    st.markdown(
        f"""
        <div class="empty-state">
          <div class="empty-state-icon">{icon('sparkles', 36)}</div>
          <h3>No active session yet</h3>
          <p>Configure your agents in the sidebar, write an initial prompt, then hit Start.</p>
          <p class="empty-state-tip">{icon('info', 14)} Dry-run mode is a great way to test the
             loop without burning API credits.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _maybe_autorefresh(orchestrator: Orchestrator) -> None:
    """If a session is running, schedule a rerun every 2s to refresh the UI.

    The 2-second cadence is a compromise: short enough to feel live, long
    enough that Streamlit's render cost doesn't dominate.
    """
    if orchestrator.is_loop_alive():
        try:
            from streamlit_autorefresh import st_autorefresh  # type: ignore

            st_autorefresh(interval=2000, key="arena_autorefresh")
        except ImportError:
            # Fallback: ask JS to reload. Less reliable but no dependency.
            st.markdown(
                "<script>setTimeout(()=>window.location.reload(),2000)</script>",
                unsafe_allow_html=True,
            )


def render_app() -> None:
    """Main entry point for the Streamlit application."""
    st.set_page_config(
        page_title=config.app_name,
        page_icon=_FAVICON_DATA_URI,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
        <style>
        {css_variables_block()}

        .block-container {{padding-top: 1.5rem; padding-bottom: 2rem;}}

        .hero {{
            background: linear-gradient(120deg,
                var(--accent-hero-start) 0%,
                var(--accent-hero-mid)   55%,
                var(--accent-hero-end)   100%);
            border-radius: 16px; padding: 18px 26px; margin-bottom: 14px;
            color: var(--text-primary); box-shadow: 0 6px 22px #00000038;
            display: flex; align-items: center; gap: 16px;
        }}
        .hero h1 {{margin: 0; font-size: 1.55rem; letter-spacing: .2px;
                   display:flex; gap:10px; align-items:center;}}
        .hero p {{margin: 4px 0 0; opacity: .82; font-size: .92rem;}}
        .hero .hero-icon {{color: var(--accent-purple); flex-shrink: 0;}}

        div[data-testid="stMetric"] {{
            background: var(--overlay-1); border: 1px solid var(--overlay-3);
            border-radius: 12px; padding: 10px 14px;
        }}
        div[data-testid="stMetric"] label {{opacity: .7; font-size: .78rem;}}

        .stButton > button, .stDownloadButton > button {{
            padding: .34rem .85rem; font-size: .88rem; font-weight: 600;
            border-radius: 9px; min-height: 44px; line-height: 1.25;
            border: 1px solid var(--overlay-4); transition: all .12s ease;
            display: inline-flex; align-items: center; gap: 6px;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            border-color: var(--overlay-5); transform: translateY(-1px);
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(120deg,
                var(--accent-primary), var(--accent-secondary));
            border-color: var(--overlay-5);
        }}

        /* Chat bubbles (consumed by chat_panel). */
        .chat-bubble {{
            background: var(--bg-surface); border: 1px solid var(--border-soft);
            border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;
        }}
        .chat-bubble.tool-call {{border-left: 3px solid var(--status-warning);
                                 background: var(--bg-elevated);}}
        .chat-bubble.error    {{border-left: 3px solid var(--status-error);
                                 background: var(--bg-error);}}
        .chat-bubble.warning  {{border-left: 3px solid var(--status-warning);
                                 background: var(--bg-warning);}}
        .chat-bubble.system   {{border-left: 3px solid var(--border-strong);
                                 background: var(--bg-base);}}

        /* Empty state card. */
        .empty-state {{
            text-align: center; padding: 40px 24px;
            background: var(--overlay-1); border: 1px dashed var(--overlay-3);
            border-radius: 16px; color: var(--text-muted);
        }}
        .empty-state h3 {{margin: 12px 0 4px; color: var(--text-primary);}}
        .empty-state p  {{margin: 4px 0; font-size: .92rem;}}
        .empty-state-icon {{color: var(--accent-purple);}}
        .empty-state-tip  {{font-size: .8rem; opacity: .7; margin-top: 14px;}}

        /* Active agent indicator in the metrics column. */
        .active-agent {{
            background: var(--bg-surface); border: 1px solid var(--border-soft);
            border-radius: 10px; padding: 8px 12px; margin-top: 8px;
            display: flex; gap: 6px; align-items: center; color: var(--text-primary);
        }}

        /* Sidebar section headers (icons injected from Python). */
        .sidebar-section {{display:flex; align-items:center; gap:6px;
                           color: var(--accent-purple);}}

        /* Bubble internals. */
        .bubble-head   {{font-size:.85rem; color: var(--text-muted);
                         margin-bottom:6px;}}
        .bubble-time   {{opacity:.6; font-weight:400;}}
        .bubble-live   {{color: var(--accent-purple); margin-left:6px;
                         font-size:.7rem; background: var(--accent-indigo);
                         padding:1px 6px; border-radius:6px;}}
        .bubble-text   {{color: var(--text-primary); line-height:1.55;}}
        .bubble-pre    {{background: var(--bg-base); color: var(--text-faint);
                         padding:8px 10px; border-radius:6px;
                         border:1px solid var(--border-soft);
                         font-size:.78rem; white-space:pre-wrap; margin:6px 0 0;}}
        .bubble-error-text   {{color: var(--text-error); font-weight:500;}}
        .bubble-warning-text {{color: var(--text-warning); font-weight:500;}}
        .bubble-tool-summary {{color: var(--text-warning); font-size:.78rem;
                              margin:4px 0 6px;
                              display:flex; align-items:center; gap:4px;}}

        /* Tool card in sidebar. */
        .tool-card       {{background: var(--bg-tool-card);
                          border:1px solid var(--border-soft);
                          border-radius:8px; padding:8px 10px; margin:6px 0;}}
        .tool-card-name  {{color: var(--accent-purple); font-weight:600;
                          font-size:.85rem;
                          display:flex; align-items:center; gap:4px;}}
        .tool-card-desc  {{color: var(--text-muted); font-size:.78rem;
                          margin-top:3px;}}

        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg,
                var(--accent-primary), var(--accent-secondary));
        }}

        .streamlit-expanderHeader {{
            background: var(--bg-surface) !important;
            border-radius: 8px !important;
        }}

        /* Sidebar scroll containment.
           The config panel grows with the number of agents and the tools
           list; on a 13" laptop that pushes the initial prompt and Start
           button off-screen. Cap the height to the viewport and let the
           sidebar scroll internally. ``vh - 60px`` leaves room for the
           Streamlit header. */
        [data-testid="stSidebar"] > div:first-child {{
            max-height: calc(100vh - 60px);
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 6px;
            scrollbar-width: thin;
            scrollbar-color: var(--overlay-4) transparent;
        }}
        [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {{
            width: 6px;
        }}
        [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {{
            background: var(--overlay-4);
            border-radius: 3px;
        }}

        pre {{
            background: var(--bg-base) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-soft) !important;
        }}

        hr {{margin: .9rem 0; border-color: var(--overlay-2);}}
        footer {{visibility: hidden;}}

        @media (prefers-reduced-motion: reduce) {{
            .stButton > button, .stDownloadButton > button {{
                transition: none !important; transform: none !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
          <span class="hero-icon">{icon('bot', 36)}</span>
          <div>
            <h1>{config.app_name} <span style="opacity:.5;font-size:1rem">v{config.version}</span></h1>
            <p>Multi-AI orchestration platform — agents collaborate on a shared context</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _init_session_state()

    orchestrator = _get_orchestrator()
    session_manager = _get_session_manager()

    render_config_panel(orchestrator, session_manager)

    # Initial prompt
    with st.expander("Initial Prompt", icon="💬", expanded=True):
        st.text_area(
            "Enter the initial prompt for the first agent",
            value=st.session_state.get("initial_prompt", ""),
            height=150,
            key="initial_prompt",
            placeholder="e.g. Discuss the future of AI collaboration, with one critic and one optimist.",
        )

    # Resolve the active session. After a rerun, ``session_manager`` reloaded
    # from disk, so the session returned here is the persisted one.
    session = session_manager.get_active_session()
    if not session and st.session_state.get("current_session_id"):
        session = session_manager.get_session(st.session_state["current_session_id"])

    render_control_buttons(orchestrator, session)

    # Surface background-loop errors without blocking the rest of the render.
    loop_error = _consume_loop_error(orchestrator)
    if loop_error:
        st.error(f"Background loop stopped: {loop_error}")

    # Auto-refresh while a session is alive so the user sees live progress.
    if session and orchestrator.is_loop_alive():
        st.markdown(
            f"<div class='active-agent'>{icon('refresh', 14)} "
            f"<b>Live:</b> {session.get_current_agent().name if session.get_current_agent() else '...'} "
            f"is working — UI auto-refreshes every 2s.</div>",
            unsafe_allow_html=True,
        )
        _maybe_autorefresh(orchestrator)

    # Three-column layout.
    col_chat, col_center, col_context = st.columns([1, 1, 1], gap="medium")

    with col_chat:
        if session:
            render_chat_panel(
                session.messages,
                session.get_current_agent() if session.is_running else None,
            )
        else:
            _render_empty_state()

    with col_center:
        if session:
            _render_metrics(session)
        else:
            st.markdown(_empty_metrics_html(), unsafe_allow_html=True)

    with col_context:
        if session:
            render_context_panel(session, orchestrator)
        else:
            _render_empty_state()


def _empty_metrics_html() -> str:
    return (
        f"<div class='empty-state' style='padding:24px;'>"
        f"<div class='empty-state-icon'>{icon('sliders', 28)}</div>"
        f"<h3>Status panel</h3>"
        f"<p>Session status will appear here once you create one.</p>"
        f"</div>"
    )
