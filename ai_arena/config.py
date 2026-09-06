"""Configuration management for AI Arena.

Supports loading from environment variables, .env files, and UI state.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Global application configuration.

    Attributes:
        app_name: Application display name.
        version: Application version.
        project_root: Repository root — the outermost boundary agents may
            read inside.
        sys_prompts_dir: Directory containing system prompt files.
        context_storage_dir: Directory for session context files.
        docs_dir: Documentation directory.
        default_rate_limit: Default rate limit in seconds.
        default_max_rounds: Default maximum ping-pong rounds.
        default_agent_count: Default number of agents.
        sensitive_file_patterns: Basename patterns agents may never read
            via the file tools, matched at any depth.
        sensitive_dir_names: Directory names agents may never read into.
        sensitive_relative_patterns: Patterns matched against the path
            relative to ``project_root`` that agents may never read.
    """

    app_name: str = "AI Arena"
    version: str = "0.1.0"
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    sys_prompts_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "sys_prompts"
    )
    context_storage_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "contexts"
    )
    docs_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "docs"
    )
    default_rate_limit: int = 5
    default_max_rounds: int = 10
    default_agent_count: int = 2
    # Credentials and runtime data agents must never exfiltrate through
    # read_file. ``contexts/session_*.json`` carries every agent's API key,
    # so it is explicitly denied even though it lives inside the project
    # root. Overridable per-instance for testing.
    sensitive_file_patterns: tuple[str, ...] = (
        ".env",
        ".env.*",
        "*.pem",
        "*.key",
        "secrets.toml",
    )
    sensitive_dir_names: tuple[str, ...] = (
        ".git",
        ".streamlit",
        ".venv",
        "venv",
        "env",
        "node_modules",
    )
    sensitive_relative_patterns: tuple[str, ...] = (
        "contexts/session_*.json",
        "contexts/audit_*.log",
    )

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

        Looks up ``{PROVIDER}_API_KEY`` (upper-cased provider name) first.
        For OpenRouter, ``OPENAI_API_KEY`` is accepted as a *fallback*
        (OpenRouter uses the OpenAI-compatible SDK and some setups only
        define that name) — but the provider-specific variable always
        wins. The reverse precedence would silently send a coexisting
        OpenAI key to OpenRouter and fail with 401.

        Args:
            provider: Provider name as used in the UI (e.g. ``"openai"``).

        Returns:
            The API key string, or an empty string if not found.
        """
        env_keys = [f"{provider.upper()}_API_KEY"]
        if provider.lower() == "openrouter":
            # Compat fallback only — OPENROUTER_API_KEY has priority.
            env_keys.append("OPENAI_API_KEY")
        for key in env_keys:
            value = os.environ.get(key, "").strip()
            if value:
                return value
        return ""

    def is_sensitive_read_path(self, path: Path) -> bool:
        """Return whether ``path`` must never be exposed to agents via read_file.

        ``path`` should be an absolute resolved path. Matching rules:
        - file patterns match the basename at any depth
        - directory names match any component of the path
        - relative patterns match the path relative to ``project_root``

        Args:
            path: Absolute, resolved filesystem path.

        Returns:
            True if reading the path should be rejected.
        """
        if any(fnmatch.fnmatch(path.name, pat) for pat in self.sensitive_file_patterns):
            return True
        if any(part in self.sensitive_dir_names for part in path.parts):
            return True
        try:
            rel = path.relative_to(self.project_root).as_posix()
        except ValueError:
            return False
        return any(fnmatch.fnmatch(rel, pat) for pat in self.sensitive_relative_patterns)


# Global config instance
config = AppConfig()

# Load environment variables if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
