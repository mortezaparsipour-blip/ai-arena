"""OpenAI provider implementation."""

from __future__ import annotations

from typing import Any, cast

from openai.types.chat import ChatCompletionMessageParam

from .base import BaseProvider, ProviderError

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    @property
    def available_models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    def chat(
        self,
        messages: list[Any],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to OpenAI and return response text."""
        if not OPENAI_AVAILABLE:
            raise ProviderError("openai package is not installed. Run: pip install openai")

        if not api_key:
            raise ProviderError("OpenAI API key is required.")

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                max_tokens=kwargs.pop("max_tokens", 20000),
                **kwargs,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ProviderError("OpenAI returned empty response.")
            return content
        except Exception as exc:
            raise ProviderError(f"OpenAI API error: {exc}") from exc

    def validate_key(self, api_key: str) -> bool:
        """Validate OpenAI API key."""
        if not api_key or not api_key.startswith("sk-"):
            return False
        return True
