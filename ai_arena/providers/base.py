"""Base provider abstraction for AI Arena."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProviderError(Exception):
    """Raised when a provider encounters an error."""
    pass


class BaseProvider(ABC):
    """Abstract base class for AI providers.

    Subclasses must implement the chat method to interface with
    specific LLM APIs (OpenAI, Anthropic, etc.).
    """

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        api_key: str,
        **kwargs: Any,
    ) -> str:
        """Send messages to the LLM and return the response text.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier.
            api_key: API key for authentication.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Response text from the model.

        Raises:
            ProviderError: If the API call fails.
        """
        pass

    @abstractmethod
    def validate_key(self, api_key: str) -> bool:
        """Validate that an API key is usable.

        Args:
            api_key: The API key to validate.

        Returns:
            True if the key appears valid, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider display name."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """Return list of available models for this provider."""
        pass
