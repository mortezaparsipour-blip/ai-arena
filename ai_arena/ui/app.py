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

import time
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
from .stepper import compute_step, render_step_indicator
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


def _session_status(session: SessionState, orchestrator: Orchestrator) -> str:
    """Return a short status keyword for the active session.

    One of: ``running``, ``paused``, ``complete``, ``idle``.
    """
    loop_alive = orchestrator.is_loop_alive()
    if session.is_complete():
        return "complete"
    if session.is_running and loop_alive:
        return "running"
    if session.is_paused:
        return "paused"
    return "idle"


def _status_pill(status: str) -> str:
    """Return an HTML status pill for the given status keyword."""
    label = {
        "running":  ("● Running",   "run"),
        "paused":   ("⏸ Paused",    "pause"),
        "complete": ("✓ Complete",  "done"),
        "idle":     ("○ Idle",      "idle"),
    }.get(status, ("○ Idle", "idle"))
    text, cls = label
    return f"<span class='status-pill {cls}'>{text}</span>"


def _render_status_bar(session: SessionState | None, orchestrator: Orchestrator) -> None:
    """Render the top status strip: progress, status pill, round + agent counts.

    Replaces the old center-column metrics block. When no session is active,
    renders a muted placeholder so the bar keeps its height and the layout
    doesn't jump when a session is created.
    """
    if session is None:
        st.markdown(
            "<div class='status-bar'>"
            "<span class='status-bar-muted'>No active session — create one in the sidebar.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    status = _session_status(session, orchestrator)
    display_round = min(session.current_round + 1, session.max_rounds) if session.max_rounds else 1
    progress = min(session.current_round, session.max_rounds) / session.max_rounds if session.max_rounds else 0.0
    active = session.get_current_agent() if session.is_running else None

    # Pre-render the optional chips so the f-string below stays backslash-free
    # (Python <3.12 disallows backslashes inside f-string expressions).
    dry_run_chip = (
        "<span class='status-bar-meta'>DRY-RUN</span>"
        if session.is_dry_run else ""
    )
    active_chip = (
        f"{icon('cpu', 14)} {active.name}" if active else ""
    )

    # Left: status pill + session name. Right: round/agent counts.
    st.markdown(
        f"<div class='status-bar'>"
        f"<div class='status-bar-left'>"
        f"{_status_pill(status)}"
        f"<span class='status-bar-name'>{icon('archive', 14)} {session.name}</span>"
        f"<span class='status-bar-meta'>{icon('users', 14)} {len(session.agents)} agents</span>"
f"<span class='status-bar-meta'>{icon('activity', 14)} "
f"Round {display_round} / {session.max_rounds}</span>"
        f"{dry_run_chip}"
        f"</div>"
        f"<div class='status-bar-right'>{active_chip}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.progress(
        progress,
        text=f"Round {display_round} / {session.max_rounds}",
    )


def render_control_buttons(orchestrator: Orchestrator, session: SessionState | None) -> None:
    """Render the playback control cluster (Start/Pause/Resume/Stop).

    Returned separately from the run bar so callers can place the cluster
    wherever they like. The export button lives in the run bar itself.
    """
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
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
        ):
            orchestrator.stop_session(session)
            st.rerun()


def _render_run_bar(orchestrator: Orchestrator, session: SessionState | None) -> None:
    """Render the bottom run bar: prompt area on the left, controls + export
    on the right. The prompt is only editable when nothing is running; while
    a session is live the cluster shows the playback controls.
    """
    st.markdown("<div class='run-bar-divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='run-bar-label'>{icon('message', 14)} Run</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2], gap="medium")

    with left:
        # Prompt area is the primary affordance; keep it always visible.
        st.text_area(
            "Initial prompt",
            value=st.session_state.get("initial_prompt", ""),
            height=90,
            key="initial_prompt",
            placeholder="e.g. Discuss the future of AI collaboration, "
            "with one critic and one optimist.",
            label_visibility="collapsed",
        )

    with right:
        if session:
            render_control_buttons(orchestrator, session)
            _render_export_button(session)
        else:
            st.markdown(
                "<div class='chat-empty' style='padding:12px;'>"
                "Create a session to enable Start / Pause / Stop."
                "</div>",
                unsafe_allow_html=True,
            )


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
        label="Export",
        icon="⬇",
        data=content,
        file_name=f"ai_arena_session_{session.id}.md",
        mime="text/markdown",
        key="btn_export",
        use_container_width=True,
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

    Uses Streamlit's fragment API (st.fragment) when available; otherwise
    falls back to streamlit_autorefresh. The old ``time.sleep(2)`` fallback
    blocked the main thread and made the UI unresponsive.
    """
    if orchestrator.is_loop_alive():
        try:
            from streamlit_autorefresh import st_autorefresh  # type: ignore

            st_autorefresh(interval=2000, key="arena_autorefresh")
        except ImportError:
            # Best-effort: use an empty st.empty + timer pattern that
            # does not block the Streamlit event loop. If nothing works,
            # the user can still manually rerun the page.
            pass


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
            border-radius: 12px; padding: 12px 20px; margin-bottom: var(--space-3);
            color: var(--text-primary); box-shadow: 0 4px 16px #00000038;
            display: flex; align-items: center; gap: var(--space-3);
        }}
        .hero h1 {{margin: 0; font-size: 1.3rem; letter-spacing: .2px;
                   display:flex; gap:10px; align-items:center;}}
        .hero p {{margin: 2px 0 0; opacity: .82; font-size: .85rem;}}
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

        /* ===== New: status bar (top strip) ===== */
        .status-bar {{
            display: flex; align-items: center; justify-content: space-between;
            gap: var(--space-3); flex-wrap: wrap;
            background: var(--status-bar-bg);
            border: 1px solid var(--status-bar-border);
            border-radius: 10px;
            padding: var(--space-2) var(--space-3);
            margin-bottom: var(--space-1);
        }}
        .status-bar-left {{
            display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap;
        }}
        .status-bar-right {{
            display: flex; align-items: center; gap: var(--space-2);
            color: var(--accent-purple); font-size: .82rem; font-weight: 500;
        }}
        .status-bar-name   {{display:flex;align-items:center;gap:4px;
                             color: var(--text-primary); font-weight:600;
                             font-size:.9rem;}}
        .status-bar-meta   {{display:flex;align-items:center;gap:4px;
                             color: var(--text-muted); font-size:.78rem;}}
        .status-bar-muted  {{color: var(--text-faint); font-size:.82rem;}}

        /* ===== New: status pills (used by status bar + context panel) ===== */
        .status-pill {{
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 10px; border-radius: 999px;
            font-size: .74rem; font-weight: 600; letter-spacing: .02em;
        }}
        .status-pill.run    {{background: var(--pill-run-bg);    color: var(--pill-run-fg);}}
        .status-pill.pause  {{background: var(--pill-pause-bg);  color: var(--pill-pause-fg);}}
        .status-pill.done   {{background: var(--pill-done-bg);   color: var(--pill-done-fg);}}
        .status-pill.idle   {{background: var(--pill-idle-bg);   color: var(--pill-idle-fg);}}
        .status-pill.error  {{background: var(--pill-error-bg);  color: var(--pill-error-fg);}}

        /* ===== New: workflow step indicator ===== */
        .step-indicator {{
            display: flex; align-items: center; gap: var(--space-2);
            background: var(--bg-surface);
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            padding: var(--space-2) var(--space-3);
            margin-bottom: var(--space-3);
        }}
        .step {{
            display: flex; align-items: center; gap: 6px;
            padding: 4px 8px; border-radius: 8px;
            color: var(--step-pending); font-size: .82rem; font-weight: 500;
        }}
        .step.pending {{background: var(--step-pending-bg);}}
        .step.active  {{
            background: var(--step-active-bg); color: var(--step-active);
            font-weight: 700; box-shadow: 0 0 0 1px var(--step-active) inset;
        }}
        .step.done    {{color: var(--step-done);}}
        .step-badge   {{display: inline-flex;}}
        .step.active .step-badge svg {{animation: stepPulse 1.6s ease-in-out infinite;}}
        .connector {{
            flex: 1; height: 2px; min-width: 14px;
            background: var(--step-connector); border-radius: 2px;
        }}
        .connector.done {{background: var(--step-done);}}

        @keyframes stepPulse {{
            0%, 100% {{opacity: 1;}}
            50%      {{opacity: .55;}}
        }}

        /* ===== New: panel headers (chat + context) ===== */
        .panel-header {{
            display: flex; align-items: center; justify-content: space-between;
            gap: var(--space-2); margin-bottom: var(--space-2);
        }}
        .panel-title {{
            display: flex; align-items: center; gap: 6px;
            color: var(--text-primary); font-size: 1.05rem; font-weight: 600;
        }}
        .panel-count {{
            background: var(--overlay-2); color: var(--text-muted);
            border-radius: 999px; padding: 1px 9px;
            font-size: .72rem; font-weight: 600;
        }}
        .panel-subheader {{margin-bottom: var(--space-2);}}
        .active-agent-chip {{
            display: inline-flex; align-items: center; gap: 4px;
            background: var(--accent-indigo); color: var(--accent-purple);
            padding: 2px 8px; border-radius: 6px; font-size: .74rem;
        }}

        /* ===== New: chat empty state + run bar ===== */
        .chat-empty {{
            text-align: center; padding: var(--space-5) var(--space-3);
            color: var(--text-muted);
        }}
        .chat-empty-icon {{font-size: 1.8rem; margin-bottom: var(--space-2);}}
        .chat-empty p    {{margin: 4px 0; font-size: .9rem;}}
        .chat-empty-cta  {{font-size: .8rem; opacity: .8;}}

        .run-bar-divider {{
            height: 1px; background: var(--border-soft);
            margin: var(--space-3) 0 var(--space-2);
        }}
        .run-bar-label {{
            display: flex; align-items: center; gap: 6px;
            color: var(--accent-purple); font-size: .72rem;
            letter-spacing: .05em; text-transform: uppercase;
            margin-bottom: var(--space-1);
        }}

        /* ===== New: agent card in sidebar ===== */
        .agent-card-header {{
            display: flex; align-items: center; gap: 8px;
            color: var(--text-primary); font-weight: 600; font-size: .9rem;
            margin: var(--space-2) 0 4px;
        }}
        .agent-card-dot {{
            width: 10px; height: 10px; border-radius: 50%;
            display: inline-block; box-shadow: 0 0 0 2px var(--bg-base);
        }}

        /* ===== New: API key status chip in sidebar ===== */
        .key-ok   {{display:inline-flex;align-items:center;gap:3px;
                    color: var(--status-success); font-size:.72rem;
                    margin-top: -6px; margin-bottom: 6px;}}
        .key-warn {{display:inline-flex;align-items:center;gap:3px;
                    color: var(--status-warning); font-size:.72rem;
                    margin-top: -6px; margin-bottom: 6px;}}

        @media (prefers-reduced-motion: reduce) {{
            .stButton > button, .stDownloadButton > button {{
                transition: none !important; transform: none !important;
            }}
            .step.active .step-badge svg {{animation: none !important;}}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
          <span class="hero-icon">{icon('bot', 28)}</span>
          <div>
            <h1>{config.app_name} <span style="opacity:.5;font-size:.9rem">v{config.version}</span></h1>
            <p>Multi-AI orchestration — agents collaborate on a shared context</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _init_session_state()

    orchestrator = _get_orchestrator()
    session_manager = _get_session_manager()

    render_config_panel(orchestrator, session_manager)

    # Resolve the active session. After a rerun, ``session_manager`` reloaded
    # from disk, so the session returned here is the persisted one.
    session = session_manager.get_active_session()
    if not session and st.session_state.get("current_session_id"):
        session = session_manager.get_session(st.session_state["current_session_id"])

    # --- Status bar (replaces the old center metrics column) ---------------
    _render_status_bar(session, orchestrator)

    # --- Workflow step indicator ------------------------------------------
    current_step = compute_step(session, orchestrator)
    render_step_indicator(current_step)

    # Surface background-loop errors without blocking the rest of the render.
    loop_error = _consume_loop_error(orchestrator)
    if loop_error:
        st.error(f"Background loop stopped: {loop_error}")

    # Auto-refresh while a session is alive so the user sees live progress.
    if session and orchestrator.is_loop_alive():
        _maybe_autorefresh(orchestrator)

    # --- Main 2-column layout: chat (wide) + context (narrow) -------------
    col_chat, col_context = st.columns([1.8, 1], gap="medium")

    with col_chat:
        if session:
            render_chat_panel(
                session.messages,
                session.get_current_agent() if session.is_running else None,
            )
        else:
            _render_empty_state()

    with col_context:
        if session:
            render_context_panel(session, orchestrator)
        else:
            _render_empty_state()

    # --- Run bar (prompt + controls + export) -----------------------------
    _render_run_bar(orchestrator, session)
