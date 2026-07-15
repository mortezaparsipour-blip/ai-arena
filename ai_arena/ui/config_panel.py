"""Configuration panel for AI Arena UI.

Handles provider selection, API keys, model selection, agent
configuration, global settings, and session management. Sidebar
expanders are prefixed with section icons for visual hierarchy.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from ..config import config
from ..engine.tool_registry import tool_registry
from ..models.agent import Agent, AgentRole
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.base import BaseProvider
from ..providers.cerebras_provider import CerebrasProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.openrouter_provider import OpenRouterProvider
from .icons import icon
from .tokens import AGENT_PALETTE


def get_available_providers() -> dict[str, BaseProvider]:
    """Return mapping of provider name to provider instance."""
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "openrouter": OpenRouterProvider(),
        "cerebras": CerebrasProvider(),
    }


def _sidebar_header(label: str, icon_name: str) -> None:
    """Render a sidebar section header with a leading icon."""
    st.markdown(
        f"<div class='sidebar-section'>{icon(icon_name, 16)} "
        f"<span style='font-size:.78rem;letter-spacing:.05em;'>"
        f"{label.upper()}</span></div>",
        unsafe_allow_html=True,
    )


def _render_tools_panel() -> None:
    """Render a read-only 'Available Tools' expander so users can see what
    agents can call. Data comes from the global ``tool_registry`` so it
    always reflects the current set of registered tools.
    """
    with st.sidebar.expander("Available Tools", icon="🔧", expanded=False):
        for tool in tool_registry.list_tools():
            st.markdown(
                f"<div class='tool-card'>"
                f"<div class='tool-card-name'>{icon('terminal', 14)} {tool.name}</div>"
                f"<div class='tool-card-desc'>{tool.description}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def render_config_panel(
    orchestrator: Any,
    session_manager: Any,
) -> dict[str, Any]:
    """Render the configuration panel in the Streamlit sidebar.

    Returns:
        Dictionary of configuration values collected from the UI. Currently
        only the sidebar UI needs them; the returned ``agents`` list is kept
        so the call site can construct a session from the same agents the
        user just configured.
    """
    st.sidebar.header("Configuration")

    providers = get_available_providers()

    with st.sidebar.expander("Global Settings", icon="⚙", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            max_rounds = st.number_input(
                "Ping-pong rounds",
                min_value=1,
                max_value=50,
                value=st.session_state.get("max_rounds", 10),
                key="max_rounds",
            )
        with col2:
            rate_limit = st.number_input(
                "Rate limit (sec)",
                min_value=0,
                max_value=300,
                value=st.session_state.get("rate_limit", 60),
                key="rate_limit",
                help="Minimum seconds between API calls.",
            )
        col3, col4 = st.columns(2)
        with col3:
            tool_max_retries = st.number_input(
                "Tool retries",
                min_value=0,
                max_value=10,
                value=st.session_state.get("tool_max_retries", 3),
                key="tool_max_retries",
                help="How many times the orchestrator retries a failed tool call "
                     "before injecting an error envelope back into the agent.",
            )
        with col4:
            st.empty()  # placeholder for future knob; keeps col3/col4 visually balanced
        is_dry_run = st.checkbox(
            "Dry-run mode",
            value=st.session_state.get("is_dry_run", False),
            help="Simulate without real API calls.",
            key="is_dry_run",
        )

    with st.sidebar.expander("Agents", icon="👥", expanded=False):
        agent_count = st.number_input(
            "Number of agents",
            min_value=1,
            max_value=6,
            value=st.session_state.get("agent_count", 2),
            key="agent_count",
        )

        sys_prompts = config.get_sys_prompts()
        prompt_names = list(sys_prompts.keys()) + ["custom"]

        agents: list[Agent] = []
        colors = AGENT_PALETTE

        for i in range(agent_count):
            st.subheader(f"Agent {i + 1}")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Name",
                    value=st.session_state.get(f"agent_name_{i}", f"Agent {chr(65+i)}"),
                    key=f"agent_name_{i}",
                )
            with col2:
                provider_name = st.selectbox(
                    "Provider",
                    options=list(providers.keys()),
                    index=list(providers.keys()).index(
                        st.session_state.get(f"agent_provider_{i}", "openai")
                    ),
                    key=f"agent_provider_{i}",
                )
                provider = providers.get(provider_name, OpenAIProvider())

            current_model = st.session_state.get(f"agent_model_{i}", provider.default_model)
            model_index = (
                provider.available_models.index(current_model)
                if current_model in provider.available_models
                else 0
            )
            model = st.selectbox(
                "Model",
                options=provider.available_models,
                index=model_index,
                key=f"agent_model_{i}",
            )
            api_key = st.text_input(
                "API Key",
                value=st.session_state.get(f"agent_api_key_{i}", "")
                or config.get_api_key(provider_name),
                type="password",
                key=f"agent_api_key_{i}",
                help=f"Falls back to {provider_name.upper()}_API_KEY from .env if empty.",
            )
            max_tokens = st.number_input(
                "Max tokens",
                min_value=64,
                max_value=200000,
                value=int(st.session_state.get(f"agent_max_tokens_{i}", 10000)),
                step=256,
                key=f"agent_max_tokens_{i}",
                help="Max tokens requested from the model per call. "
                     "Bump up for long responses, down to save cost.",
            )

            current_prompt = st.session_state.get(f"agent_prompt_{i}", "custom")
            prompt_index = (
                prompt_names.index(current_prompt)
                if current_prompt in prompt_names
                else len(prompt_names) - 1
            )
            prompt_option = st.selectbox(
                "System prompt",
                options=prompt_names,
                index=prompt_index,
                key=f"agent_prompt_{i}",
            )

            if prompt_option == "custom":
                system_prompt = st.text_area(
                    "Custom prompt",
                    value=st.session_state.get(f"agent_custom_prompt_{i}", ""),
                    height=100,
                    key=f"agent_custom_prompt_{i}",
                )
            else:
                try:
                    system_prompt = config.load_sys_prompt(prompt_option)
                except FileNotFoundError:
                    system_prompt = ""
                st.caption(f"Loaded: {prompt_option}.md")

            role = AgentRole.CUSTOM
            if i == 0:
                role = AgentRole.CRITIC
            elif i == 1:
                role = AgentRole.OPTIMIST

            agents.append(Agent(
                id=f"agent_{i}",
                name=name,
                role=role,
                system_prompt=system_prompt,
                provider=provider_name,
                model=model,
                api_key=api_key,
                max_tokens=int(max_tokens),
                color=colors[i % len(colors)],
            ))

    _render_tools_panel()

    with st.sidebar.expander("Sessions", icon="📂", expanded=False):
        sessions = session_manager.list_sessions()
        session_options = ["New Session"] + [f"{s['name']} ({s['id']})" for s in sessions]
        selected = st.selectbox(
            "Active Session",
            options=session_options,
            index=0,
            key="active_session",
        )

        if selected != "New Session" and sessions:
            sid = sessions[session_options.index(selected) - 1]["id"]
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Switch", icon="➡", key="switch_session"):
                    session_manager.set_active_session(sid)
                    st.rerun()
            with col_b:
                if st.button("Delete", icon="🗑", key="delete_session"):
                    session_manager.delete_session(sid)
                    st.rerun()

        session_name = st.text_input(
            "Session name",
            value=st.session_state.get("session_name", "Session 1"),
            key="session_name",
        )

        if st.button("Create Session", icon="✓", key="create_session", type="primary"):
            session = session_manager.create_session(
                name=session_name,
                agents=agents,
                max_rounds=max_rounds,
                rate_limit=rate_limit,
                is_dry_run=is_dry_run,
                tool_max_retries=tool_max_retries,
            )
            st.session_state["current_session_id"] = session.id
            st.rerun()

    return {
        "agents": agents,
        "max_rounds": max_rounds,
        "rate_limit": rate_limit,
        "is_dry_run": is_dry_run,
        "tool_max_retries": tool_max_retries,
        "session_name": session_name,
    }
