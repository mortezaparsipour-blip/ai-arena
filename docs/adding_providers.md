# How to Add a New Provider

AI Arena uses a provider abstraction layer that makes it straightforward to add support for new LLM providers.

## Step 1: Create the Provider Class

Create a new file in `ai_arena/providers/`, e.g. `my_provider.py`:

```python
from __future__ import annotations

from typing import Any

from .base import BaseProvider, ProviderError


class MyProvider(BaseProvider):
    """My custom LLM provider."""

    @property
    def name(self) -> str:
        return "MyProvider"

    @property
    def default_model(self) -> str:
        return "my-model-v1"

    @property
    def available_models(self) -> list[str]:
        return ["my-model-v1", "my-model-v2"]

    def chat(
        self,
        messages: list[Any],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to the provider and return response text."""
        if not api_key:
            raise ProviderError("API key is required.")

        try:
            # Your API call here
            response = your_client.call(model=model, messages=messages, api_key=api_key)
            return response.text
        except Exception as exc:
            raise ProviderError(f"MyProvider API error: {exc}") from exc

    def validate_key(self, api_key: str) -> bool:
        """Validate that the API key is usable."""
        return bool(api_key and len(api_key) > 10)
```

## Step 2: Register the Provider

Update `ai_arena/providers/__init__.py`:

```python
from .my_provider import MyProvider

__all__ = ["BaseProvider", "ProviderError", "OpenAIProvider", "AnthropicProvider", "MyProvider"]
```

Update `ai_arena/ui/config_panel.py` to include the new provider:

```python
from ..providers.my_provider import MyProvider

def get_available_providers() -> dict[str, BaseProvider]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "myprovider": MyProvider(),
    }
```

## Step 3: Install Dependencies

Add any required packages to `requirements.txt`:

```
my-provider-sdk>=1.0.0
```

## Step 4: Test

Create a test in `tests/test_providers.py`:

```python
from ai_arena.providers.my_provider import MyProvider

def test_my_provider_validate_key():
    provider = MyProvider()
    assert provider.validate_key("valid-key-123")
    assert not provider.validate_key("")
```

## BaseProvider Interface

All providers must implement:

| Method | Description |
|--------|-------------|
| `chat(messages, model, api_key, **kwargs)` | Send messages, return response text |
| `validate_key(api_key)` | Validate API key format |
| `name` (property) | Display name |
| `default_model` (property) | Default model identifier |
| `available_models` (property) | List of supported models |

## Message Format

The `messages` parameter is typed as `list[Any]`. Before passing it to a provider SDK, cast it to the SDK's message type (e.g. `ChatCompletionMessageParam` for OpenAI-compatible SDKs):

```python
from typing import Any, cast
from openai.types.chat import ChatCompletionMessageParam

response = client.chat.completions.create(
    model=model,
    messages=cast(list[ChatCompletionMessageParam], messages),
)
```

The runtime format follows the OpenAI chat standard:

```python
[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
]
```

## Provider-Specific Parameters

Pass additional parameters via `**kwargs` in the `chat()` method. These come from the orchestrator and can include temperature, max_tokens, etc.
