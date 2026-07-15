"""Session manager for multi-session support."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models.agent import Agent
from ..models.message import Message
from ..models.session_state import SessionState
from ..config import config


class SessionManager:
    """Manages multiple named orchestration sessions.

    Sessions are persisted to disk as JSON files for multi-session support.
    On init, any previously saved session is reloaded into memory so that
    Streamlit reruns don't drop state.
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
        self._save_locks: dict[str, threading.Lock] = {}
        # Reload any sessions saved by previous runs.
        self._load_from_disk()

    def _save_lock(self, session_id: str) -> threading.Lock:
        """Return (and lazily create) a per-session lock for atomic writes."""
        lock = self._save_locks.get(session_id)
        if lock is None:
            lock = threading.Lock()
            self._save_locks[session_id] = lock
        return lock

    def _load_from_disk(self) -> None:
        """Load every ``session_*.json`` file under ``storage_dir`` into memory.

        The most recently updated session becomes the active one.
        """
        latest_id: str | None = None
        latest_updated: datetime | None = None
        for path in self.storage_dir.glob("session_*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                # Skip corrupted/partial files silently — they will be
                # overwritten on the next save.
                continue
            session = self._deserialize(data)
            if session is None:
                continue
            self._sessions[session.id] = session
            if latest_updated is None or session.updated_at > latest_updated:
                latest_updated = session.updated_at
                latest_id = session.id
        if latest_id is not None:
            self._active_session_id = latest_id

    def _deserialize(self, data: dict[str, Any]) -> SessionState | None:
        """Build a SessionState from a persisted dict.

        Returns None if the dict is missing required fields.
        """
        try:
            agents = [Agent.from_dict(a) for a in data.get("agents", [])]
            messages = [self._deserialize_message(m) for m in data.get("messages", [])]
            return SessionState(
                id=data["id"],
                name=data.get("name", data["id"]),
                agents=agents,
                messages=messages,
                context_file_path=data.get("context_file_path", "shared_context.md"),
                current_round=int(data.get("current_round", 0)),
                current_agent_index=int(data.get("current_agent_index", 0)),
                max_rounds=int(data.get("max_rounds", 10)),
                rate_limit_seconds=int(data.get("rate_limit_seconds", 60)),
                is_running=bool(data.get("is_running", False)),
                is_paused=bool(data.get("is_paused", False)),
                is_dry_run=bool(data.get("is_dry_run", False)),
                tool_max_retries=int(data.get("tool_max_retries", 3)),
                created_at=self._parse_dt(data.get("created_at")),
                updated_at=self._parse_dt(data.get("updated_at")),
            )
        except (KeyError, ValueError, TypeError):
            return None

    @staticmethod
    def _deserialize_message(data: dict[str, Any]) -> Message:
        """Rebuild a Message from a dict, tolerating missing optional fields."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            try:
                timestamp = datetime.fromisoformat(ts)
            except ValueError:
                timestamp = datetime.now()
        elif isinstance(ts, datetime):
            timestamp = ts
        else:
            timestamp = datetime.now()
        return Message(
            agent_id=data.get("agent_id", "unknown"),
            agent_name=data.get("agent_name", "Unknown"),
            content=data.get("content", ""),
            timestamp=timestamp,
            round_number=int(data.get("round_number", 0)),
            is_system=bool(data.get("is_system", False)),
            context_diff=data.get("context_diff"),
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime:
        """Parse an ISO-8601 timestamp string, falling back to ``now``."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()

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
        self._save_locks.pop(session_id, None)
        return True

    def _save_session(self, session: SessionState) -> None:
        """Persist session state to disk atomically.

        Writes to ``session_<id>.json.tmp`` first, then renames it to the
        final path. The rename is atomic on both POSIX and Windows, so a
        reader (or a concurrent writer crashing mid-write) will never observe
        a half-written JSON document.
        """
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
        tmp_file = storage_file.with_suffix(".json.tmp")
        lock = self._save_lock(session.id)
        payload = json.dumps(data, indent=2)
        with lock:
            try:
                with tmp_file.open("w", encoding="utf-8") as f:
                    f.write(payload)
                os.replace(tmp_file, storage_file)
            except OSError:
                # Best-effort cleanup; raise so the caller can decide.
                try:
                    if tmp_file.exists():
                        tmp_file.unlink()
                except OSError:
                    pass
                raise
