"""OpenRouter provider tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from ai_arena.providers.openrouter_provider import OpenRouterProvider
from ai_arena.providers.base import ProviderError


@pytest.fixture()
def provider():
    return OpenRouterProvider()


def test_defaults(provider):
    assert provider.name == "OpenRouter"
    assert provider.default_model == "openrouter/free"
    models = provider.available_models
    assert "openrouter/free" in models
    assert "meta-llama/llama-3.1-8b-instruct:free" in models


def test_validate_key(provider):
    assert provider.validate_key("sk-or-abc123") is True
    assert provider.validate_key("") is False
    assert provider.validate_key("sk-abc") is False
    assert provider.validate_key("invalid") is False


def test_chat_requires_api_key(provider):
    with pytest.raises(ProviderError, match="OpenRouter API key is required"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], model="openrouter/free", api_key="")


def test_chat_requires_openai_package(provider, monkeypatch):
    monkeypatch.setattr("ai_arena.providers.openrouter_provider.OPENAI_AVAILABLE", False)
    with pytest.raises(ProviderError, match="openai package is not installed"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], model="openrouter/free", api_key="sk-or-")


def _patch_openrouter_client(monkeypatch, exc):
    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.message = "mocked"
    fake_response.request = "GET / HTTP/1.1"

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = exc(
        message="mocked", response=fake_response, body=None
    )

    monkeypatch.setattr(
        "ai_arena.providers.openrouter_provider.OpenAI",
        lambda **kwargs: fake_client,
    )
    return fake_client


def test_auth_error_maps_to_authentication(provider, monkeypatch):
    from openai import AuthenticationError

    _patch_openrouter_client(monkeypatch, AuthenticationError)
    with pytest.raises(ProviderError, match="OpenRouter authentication failed"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], model="openrouter/free", api_key="sk-or-bad")


def test_rate_limit_error_maps_to_rate_limit(provider, monkeypatch):
    from openai import RateLimitError

    _patch_openrouter_client(monkeypatch, RateLimitError)
    with pytest.raises(ProviderError, match="OpenRouter rate limit exceeded"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], model="openrouter/free", api_key="sk-or-ok")


def test_not_found_error_maps_to_model_not_found(provider, monkeypatch):
    from openai import NotFoundError

    client = _patch_openrouter_client(monkeypatch, NotFoundError)
    client.chat.completions.create.side_effect = NotFoundError(
        message="model not found",
        response=MagicMock(status_code=404),
        body=None,
    )
    with pytest.raises(ProviderError, match="OpenRouter model not found or unavailable"):
        provider.chat(messages=[{"role": "user", "content": "hi"}], model="unknown-model", api_key="sk-or-ok")


def test_openrouter_integration_through_orchestrator():
    from ai_arena.engine.session import SessionManager
    from ai_arena.engine.orchestrator import Orchestrator
    from ai_arena.models.agent import Agent, AgentRole
    from ai_arena.providers.openrouter_provider import OpenRouterProvider

    for f in Path("contexts").glob("session_*.json"):
        f.unlink()
    for f in Path("contexts").glob("*.md"):
        f.unlink()

    sm = SessionManager()
    agent = Agent(
        id="a1",
        name="Tester",
        role=AgentRole.CUSTOM,
        system_prompt="You are a tester.",
        provider="openrouter",
        model="openrouter/free",
        api_key="sk-or-invalid",
        color="#6366f1",
    )
    session = sm.create_session(
        "OpenRouter Dry Run",
        [agent],
        max_rounds=1,
        rate_limit=0,
        is_dry_run=True,
    )
    orch = Orchestrator(session_manager=sm)
    orch.register_provider("openrouter", OpenRouterProvider())
    orch.start_session(session, initial_prompt="Hello")
    msg = orch.step(session)
    assert msg is not None
    assert "[DRY RUN]" in msg.content
