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
    # The user-provided task brief. Stored on the session (not in the
    # context file) so it can be sent to the model as the first user
    # message on round 0 without polluting the agents' shared scratchpad.
    initial_prompt: str = ""
    current_round: int = 0
    current_agent_index: int = 0
    max_rounds: int = 10
    rate_limit_seconds: int = 5
    is_running: bool = False
    is_paused: bool = False
    is_dry_run: bool = False
    summary_agent: Optional[Agent] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tool_max_retries: int = 3
    # Consecutive provider-failure counter. Incremented on every
    # ProviderError, reset to 0 on any successful turn. When it reaches
    # ``max_consecutive_errors`` the orchestrator stops the session so a
    # persistent failure (bad API key, dead endpoint) cannot pin the
    # loop in an infinite retry storm. Transient failures (rate-limit,
    # brief network blip) get a few retries before giving up.
    consecutive_errors: int = 0
    max_consecutive_errors: int = 3

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

    def record_provider_error(self) -> bool:
        """Increment the consecutive-error counter.

        Returns:
            True if the threshold has been reached and the session
            should stop, False if more retries are allowed.
        """
        self.consecutive_errors += 1
        self.updated_at = datetime.now()
        return self.consecutive_errors >= self.max_consecutive_errors

    def record_success(self) -> None:
        """Reset the consecutive-error counter after a successful turn.

        A single success anywhere in the loop is enough to clear the
        streak — we only want to stop when failures pile up
        back-to-back.
        """
        if self.consecutive_errors:
            self.consecutive_errors = 0
            self.updated_at = datetime.now()

    def has_enabled_agents(self) -> bool:
        """Return whether at least one agent is enabled.

        The orchestration loop relies on ``get_current_agent`` returning
        a non-None agent; without one it would spin forever advancing
        nowhere. This predicate lets callers bail out cleanly.
        """
        return any(a.enabled for a in self.agents)
