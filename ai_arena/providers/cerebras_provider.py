"""Cerebras provider implementation.

Cerebras Cloud provides high-speed inference for open models including:
- GPT-OSS 120B (OpenAI's open reasoning model)
- ZAI GLM 4.7 (preview)
- Gemma 4 31B (preview)

Note: These are reasoning models that output reasoning tokens before content.
Use max_tokens >= 500 for best results.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import BaseProvider, ProviderError

if TYPE_CHECKING:
    from cerebras.cloud.sdk import Cerebras
    from cerebras.cloud.sdk.types.chat import ChatCompletion

try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False


class CerebrasProvider(BaseProvider):
    """Cerebras Cloud API provider for high-speed open model inference."""

    @property
    def name(self) -> str:
        return "Cerebras"

    @property
    def default_model(self) -> str:
        return "gpt-oss-120b"

    @property
    def available_models(self) -> list[str]:
        return [
            "gpt-oss-120b",
            "zai-glm-4.7",
            "gemma-4-31b",
        ]

    def __init__(self) -> None:
        """Initialize Cerebras provider."""
        self.base_url = "https://api.cerebras.ai/v1"

    def chat(
        self,
        messages: list[Any],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to Cerebras and return response text."""
        if not CEREBRAS_AVAILABLE:
            raise ProviderError(
                "cerebras-cloud-sdk package is not installed. "
                "Run: pip install cerebras-cloud-sdk"
            )

        if not api_key:
            raise ProviderError("Cerebras API key is required.")

        try:
            client = Cerebras(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.pop("max_tokens", 20000),
                **kwargs,
            )
            # Type-safe extraction: response.choices[0].message.content
            content = response.choices[0].message.content or ""  # type: ignore[attr-defined]
            if not content:
                raise ProviderError("Cerebras returned empty response.")
            return content
        except Exception as exc:
            raise ProviderError(f"Cerebras API error: {exc}") from exc

    def validate_key(self, api_key: str) -> bool:
        """Validate Cerebras API key."""
        if not api_key:
            return False
        return True