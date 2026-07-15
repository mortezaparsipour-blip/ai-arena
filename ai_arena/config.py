"""Configuration management for AI Arena.

Supports loading from environment variables, .env files, and UI state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Global application configuration.

    Attributes:
        app_name: Application display name.
        version: Application version.
        sys_prompts_dir: Directory containing system prompt files.
        context_storage_dir: Directory for session context files.
        docs_dir: Documentation directory.
        default_rate_limit: Default rate limit in seconds.
        default_max_rounds: Default maximum ping-pong rounds.
        default_agent_count: Default number of agents.
    """

    app_name: str = "AI Arena"
    version: str = "0.1.0"
    sys_prompts_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "sys_prompts"
    )
    context_storage_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "contexts"
    )
    docs_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "docs"
    )
    default_rate_limit: int = 60
    default_max_rounds: int = 10
    default_agent_count: int = 2

    def __post_init__(self) -> None:
        """Ensure directories exist."""
        self.sys_prompts_dir.mkdir(parents=True, exist_ok=True)
        self.context_storage_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_sys_prompts(self) -> dict[str, Path]:
        """Return mapping of prompt name to file path."""
        prompts: dict[str, Path] = {}
        if self.sys_prompts_dir.exists():
            for f in self.sys_prompts_dir.glob("*.md"):
                prompts[f.stem] = f
        return prompts

    def load_sys_prompt(self, name: str) -> str:
        """Load a system prompt by name (stem).

        Args:
            name: Prompt name without extension.

        Returns:
            Prompt text content.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        prompts = self.get_sys_prompts()
        if name not in prompts:
            raise FileNotFoundError(f"System prompt '{name}' not found in {self.sys_prompts_dir}")
        return prompts[name].read_text(encoding="utf-8")

    def get_context_path(self, session_id: str) -> Path:
        """Return the context file path for a given session."""
        return self.context_storage_dir / f"{session_id}.md"

    def get_api_key(self, provider: str) -> str:
        """Return the API key for a provider from environment variables.

        Looks up ``{PROVIDER}_API_KEY`` (upper-cased provider name) and,
        for OpenRouter, also ``OPENROUTER_API_KEY``.

        Args:
            provider: Provider name as used in the UI (e.g. ``"openai"``).

        Returns:
            The API key string, or an empty string if not found.
        """
        env_keys = [f"{provider.upper()}_API_KEY"]
        if provider.lower() == "openrouter":
            # OpenRouter is commonly configured under OPENAI_API_KEY (it uses
            # the OpenAI-compatible SDK). Accept either name.
            env_keys.insert(0, "OPENAI_API_KEY")
        for key in env_keys:
            value = os.environ.get(key, "").strip()
            if value:
                return value
        return ""


# Global config instance
config = AppConfig()

# Load environment variables if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
