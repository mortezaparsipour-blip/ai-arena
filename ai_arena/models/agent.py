"""Agent model representing an AI agent in the orchestration loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgentRole(str, Enum):
    CRITIC = "critic"
    OPTIMIST = "optimist"
    CUSTOM = "custom"


@dataclass
class Agent:
    """Represents a configurable AI agent.

    Attributes:
        id: Unique identifier for the agent.
        name: Human-readable name.
        role: Predefined role type.
        system_prompt: The system prompt text for this agent.
        provider: Provider name (e.g., 'openai', 'anthropic').
        model: Model identifier (e.g., 'gpt-4', 'claude-3-opus').
        api_key: API key for the provider.
        color: Display color for UI differentiation.
        enabled: Whether this agent is active in the loop.
    """

    id: str
    name: str
    role: AgentRole = AgentRole.CUSTOM
    system_prompt: str = ""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    color: str = "#6366f1"
    enabled: bool = True

    def to_dict(self) -> dict:
        """Serialize agent to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "system_prompt": self.system_prompt,
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
            "color": self.color,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Agent:
        """Create agent from dictionary."""
        role = AgentRole(data.get("role", "custom"))
        return cls(
            id=data["id"],
            name=data["name"],
            role=role,
            system_prompt=data.get("system_prompt", ""),
            provider=data.get("provider", "openai"),
            model=data.get("model", "gpt-4"),
            api_key=data.get("api_key", ""),
            color=data.get("color", "#6366f1"),
            enabled=data.get("enabled", True),
        )
