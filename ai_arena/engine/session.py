"""Session manager for multi-session support."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.agent import Agent
from ..models.session_state import SessionState
from ..config import config


class SessionManager:
    """Manages multiple named orchestration sessions.

    Sessions are persisted to disk as JSON files for multi-session support.
    """

    def __init__(self, storage_dir: Path | None = None) -> None:
        """Initialize session manager.

        Args:
            storage_dir: Directory for session storage. Defaults to config value.
        """
        self.storage_dir = storage_dir or config.context_storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionState] = {}
        self._active_session_id: str | None = None

    def create_session(
        self,
        name: str,
        agents: list[Agent],
        max_rounds: int = 10,
        rate_limit: int = 60,
        context_file: str | None = None,
        is_dry_run: bool = False,
        tool_max_retries: int = 3,
    ) -> SessionState:
        """Create a new session.

        Args:
            name: Human-readable session name.
            agents: List of agents in this session.
            max_rounds: Maximum ping-pong rounds.
            rate_limit: Rate limit delay in seconds.
            context_file: Optional custom context file path.
            is_dry_run: Whether this is a dry-run session.
            tool_max_retries: Max retries for failed tool calls.

        Returns:
            The newly created session state.
        """
        session_id = str(uuid.uuid4())[:8]
        ctx_path = context_file or str(config.get_context_path(session_id))

        session = SessionState(
            id=session_id,
            name=name,
            agents=agents,
            max_rounds=max_rounds,
            rate_limit_seconds=rate_limit,
            context_file_path=ctx_path,
            is_dry_run=is_dry_run,
            tool_max_retries=tool_max_retries,
        )

        # Initialize context file
        Path(ctx_path).write_text("", encoding="utf-8")

        self._sessions[session_id] = session
        self._active_session_id = session_id
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> SessionState | None:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def get_active_session(self) -> SessionState | None:
        """Return the currently active session."""
        if self._active_session_id:
            return self._sessions.get(self._active_session_id)
        return None

    def set_active_session(self, session_id: str) -> bool:
        """Set the active session by ID.

        Returns:
            True if session exists, False otherwise.
        """
        if session_id in self._sessions:
            self._active_session_id = session_id
            return True
        return False

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions with metadata."""
        result = []
        for sid, session in self._sessions.items():
            result.append({
                "id": sid,
                "name": session.name,
                "round": session.current_round,
                "max_rounds": session.max_rounds,
                "is_running": session.is_running,
                "is_paused": session.is_paused,
                "is_dry_run": session.is_dry_run,
                "agent_count": len(session.agents),
                "updated_at": session.updated_at.isoformat(),
            })
        return result

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its context file.

        Returns:
            True if deleted, False if not found.
        """
        if session_id not in self._sessions:
            return False
        session = self._sessions.pop(session_id)
        ctx_path = Path(session.context_file_path)
        if ctx_path.exists():
            ctx_path.unlink()
        storage_file = self.storage_dir / f"session_{session_id}.json"
        if storage_file.exists():
            storage_file.unlink()
        if self._active_session_id == session_id:
            self._active_session_id = None
        return True

    def _save_session(self, session: SessionState) -> None:
        """Persist session state to disk."""
        data = {
            "id": session.id,
            "name": session.name,
            "agents": [a.to_dict() for a in session.agents],
            "messages": [m.to_dict() for m in session.messages],
            "context_file_path": session.context_file_path,
            "current_round": session.current_round,
            "current_agent_index": session.current_agent_index,
            "max_rounds": session.max_rounds,
            "rate_limit_seconds": session.rate_limit_seconds,
            "is_running": session.is_running,
            "is_paused": session.is_paused,
            "is_dry_run": session.is_dry_run,
            "tool_max_retries": session.tool_max_retries,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        storage_file = self.storage_dir / f"session_{session.id}.json"
        storage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
