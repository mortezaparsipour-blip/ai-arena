"""Session state model for managing orchestration sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .agent import Agent
from .message import Message


@dataclass
class SessionState:
    """Represents the full state of an orchestration session.

    Attributes:
        id: Unique session identifier.
        name: Human-readable session name.
        agents: List of configured agents.
        messages: Conversation history.
        context_file_path: Path to the shared context file.
        current_round: Current round number (1-indexed).
        current_agent_index: Index of the currently active agent.
        max_rounds: Maximum number of ping-pong rounds.
        rate_limit_seconds: Delay between API calls.
        is_running: Whether the orchestration loop is active.
        is_paused: Whether the loop is paused.
        is_dry_run: Whether this is a dry-run (no real API calls).
        summary_agent: Optional agent for final synthesis.
        created_at: Session creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    name: str
    agents: list[Agent] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    context_file_path: str = "shared_context.md"
    current_round: int = 0
    current_agent_index: int = 0
    max_rounds: int = 10
    rate_limit_seconds: int = 60
    is_running: bool = False
    is_paused: bool = False
    is_dry_run: bool = False
    summary_agent: Optional[Agent] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tool_max_retries: int = 3

    def get_active_agents(self) -> list[Agent]:
        """Return only enabled agents in order."""
        return [a for a in self.agents if a.enabled]

    def get_current_agent(self) -> Optional[Agent]:
        """Return the currently active agent."""
        active = self.get_active_agents()
        if not active:
            return None
        return active[self.current_agent_index % len(active)]

    def advance(self) -> Optional[Agent]:
        """Advance to the next agent, cycling through rounds.

        Returns:
            The next agent to act, or None if session is complete.
        """
        active = self.get_active_agents()
        if not active:
            return None

        self.current_agent_index += 1
        if self.current_agent_index >= len(active):
            self.current_agent_index = 0
            self.current_round += 1

        self.updated_at = datetime.now()
        return self.get_current_agent()

    def is_complete(self) -> bool:
        """Check if the session has completed all rounds."""
        return self.current_round >= self.max_rounds
