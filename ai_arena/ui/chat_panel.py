"""Chat panel for AI Arena UI.

Displays the conversation history between agents with color-coding
and timestamps. Shows tool calls, errors, and system messages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import hashlib

import streamlit as st

from ..models.message import Message
from .icons import MESSAGE_SQUARE, ALERT, ZAP, ACTIVITY, SPARKLES


def _stable_color_index(agent_id: str, num_colors: int) -> int:
    """Return a stable color index for an agent ID using MD5 hash."""
    return int(hashlib.md5(agent_id.encode()).hexdigest(), 16) % num_colors


def render_chat_panel(messages: list[Message], current_agent: Any | None) -> None:
    """Render the conversation history in the left panel.

    Args:
        messages: List of messages in the conversation.
        current_agent: The currently active agent, if any.
    """
    st.header(f"{MESSAGE_SQUARE} Conversation")

    if not messages:
        st.info("No messages yet. Configure agents and start a session.")
        return

    for msg in messages:
        agent_color = _get_agent_color(msg.agent_id)
        is_current = current_agent and msg.agent_id == current_agent.id

        with st.container():
            cols = st.columns([1, 10])
            with cols[0]:
                badge_color = agent_color
                badge_label = msg.agent_name[:2].upper()
                badge_icon = ""
                if msg.is_system:
                    badge_color = "#475569"
                    badge_label = "SYS"
                elif msg.had_tool_call:
                    badge_color = "#f59e0b"
                    badge_label = "TOOL"
                    badge_icon = ZAP
                st.markdown(
                    f"<div style='background-color:{badge_color};"
                    f"color:white;padding:6px 10px;border-radius:6px;"
                    f"font-size:0.85em;font-weight:600;text-align:center;"
                    f"margin-top:4px;min-width:36px;display:flex;align-items:center;justify-content:center;gap:4px;'>"
                    f"{badge_icon}{badge_label}</div>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                label = msg.agent_name
                if msg.is_system:
                    label = "System"
                elif msg.had_tool_call:
                    label = f"{msg.agent_name} [Tool Call]"
                st.markdown(f"**{label}** — Round {msg.round_number + 1}")
                time_str = msg.timestamp.strftime("%H:%M:%S")
                st.caption(time_str)

                if msg.is_system and msg.content.startswith("[ERROR]"):
                    st.error(f"{ALERT} {msg.content}")
                elif msg.is_system and msg.content.startswith("[WARNING]"):
                    st.warning(f"{ALERT} {msg.content}")
                elif msg.had_tool_call:
                    with st.expander(f"{ZAP} Tool Call Details", expanded=False):
                        st.code(msg.content, language="json")
                else:
                    st.markdown(msg.content)

                if msg.context_diff:
                    with st.expander(f"{ACTIVITY} Context Diff", expanded=False):
                        st.code(msg.context_diff, language="diff")
            st.divider()


def _get_agent_color(agent_id: str) -> str:
    """Return a consistent color for an agent based on its ID."""
    colors = [
        "#6366f1", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
    ]
    # Use stable MD5 hash instead of Python's randomized hash()
    idx = int(hashlib.md5(agent_id.encode()).hexdigest(), 16) % len(colors)
    return colors[idx]
