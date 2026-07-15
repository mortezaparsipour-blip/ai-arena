"""Real-API provider tests.

These tests make real network calls and consume small amounts of API credits.
They are gated behind the ``AI_ARENA_LIVE_TESTS`` env var so they do NOT
run during normal ``pytest`` invocations. To run them:

    PowerShell:
        $env:AI_ARENA_LIVE_TESTS="1"
        .venv\\Scripts\\python.exe -m pytest tests/test_providers_live.py -v -s

Each test prints a one-line summary (provider, model, latency, response) to
stdout via ``-s`` so you can read the report inline.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from ai_arena.config import config
from ai_arena.providers import (
    CerebrasProvider,
    OpenAIProvider,
    OpenRouterProvider,
)
from ai_arena.providers.base import ProviderError


# Tiny probe prompt to keep token usage minimal.
PROBE_MESSAGES = [{"role": "user", "content": "Reply with exactly the word 'pong'."}]
PROMPT_TOKENS = 64
# Cerebras reasoning models burn output tokens on reasoning before content;
# 500+ is the floor they recommend in the docstring.
CEREBRAS_TOKENS = 600

# A live test runs only when this env var is set.
LIVE = os.environ.get("AI_ARENA_LIVE_TESTS") == "1"


def _report(provider_name: str, model: str, dt: float, text: str) -> None:
    """Emit a one-line report. Truncated for readability."""
    snippet = (text or "").replace("\n", " ").strip()
    if len(snippet) > 80:
        snippet = snippet[:77] + "..."
    print(f"\n  [{provider_name}] {dt:5.2f}s  model={model}  response={snippet!r}")


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not LIVE, reason="set AI_ARENA_LIVE_TESTS=1 to run real API tests")
@pytest.mark.skipif(not config.get_api_key("openai"), reason="OPENAI_API_KEY not set")
def test_live_openai():
    """Real OpenAI chat call."""
    provider = OpenAIProvider()
    key = config.get_api_key("openai")
    t0 = time.perf_counter()
    try:
        out = provider.chat(
            messages=PROBE_MESSAGES,
            model="gpt-4o-mini",
            api_key=key,
            max_tokens=PROMPT_TOKENS,
        )
        dt = time.perf_counter() - t0
        _report("openai", "gpt-4o-mini", dt, out)
        assert out, "OpenAI returned empty response"
    except ProviderError as exc:
        dt = time.perf_counter() - t0
        print(f"\n  [openai] {dt:5.2f}s  FAILED: {exc}")
        # Re-raise so pytest marks the test as failed; the report is the headline.
        raise


# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not LIVE, reason="set AI_ARENA_LIVE_TESTS=1 to run real API tests")
def test_live_openrouter():
    """Real OpenRouter chat call.

    The user's ``.env`` puts an OpenRouter key under ``OPENAI_API_KEY`` and
    ``config.get_api_key("openrouter")`` does not currently fall back to it,
    so we read both env vars explicitly here to honor the test request.
    """
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        pytest.skip("no OpenRouter key (set OPENROUTER_API_KEY or OPENAI_API_KEY)")

    provider = OpenRouterProvider()
    t0 = time.perf_counter()
    try:
        out = provider.chat(
            messages=PROBE_MESSAGES,
            model="openai/gpt-oss-120b",
            api_key=key,
            max_tokens=PROMPT_TOKENS,
        )
        dt = time.perf_counter() - t0
        _report("openrouter", "openai/gpt-oss-120b", dt, out)
        assert out, "OpenRouter returned empty response"
    except ProviderError as exc:
        dt = time.perf_counter() - t0
        print(f"\n  [openrouter] {dt:5.2f}s  FAILED: {exc}")
        raise


# ---------------------------------------------------------------------------
# Cerebras
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not LIVE, reason="set AI_ARENA_LIVE_TESTS=1 to run real API tests")
@pytest.mark.skipif(not config.get_api_key("cerebras"), reason="CEREBRAS_API_KEY not set")
def test_live_cerebras():
    """Real Cerebras chat call."""
    provider = CerebrasProvider()
    key = config.get_api_key("cerebras")
    t0 = time.perf_counter()
    try:
        out = provider.chat(
            messages=PROBE_MESSAGES,
            model="gpt-oss-120b",
            api_key=key,
            max_tokens=CEREBRAS_TOKENS,
        )
        dt = time.perf_counter() - t0
        _report("cerebras", "gpt-oss-120b", dt, out)
        assert out, "Cerebras returned empty response"
    except ProviderError as exc:
        dt = time.perf_counter() - t0
        print(f"\n  [cerebras] {dt:5.2f}s  FAILED: {exc}")
        raise


# ---------------------------------------------------------------------------
# Anthropic (skipped — no key configured)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not LIVE, reason="set AI_ARENA_LIVE_TESTS=1 to run real API tests")
@pytest.mark.skipif(not config.get_api_key("anthropic"), reason="ANTHROPIC_API_KEY not set")
def test_live_anthropic():
    """Real Anthropic chat call (currently skipped — no key)."""
    pytest.skip("Anthropic key not configured; nothing to test")
