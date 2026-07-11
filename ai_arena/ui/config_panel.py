"""Configuration panel for AI Arena UI.

Handles provider selection, API keys, model selection,
agent configuration, and global settings.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from ..config import config
from ..models.agent import Agent, AgentRole
from ..providers.base import BaseProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.openrouter_provider import OpenRouterProvider


def get_available_providers() -> dict[str, BaseProvider]:
    """Return mapping of provider name to provider instance."""
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "openrouter": OpenRouterProvider(),
    }


def render_config_panel(
    orchestrator: Any,
    session_manager: Any,
) -> dict[str, Any]:
    """Render the configuration panel in the Streamlit sidebar.

    Args:
        orchestrator: The Orchestrator instance.
        session_manager: The SessionManager instance.

    Returns:
        Dictionary of configuration values from the UI.
    """
    st.sidebar.header("Configuration")

    providers = get_available_providers()

    # Global settings
    with st.sidebar.expander("Global Settings", expanded=True):
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
            )
        is_dry_run = st.checkbox(
            "Dry-run mode",
            value=st.session_state.get("is_dry_run", False),
            help="Simulate without real API calls.",
            key="is_dry_run",
        )

    # Agent count
    with st.sidebar.expander("Agents", expanded=True):
        agent_count = st.number_input(
            "Number of agents",
            min_value=1,
            max_value=6,
            value=st.session_state.get("agent_count", 2),
            key="agent_count",
        )

        sys_prompts = config.get_sys_prompts()
        prompt_names = list(sys_prompts.keys()) + ["custom"]

        agents = []
        colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]

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

            model = st.selectbox(
                "Model",
                options=provider.available_models,
                index=provider.available_models.index(
                    st.session_state.get(f"agent_model_{i}", provider.default_model)
                ) if st.session_state.get(f"agent_model_{i}", provider.default_model) in provider.available_models else 0,
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

            prompt_option = st.selectbox(
                "System prompt",
                options=prompt_names,
                index=prompt_names.index(
                    st.session_state.get(f"agent_prompt_{i}", "custom")
                ) if st.session_state.get(f"agent_prompt_{i}", "custom") in prompt_names else len(prompt_names) - 1,
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

            agent = Agent(
                id=f"agent_{i}",
                name=name,
                role=role,
                system_prompt=system_prompt,
                provider=provider_name,
                model=model,
                api_key=api_key,
                color=colors[i % len(colors)],
            )
            agents.append(agent)

    # Session management
    with st.sidebar.expander("Sessions", expanded=True):
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
            if st.button("Switch to Session", key="switch_session"):
                session_manager.set_active_session(sid)
                st.rerun()
            if st.button("Delete Session", key="delete_session"):
                session_manager.delete_session(sid)
                st.rerun()

        session_name = st.text_input(
            "Session name",
            value=st.session_state.get("session_name", "Session 1"),
            key="session_name",
        )

        if st.button("Create Session", key="create_session"):
            session = session_manager.create_session(
                name=session_name,
                agents=agents,
                max_rounds=max_rounds,
                rate_limit=rate_limit,
                is_dry_run=is_dry_run,
            )
            st.session_state["current_session_id"] = session.id
            st.rerun()

    return {
        "agents": agents,
        "max_rounds": max_rounds,
        "rate_limit": rate_limit,
        "is_dry_run": is_dry_run,
        "session_name": session_name,
    }
