"""Chat panel for AI Arena UI.

Displays the conversation history between agents with color-coding,
timestamps, and styled chat-bubble containers. Tool calls, errors, and
system messages get their own visual treatment via the ``.chat-bubble``
classes declared in ``app.py``.

Note: streamlit ``st.expander`` and ``st.code`` are interactive components
and cannot live inside an HTML bubble, so expandable details (tool call
payload, context diff) are rendered *after* the bubble rather than inside it.
"""

from __future__ import annotations

import hashlib
from typing import Any

import streamlit as st

from ..models.message import Message
from .icons import icon
from .tokens import AGENT_PALETTE


# Stable palette for agent badges. Source of truth lives in ``tokens.py``
# so the same colors are reused by the config panel.
_AGENT_COLORS: list[str] = AGENT_PALETTE


def _agent_color(agent_id: str) -> str:
    """Return a consistent color for an agent based on its ID."""
    idx = int(hashlib.md5(agent_id.encode()).hexdigest(), 16) % len(_AGENT_COLORS)
    return _AGENT_COLORS[idx]


def _bubble_variant(msg: Message) -> str:
    """Pick the CSS modifier for a message's chat bubble."""
    if msg.is_system and msg.content.startswith("[ERROR]"):
        return "error"
    if msg.is_system and msg.content.startswith("[WARNING]"):
        return "warning"
    if msg.had_tool_call:
        return "tool-call"
    if msg.is_system:
        return "system"
    return ""


def _bubble_label(msg: Message) -> tuple[str, str]:
    """Return (display_name, badge_text) for the message."""
    if msg.is_system:
        return "System", "SYS"
    if msg.had_tool_call:
        return f"{msg.agent_name} [Tool Call]", "TL"
    return msg.agent_name, msg.agent_name[:2].upper()


def msg_color_for(variant: str, agent_color: str) -> str:
    """Map a bubble variant to its background color for the badge.

    Always returns a color string — the variant wins over the agent color
    so error/warning/tool/system bubbles are visually distinct regardless
    of which agent produced them.
    """
    if variant == "error":
        return "#ef4444"
    if variant == "warning":
        return "#f59e0b"
    if variant == "tool-call":
        return "#f59e0b"
    if variant == "system":
        return "#475569"
    return agent_color


def _bubble_badge(label: str, variant: str, color: str) -> str:
    """Render the small colored badge that sits to the left of each bubble."""
    bg = msg_color_for(variant, color)
    return (
        f"<div style='background-color:{bg};color:white;padding:6px 10px;"
        f"border-radius:6px;font-size:0.85em;font-weight:600;text-align:center;"
        f"margin-top:4px;min-width:36px;'>{label}</div>"
    )


def render_chat_panel(messages: list[Message], current_agent: Any | None) -> None:
    """Render the conversation history in the left panel.

    Args:
        messages: List of messages in the conversation.
        current_agent: The currently active agent, if any.
    """
    st.header("Conversation")

    if not messages:
        st.info("No messages yet. Configure agents and start a session.")
        return

    for msg in messages:
        variant = _bubble_variant(msg)
        agent_color = _agent_color(msg.agent_id)
        is_current = current_agent and msg.agent_id == current_agent.id
        display_name, badge_text = _bubble_label(msg)
        bg_color = msg_color_for(variant, agent_color)

        cols = st.columns([1, 11])
        with cols[0]:
            st.markdown(_bubble_badge(badge_text, variant, agent_color), unsafe_allow_html=True)
        with cols[1]:
            _render_bubble(msg, variant, display_name, bg_color, is_current)
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


def _render_bubble(
    msg: Message,
    variant: str,
    display_name: str,
    bg_color: str,
    is_current: bool,
) -> None:
    """Render one chat bubble and any expandable details."""
    time_str = msg.timestamp.strftime("%H:%M:%S")
    live_dot = (
        f"<span class='bubble-live'>{icon('cpu', 12)} live</span>" if is_current else ""
    )
    head = (
        f"<div class='bubble-head'>"
        f"<b>{display_name}</b> · Round {msg.round_number + 1} · "
        f"<span class='bubble-time'>{time_str}</span> {live_dot}"
        f"</div>"
    )

    if msg.is_system and msg.content.startswith("[ERROR]"):
        body = f"<div class='bubble-error-text'>{msg.content}</div>"
    elif msg.is_system and msg.content.startswith("[WARNING]"):
        body = f"<div class='bubble-warning-text'>{msg.content}</div>"
    elif msg.is_system and msg.content.startswith("```tool_result"):
        # Tool result envelope — render as preformatted JSON for readability.
        body = f"<pre class='bubble-pre'>{msg.content}</pre>"
    elif msg.is_system:
        body = f"<pre class='bubble-pre'>{msg.content}</pre>"
    elif msg.had_tool_call:
        # The visible text is the post-tool-call answer; the raw JSON lives
        # in the expander below.
        body = (
            f"<div class='bubble-tool-summary'>{icon('zap', 14)} tool call executed</div>"
            f"<div class='bubble-text'>{msg.content}</div>"
        )
    else:
        body = f"<div class='bubble-text'>{msg.content}</div>"

    # Inline style paints a thin left border in the variant color so the
    # variant is identifiable even before the CSS class is applied.
    inline = f"border-left: 3px solid {bg_color};" if variant and bg_color else ""
    st.markdown(
        f"<div class='chat-bubble {variant}' style='{inline}'>"
        f"{head}{body}</div>",
        unsafe_allow_html=True,
    )

    # Expanders: only the kinds that have interesting detail.
    if msg.had_tool_call and not msg.is_system and msg.content.strip().startswith("```"):
        with st.expander("Tool Call Details", expanded=False):
            st.code(msg.content, language="json")
    if msg.context_diff:
        with st.expander("Context Diff", expanded=False):
            st.code(msg.context_diff, language="diff")


# Public alias kept for backwards compatibility with any external caller.
def get_agent_color(agent_id: str) -> str:
    """Return the agent's stable color."""
    return _agent_color(agent_id)
