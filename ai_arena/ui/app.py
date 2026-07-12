"""Main Streamlit application for AI Arena.

Implements the three-panel layout:
- Left: Conversation history
- Center: Controls and progress
- Right: Shared context file view
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import streamlit as st

from ..config import config
from ..engine.orchestrator import Orchestrator
from ..engine.rate_limiter import RateLimiter
from ..engine.session import SessionManager
from ..models.agent import Agent
from ..models.session_state import SessionState
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.openrouter_provider import OpenRouterProvider
from .chat_panel import render_chat_panel
from .config_panel import render_config_panel
from .context_panel import render_context_panel
from .icons import (
    BOT,
    CPU,
    DOWNLOAD,
    NETWORK,
    PLAY,
    PAUSE,
    STOP,
    SETTINGS,
    USERS,
    SPARKLES,
    ZAP,
    FILE_TEXT,
    TERMINAL,
    MESSAGE_SQUARE,
    ALERT,
    CHECK,
    X,
    PLUS,
    MINUS,
    EYE,
    EYE_OFF,
    COPY,
    SAVE,
    HOME,
    ARROW_RIGHT,
    ARROW_LEFT,
    EXTERNAL_LINK,
    STAR,
    TARGET,
    ACTIVITY,
    LAYERS,
    GIT_BRANCH,
    DATABASE,
    SERVER,
    SHIELD,
    LOCK,
    KEY,
    MENU,
    SUN,
    MOON,
)


def _init_session_state() -> None:
    """Initialize Streamlit session state defaults."""
    defaults = {
        "current_session_id": None,
        "orchestrator_running": False,
        "initialized": False,
        "_orchestrator": None,
        "_session_manager": None,
        "_rate_limiter": None,
        "last_error": None,
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
        st.session_state["_orchestrator"] = orchestrator
    return st.session_state["_orchestrator"]


def _get_session_manager() -> SessionManager:
    """Get or create the session manager, persisting it in session state."""
    if st.session_state.get("_session_manager") is None:
        st.session_state["_session_manager"] = SessionManager()
    return st.session_state["_session_manager"]


def _get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter, persisting it in session state."""
    if st.session_state.get("_rate_limiter") is None:
        st.session_state["_rate_limiter"] = RateLimiter()
    return st.session_state["_rate_limiter"]


def _run_loop(orchestrator: Orchestrator, session: SessionState) -> None:
    """Run the orchestration loop in a background thread."""
    while session.is_running and not session.is_paused:
        if session.is_complete():
            session.is_running = False
            break
        try:
            orchestrator.step(session)
        except Exception as exc:
            st.session_state["last_error"] = str(exc)
            session.is_running = False
            break
        time.sleep(0.1)
    st.session_state["orchestrator_running"] = False


def render_control_buttons(orchestrator: Orchestrator, session: SessionState | None) -> None:
    """Render start, pause, resume, stop, and export buttons."""
    if not session:
        st.info("Create a session to begin.")
        return

    # Show running indicator
    if session.is_running:
        with st.spinner("Session running...", show_time=True):
            st.empty()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Start", disabled=session.is_running, key="btn_start"):
            initial_prompt = st.session_state.get("initial_prompt", "").strip()
            if not initial_prompt:
                st.error("Please enter an initial prompt before starting.")
                return
            orchestrator.start_session(session, initial_prompt=initial_prompt)
            st.session_state["orchestrator_running"] = True
            thread = threading.Thread(
                target=_run_loop,
                args=(orchestrator, session),
                daemon=True,
            )
            thread.start()
            st.rerun()

    with col2:
        if st.button("Pause", disabled=not session.is_running, key="btn_pause"):
            orchestrator.pause_session(session)
            st.rerun()

    with col3:
        if st.button("Resume", disabled=not session.is_paused, key="btn_resume"):
            orchestrator.resume_session(session)
            st.session_state["orchestrator_running"] = True
            thread = threading.Thread(
                target=_run_loop,
                args=(orchestrator, session),
                daemon=True,
            )
            thread.start()
            st.rerun()

    with col4:
        if st.button("Stop", disabled=not session.is_running and not session.is_paused, key="btn_stop"):
            orchestrator.stop_session(session)
            st.rerun()

    # Export
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
        data=content,
        file_name=f"ai_arena_session_{session.id}.md",
        mime="text/markdown",
        key="btn_export",
    )


def render_app() -> None:
    """Main entry point for the Streamlit application."""
    st.set_page_config(
        page_title=config.app_name,
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Dark theme CSS
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}

        /* Hero banner */
        .hero {
            background: linear-gradient(120deg,#1f2a52 0%,#3a2b63 55%,#5a2d52 100%);
            border-radius: 16px; padding: 18px 26px; margin-bottom: 14px;
            color: #f4f1ea; box-shadow: 0 6px 22px #00000038;
        }
        .hero h1 {margin: 0; font-size: 1.55rem; letter-spacing: .2px;}
        .hero p {margin: 4px 0 0; opacity: .82; font-size: .92rem;}

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: #ffffff0a; border: 1px solid #ffffff1f;
            border-radius: 12px; padding: 10px 14px;
        }
        div[data-testid="stMetric"] label {opacity: .7; font-size: .78rem;}

        /* Buttons */
        .stButton > button, .stDownloadButton > button {
            padding: .34rem .85rem; font-size: .88rem; font-weight: 600;
            border-radius: 9px; min-height: 44px; line-height: 1.25;
            border: 1px solid #ffffff26; transition: all .12s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: #ffffff55; transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(120deg,#3a2b63,#5a2d52);
            border-color: #ffffff55;
        }

        /* Chat bubbles */
        .chat-bubble {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;
        }
        .chat-bubble.tool-call {
            border-left: 3px solid #f59e0b;
            background: #1a2332;
        }
        .chat-bubble.error {
            border-left: 3px solid #ef4444;
            background: #1a1215;
        }
        .chat-bubble.warning {
            border-left: 3px solid #f59e0b;
            background: #1a1a12;
        }

        /* Progress bar */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #3a2b63, #5a2d52);
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: #1e293b !important;
            border-radius: 8px !important;
        }

        /* Code blocks */
        pre {
            background: #0f172a !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
        }

        hr {margin: .9rem 0; border-color: #ffffff14;}
        footer {visibility: hidden;}

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
            .stButton > button, .stDownloadButton > button {
                transition: none !important;
                transform: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
          <h1>{BOT} {config.app_name} <span style="opacity:.5;font-size:1rem">v{config.version}</span></h1>
          <p>Multi-AI orchestration platform — agents collaborate on a shared context</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _init_session_state()

    orchestrator = _get_orchestrator()
    session_manager = _get_session_manager()

    # Config panel
    config_values = render_config_panel(orchestrator, session_manager)

    # Initial prompt
    with st.expander("Initial Prompt", expanded=True):
        initial_prompt = st.text_area(
            "Enter the initial prompt for the first agent",
            value=st.session_state.get("initial_prompt", ""),
            height=150,
            key="initial_prompt",
        )

    # Active session
    session = session_manager.get_active_session()
    if not session and st.session_state.get("current_session_id"):
        session = session_manager.get_session(st.session_state["current_session_id"])

    # Control buttons
    render_control_buttons(orchestrator, session)

    # Display last error if any
    if st.session_state.get("last_error"):
        st.error(st.session_state["last_error"])

    # Loading indicator
    if session and session.is_running:
        st.spinner("Session running...")

    # Three-column layout (responsive on mobile)
    col_chat, col_center, col_context = st.columns([1, 1, 1], gap="medium")

    with col_chat:
        if session:
            render_chat_panel(session.messages, session.get_current_agent() if session.is_running else None)
        else:
            st.info("No active session.")

    with col_center:
        if session:
            st.metric("Session", session.name)
            st.metric("Round", f"{session.current_round} / {session.max_rounds}")
            st.metric("Status", "Running" if session.is_running else ("Paused" if session.is_paused else "Idle"))
            st.metric("Dry Run", "Yes" if session.is_dry_run else "No")
            st.metric("Agents", len(session.agents))
            if session.summary_agent:
                st.metric("Summary Agent", session.summary_agent.name)
        else:
            st.info("No active session.")

    with col_context:
        if session:
            render_context_panel(session, orchestrator)
        else:
            st.info("No active session.")
