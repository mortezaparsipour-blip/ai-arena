"""Anthropic provider implementation."""

from __future__ import annotations

from typing import Any

from .base import BaseProvider, ProviderError

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    @property
    def available_models(self) -> list[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to Anthropic and return response text."""
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError(
                "anthropic package is not installed. Run: pip install anthropic"
            )

        if not api_key:
            raise ProviderError("Anthropic API key is required.")

        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        try:
            client = Anthropic(api_key=api_key)
            params: dict[str, Any] = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": chat_messages,
            }
            if system_message:
                params["system"] = system_message
            response = client.messages.create(**params)
            content = response.content[0].text
            return content
        except Exception as exc:
            raise ProviderError(f"Anthropic API error: {exc}") from exc

    def validate_key(self, api_key: str) -> bool:
        """Validate Anthropic API key."""
        if not api_key or not api_key.startswith("sk-ant-"):
            return False
        return True
