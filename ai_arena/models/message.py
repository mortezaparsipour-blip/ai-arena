"""Message model for conversation history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """Represents a single message in the conversation history.

    Attributes:
        agent_id: ID of the agent that sent this message.
        agent_name: Display name of the agent.
        content: Message content.
        timestamp: When the message was created.
        round_number: Which round of the ping-pong loop this belongs to.
        is_system: Whether this is a system-level message.
        context_diff: Optional diff of context file changes after this message.
        had_tool_call: Whether this message contained a tool call.
        tool_result: Tool execution result if this is a tool result message.
    """

    agent_id: str
    agent_name: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0
    is_system: bool = False
    context_diff: Optional[str] = None
    had_tool_call: bool = False
    tool_result: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize message to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "round_number": self.round_number,
            "is_system": self.is_system,
            "context_diff": self.context_diff,
        }
