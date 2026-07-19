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


def _api_key_status(provider_name: str, value: str) -> str:
    """Return a small HTML chip describing whether the API key field is filled.

    Renders ``✓ using .env key`` if the value came from the env fallback,
    ``✓ key set`` if the user typed one, or ``⚠ enter key`` otherwise.
    """
    env_key = config.get_api_key(provider_name)
    if value.strip():
        # If the field value equals the env fallback, attribute it to .env.
        source = "using .env key" if value == env_key else "key set"
        return (
            f"<span class='key-ok'>{icon('check', 12)} {source}</span>"
        )
    if env_key:
        return (
            f"<span class='key-ok'>{icon('check', 12)} using .env key</span>"
        )
    return f"<span class='key-warn'>{icon('alert', 12)} enter key</span>"


# Heuristic prefix → provider mapping. Used to flag obvious key/provider
# mismatches (e.g. ``csk-...`` pasted into the OpenRouter field, or an
# ``sk-or-v1-...`` key sent to Cerebras). Keys that don't match any known
# prefix are left alone — custom proxies and self-hosted gateways often
# use non-standard formats.
_KEY_PREFIX_HINTS: dict[str, tuple[str, ...]] = {
    "openai": ("sk-",),
    "anthropic": ("sk-ant-",),
    "openrouter": ("sk-or-v1-",),
    "cerebras": ("csk-",),
}


def _provider_key_prefix_warning(provider_name: str, value: str) -> str:
    """Return a small warning chip if the API key prefix doesn't match the
    selected provider. Returns an empty string when no obvious mismatch.

    Match is done against the LONGEST known prefix so a generic ``sk-``
    (OpenAI) doesn't shadow a more specific ``sk-or-v1-`` (OpenRouter).
    """
    selected = provider_name.lower()
    # Step 1: does the value match ANY prefix of the SELECTED provider?
    # If yes, no warning — the key is plausibly for this provider.
    selected_prefixes = sorted(
        _KEY_PREFIX_HINTS.get(selected, ()), key=len, reverse=True
    )
    if any(value.startswith(p) for p in selected_prefixes):
        return ""
    # Step 2: if it doesn't match the selected provider, does it look
    # like a known OTHER provider's key? Longest match wins.
    other_prefixes = sorted(
        (
            (prefix, prov)
            for prov, prefixes in _KEY_PREFIX_HINTS.items()
            for prefix in prefixes
            if prov != selected
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for prefix, prov in other_prefixes:
        if value.startswith(prefix):
            return (
                f"<span class='key-warn'>{icon('alert', 12)} "
                f"key looks like a <b>{prov}</b> key, not "
                f"<b>{provider_name}</b></span>"
            )
    return ""


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
    _sidebar_header("Configuration", "sliders_horizontal")

    providers = get_available_providers()

    # --- Step 1: Setup (Global Settings + Agents) --------------------------
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
                value=st.session_state.get("rate_limit", 5),
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
        # Slider gives a more glanceable control than a bare number input.
        agent_count = st.slider(
            "Number of agents",
            min_value=1,
            max_value=6,
            value=st.session_state.get("agent_count", 2),
            key="agent_count",
            help="Each agent takes a turn on the shared context, then hands off.",
        )

        sys_prompts = config.get_sys_prompts()
        prompt_names = list(sys_prompts.keys()) + ["custom"]

        agents: list[Agent] = []
        colors = AGENT_PALETTE

        for i in range(agent_count):
            # Agent card: a bordered sub-container so each agent reads as a
            # unit rather than a stream of inputs.
            st.markdown(
                f"<div class='agent-card-header'>"
                f"<span class='agent-card-dot' style='background:{colors[i % len(colors)]}'></span>"
                f"Agent {i + 1}</div>",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
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

                # Provider-aware state keys: including the provider name in
                # the key forces a fresh widget when the user switches
                # providers, so the API-key field and Model dropdown are
                # re-initialized against the new provider instead of showing
                # the previous provider's value (which is what produced
                # 401s when a Cerebras key was sent to OpenRouter or vice
                # versa).
                model_state_key = f"agent_model_{i}_{provider_name}"
                api_key_state_key = f"agent_api_key_{i}_{provider_name}"

                default_model = provider.default_model
                if model_state_key not in st.session_state:
                    st.session_state[model_state_key] = default_model
                current_model = st.session_state[model_state_key]
                model_index = (
                    provider.available_models.index(current_model)
                    if current_model in provider.available_models
                    else 0
                )
                model = st.selectbox(
                    "Model",
                    options=provider.available_models,
                    index=model_index,
                    key=model_state_key,
                )

                # Pre-fill the API key field with the .env value for THIS
                # provider. Because the key now contains ``provider_name``,
                # a provider change yields a brand-new widget and a fresh
                # auto-fill from the matching env var.
                env_key = config.get_api_key(provider_name)
                if api_key_state_key not in st.session_state:
                    st.session_state[api_key_state_key] = env_key
                api_key = st.text_input(
                    "API Key",
                    type="password",
                    key=api_key_state_key,
                    help=f"Falls back to {provider_name.upper()}_API_KEY from .env if empty.",
                )
                # Resolve the effective key: user input wins, otherwise .env.
                # This is what gets passed to the Agent and shown in the badge,
                # so the UI's claim and the actual API call always agree.
                effective_api_key = api_key.strip() or env_key
                # Inline micro-feedback on the key status.
                st.markdown(
                    _api_key_status(provider_name, effective_api_key),
                    unsafe_allow_html=True,
                )
                # Provider-key prefix sanity check. Catches the classic
                # "I selected OpenRouter in the dropdown but my .env Cerebras
                # key got pasted here" mistake before it becomes a 401.
                if effective_api_key:
                    prefix_warning = _provider_key_prefix_warning(
                        provider_name, effective_api_key
                    )
                    if prefix_warning:
                        st.markdown(prefix_warning, unsafe_allow_html=True)
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
                api_key=effective_api_key,
                max_tokens=int(max_tokens),
                color=colors[i % len(colors)],
            ))

    # --- Step 2: Sessions (promoted near the top — this is what creates
    #     the thing the rest of the UI operates on) -------------------------
    with st.sidebar.expander("Sessions", icon="📂", expanded=True):
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

        if st.button("Create Session", icon="➕", key="create_session", type="primary"):
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

    # --- Step 3: Tools (read-only reference, collapsed) --------------------
    _render_tools_panel()

    return {
        "agents": agents,
        "max_rounds": max_rounds,
        "rate_limit": rate_limit,
        "is_dry_run": is_dry_run,
        "tool_max_retries": tool_max_retries,
        "session_name": session_name,
    }
