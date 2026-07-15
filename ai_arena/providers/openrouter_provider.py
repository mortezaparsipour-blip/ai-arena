"""OpenRouter provider implementation.

OpenRouter provides access to many free models through a single API.
Free models include: openrouter/free, meta-llama/llama-3.1-8b-instruct:free, etc.
"""

from __future__ import annotations

from typing import Any, cast

from .base import BaseProvider, ProviderError

try:
    from openai import (
        APIStatusError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        OpenAI,
        RateLimitError,
    )
    from openai.types.chat import ChatCompletionMessageParam
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    APIStatusError = Exception
    AuthenticationError = Exception
    BadRequestError = Exception
    NotFoundError = Exception
    RateLimitError = Exception


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider supporting free and paid models."""

    @property
    def name(self) -> str:
        return "OpenRouter"

    @property
    def default_model(self) -> str:
        return "openrouter/free"

    @property
    def available_models(self) -> list[str]:
        return [
            "openrouter/free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "google/gemma-2-9b-it:free",
            "mistral/mistral-7b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
            "nousresearch/nous-capybara-7b:free",
            "openai/gpt-oss-120b:free",
            "qwen/qwen-2-7b-instruct:free",
            "gryphe/mythomist-7b:free",
        ]

    def __init__(self) -> None:
        """Initialize OpenRouter provider."""
        self.base_url = "https://openrouter.ai/api/v1"

    def chat(
        self,
        messages: list[Any],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to OpenRouter and return response text."""
        if not OPENAI_AVAILABLE:
            raise ProviderError("openai package is not installed. Run: pip install openai")

        if not api_key:
            raise ProviderError("OpenRouter API key is required.")

        try:
            client = OpenAI(base_url=self.base_url, api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                max_tokens=kwargs.pop("max_tokens", 10000),
                **kwargs,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ProviderError("OpenRouter returned empty response.")
            return content
        except AuthenticationError as exc:
            raise ProviderError(
                "OpenRouter authentication failed. Check your API key (sk-or-...). "
                f"Detail: {exc}"
            ) from exc
        except RateLimitError as exc:
            raise ProviderError(
                "OpenRouter rate limit exceeded. Free models may be busy. "
                f"Retry after backoff. Detail: {exc}"
            ) from exc
        except NotFoundError as exc:
            raise ProviderError(
                f"OpenRouter model not found or unavailable: '{model}'. "
                "Check available models list or enable a different provider. "
                f"Detail: {exc}"
            ) from exc
        except BadRequestError as exc:
            raise ProviderError(
                f"OpenRouter bad request. Check messages/parameters. Detail: {exc}"
            ) from exc
        except APIStatusError as exc:
            raise ProviderError(
                f"OpenRouter API error {getattr(exc, 'status_code', '?')}: {getattr(exc, 'message', str(exc))}"
            ) from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"OpenRouter API error: {exc}") from exc

    def validate_key(self, api_key: str) -> bool:
        """Validate OpenRouter API key."""
        if not api_key or not api_key.startswith("sk-or-"):
            return False
        return True
