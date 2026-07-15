"""Core orchestration engine for AI Arena.

The Orchestrator acts as middleware between AI agents in a ping-pong loop.
It detects, executes, and validates tool calls, with retry logic and
audit logging.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config import config
from ..engine.rate_limiter import RateLimiter
from ..engine.tool_executor import ToolExecutor, build_tool_result_envelope
from ..engine.tool_registry import ToolRegistry, tool_registry
from ..engine.tool_parser import ToolCallParseError, has_tool_call, parse_tool_call
from ..models.agent import Agent
from ..models.message import Message
from ..models.session_state import SessionState
from ..providers.base import BaseProvider, ProviderError
from ..tools.file_tools import compute_diff
from .session import SessionManager


class Orchestrator:
    """Main orchestration engine acting as middleware between AI agents.

    The middleware flow for each agent turn:
    1. Call the agent with its system prompt + conversation history
    2. Detect whether the response contains a tool call
    3. If tool call → execute it → return result to same agent (retry loop)
    4. If clean execution → forward updated context to next agent
    5. If no tool call → forward response to next agent
    """

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        rate_limiter: RateLimiter | None = None,
        tool_registry_instance: ToolRegistry | None = None,
        max_tool_retries: int = 3,
    ) -> None:
        """Initialize orchestrator.

        Args:
            session_manager: Session manager instance. Created if not provided.
            rate_limiter: Rate limiter instance. Created if not provided.
            tool_registry_instance: Tool registry. Uses global if not provided.
            max_tool_retries: Maximum retry attempts for failed tool calls.
        """
        self.session_manager = session_manager or SessionManager()
        self.rate_limiter = rate_limiter or RateLimiter()
        self._stop_event = False
        self._state_lock = threading.Lock()
        self._loop_thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        self._last_error: Optional[str] = None
        self._providers: dict[str, BaseProvider] = {}
        self.tool_registry = tool_registry_instance or tool_registry
        self.max_tool_retries = max_tool_retries

    # -- Thread-safe status accessors -----------------------------------------
    # The background loop writes these flags; the Streamlit main thread reads
    # them on every rerun. Sharing via a lock avoids corrupting
    # ``st.session_state`` from a non-main thread.

    def is_loop_running(self) -> bool:
        """Return whether the background loop is currently executing."""
        with self._state_lock:
            return self._is_running

    def consume_last_error(self) -> Optional[str]:
        """Atomically read and clear the latest background-loop error."""
        with self._state_lock:
            err = self._last_error
            self._last_error = None
            return err

    def _set_loop_running(self, value: bool) -> None:
        with self._state_lock:
            self._is_running = value

    def _set_last_error(self, message: Optional[str]) -> None:
        with self._state_lock:
            self._last_error = message

    def is_loop_alive(self) -> bool:
        """Return whether the background thread has been started and is alive."""
        thread = self._loop_thread
        return thread is not None and thread.is_alive()

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Register a provider by name."""
        self._providers[name.lower()] = provider

    def get_provider(self, name: str) -> BaseProvider | None:
        """Get a registered provider by name."""
        return self._providers.get(name.lower())

    def get_available_providers(self) -> list[str]:
        """Return list of registered provider names."""
        return list(self._providers.keys())

    def _get_tool_manual(self) -> str:
        """Get the auto-generated tool manual for prompt injection.

        Returns:
            Markdown tool manual string.
        """
        return self.tool_registry.get_manual()

    def _build_system_prompt(self, agent: Agent, inject_tools: bool = True) -> str:
        """Build the system prompt for an agent.

        Args:
            agent: The agent to build the prompt for.
            inject_tools: Whether to inject the tool manual.

        Returns:
            Complete system prompt string.
        """
        prompt = agent.system_prompt
        if inject_tools:
            prompt = prompt + "\n\n" + self._get_tool_manual()
        return prompt

    def _build_messages(
        self,
        agent: Agent,
        session: SessionState,
        tool_result_envelope: str | None = None,
    ) -> list[dict[str, str]]:
        """Build the message list for a provider API call.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            tool_result_envelope: Optional tool result to inject as user message.

        Returns:
            List of message dicts for the provider.
        """
        messages: list[dict[str, str]] = []

        # System message with agent instructions and available tools
        inject_tools = session.current_round == 0 and not tool_result_envelope
        system_content = self._build_system_prompt(agent, inject_tools=inject_tools)
        messages.append({"role": "system", "content": system_content})

        # If we're retrying after a tool failure, inject the error envelope
        if tool_result_envelope:
            messages.append({"role": "user", "content": tool_result_envelope})

        # Recent conversation history (last 10 messages to avoid token bloat)
        recent = session.messages[-10:] if len(session.messages) > 10 else session.messages
        for msg in recent:
            role = "user" if msg.agent_id != agent.id else "assistant"
            messages.append({"role": role, "content": msg.content})

        return messages

    def _call_provider(
        self,
        agent: Agent,
        session: SessionState,
        tool_result_envelope: str | None = None,
    ) -> str:
        """Call the provider API for the given agent.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            tool_result_envelope: Optional tool result to inject.

        Returns:
            Response text from the model.

        Raises:
            ProviderError: If the API call fails.
        """
        provider = self.get_provider(agent.provider)
        if provider is None:
            raise ProviderError(f"Provider '{agent.provider}' is not registered.")

        messages = self._build_messages(agent, session, tool_result_envelope)

        if session.is_dry_run:
            return self._simulate_response(agent, session)

        try:
            response = provider.chat(
                messages=messages,
                model=agent.model,
                api_key=agent.api_key,
                max_tokens=agent.max_tokens,
            )
            return response
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Unexpected error calling {provider.name}: {exc}") from exc

    def _simulate_response(self, agent: Agent, session: SessionState) -> str:
        """Generate a simulated response for dry-run mode.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.

        Returns:
            Simulated response text.
        """
        round_num = session.current_round
        return (
            f"[DRY RUN] {agent.name} ({agent.role.value}) simulated response for round {round_num}.\n"
            f"This is a placeholder. In production, this would be the actual model output."
        )

    def _read_context(self, session: SessionState) -> str:
        """Read the current shared context file.

        Args:
            session: Current session state.

        Returns:
            Current context content.
        """
        ctx_path = Path(session.context_file_path)
        return ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else ""

    def _update_context(self, session: SessionState, content: str) -> tuple[str, str]:
        """Update the shared context file with new content.

        Args:
            session: Current session state.
            content: New content to write.

        Returns:
            Tuple of (new_content, diff_string).
        """
        ctx_path = Path(session.context_file_path)
        old_content = self._read_context(session)
        new_content = content
        diff = compute_diff(old_content, new_content)
        ctx_path.write_text(new_content, encoding="utf-8")
        return new_content, diff

    def _append_agent_turn_to_context(
        self, context: str, agent: Agent, response: str, round_number: int
    ) -> str:
        """Append agent response to context file content.

        Args:
            context: Current context content.
            agent: The agent that produced the response.
            response: The agent's response text.
            round_number: Current round number (1-indexed).

        Returns:
            Updated context content.
        """
        separator = "\n\n---\n\n"
        entry = f"## {agent.name} (Round {round_number})\n\n{response}"
        if context.strip():
            return context + separator + entry
        return entry

    def run_turn(
        self,
        session: SessionState,
    ) -> Optional[Message]:
        """Execute a single agent turn with full middleware logic.

        The middleware flow:
        1. Call the agent
        2. Check for tool calls in the response
        3. If tool call → execute with retries → return result to same agent
        4. If clean execution → forward to next agent
        5. If no tool call → forward to next agent

        Args:
            session: Current session state.

        Returns:
            The Message created by this turn, or None if stopped.
        """
        agent = session.get_current_agent()
        if agent is None:
            return None

        if self._stop_event:
            return None

        # Wait for rate limit
        self.rate_limiter.wait()

        # Initialize tool executor for this turn
        executor = ToolExecutor(
            registry=self.tool_registry,
            max_retries=session.tool_max_retries,
            session_id=session.id,
        )

        # Call the agent (first attempt)
        try:
            response = self._call_provider(agent, session)
        except ProviderError as exc:
            error_msg = Message(
                agent_id=agent.id,
                agent_name=agent.name,
                content=f"[ERROR] Provider call failed: {exc}",
                round_number=session.current_round,
                is_system=True,
            )
            session.messages.append(error_msg)
            self.session_manager._save_session(session)
            return error_msg

        # Process tool calls in the response (retry loop)
        final_response = self._process_tool_calls(
            agent=agent,
            session=session,
            executor=executor,
            response=response,
        )

        if final_response is None:
            return None

        # Update context with the final response
        current_context = self._read_context(session)
        new_context = self._append_agent_turn_to_context(
            current_context, agent, final_response, round_number=session.current_round + 1
        )
        _, diff = self._update_context(session, new_context)

        # Record message
        had_tool = has_tool_call(final_response)
        message = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=final_response,
            round_number=session.current_round,
            context_diff=diff,
            had_tool_call=had_tool,
        )
        session.messages.append(message)
        session.updated_at = datetime.now()
        self.session_manager._save_session(session)

        return message

    def _process_tool_calls(
        self,
        agent: Agent,
        session: SessionState,
        executor: ToolExecutor,
        response: str,
    ) -> str | None:
        """Process tool calls in an agent response with retry logic.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            executor: Tool executor instance.
            response: Initial response from the agent.

        Returns:
            Final response text after all tool calls are resolved, or None if stopped.
        """
        current_response = response
        max_inner_loops = 5  # Prevent infinite tool call loops

        for _ in range(max_inner_loops):
            if self._stop_event:
                return None

            # Check if the response contains a tool call
            if not has_tool_call(current_response):
                return current_response

            # Process the tool call
            processed_response, had_tool = executor.process_response(current_response)

            if not had_tool:
                return current_response

            if processed_response == "":
                # Tool call succeeded silently — continue to next agent
                return current_response

            # Tool call failed — inject error envelope and retry with same agent
            error_envelope = processed_response

            # Record the tool failure in conversation
            tool_failure_msg = Message(
                agent_id=agent.id,
                agent_name=agent.name,
                content=error_envelope,
                round_number=session.current_round,
                is_system=True,
                had_tool_call=True,
            )
            session.messages.append(tool_failure_msg)
            self.session_manager._save_session(session)

            # Retry: call the same agent with the error envelope
            try:
                self.rate_limiter.wait()
                current_response = self._call_provider(
                    agent, session, tool_result_envelope=error_envelope
                )
            except ProviderError as exc:
                error_msg = Message(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    content=f"[ERROR] Retry provider call failed: {exc}",
                    round_number=session.current_round,
                    is_system=True,
                )
                session.messages.append(error_msg)
                self.session_manager._save_session(session)
                return error_msg.content

        # Max inner loops exceeded — graceful degradation
        warning_msg = (
            f"[WARNING] Agent {agent.name} exceeded maximum tool call iterations. "
            f"Skipping tool step and continuing with current response."
        )
        degradation_msg = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=warning_msg,
            round_number=session.current_round,
            is_system=True,
        )
        session.messages.append(degradation_msg)
        self.session_manager._save_session(session)
        return current_response

    def start_session(
        self,
        session: SessionState,
        initial_prompt: str = "",
    ) -> None:
        """Start the orchestration loop for a session.

        Args:
            session: Session to start.
            initial_prompt: Optional initial prompt to seed the context.
        """
        self._stop_event = False
        session.is_running = True
        session.is_paused = False
        session.current_round = 0
        session.current_agent_index = 0
        session.messages = []

        # Update the existing rate limiter's delay without rebuilding it,
        # so the previous ``_last_call`` timestamp is preserved and burst
        # protection still applies to the first call after a resume.
        self.rate_limiter.delay_seconds = float(session.rate_limit_seconds)

        if initial_prompt:
            ctx_path = Path(session.context_file_path)
            ctx_path.write_text(f"# Initial Prompt\n\n{initial_prompt}\n", encoding="utf-8")

        self.session_manager._save_session(session)

    def stop_session(self, session: SessionState) -> None:
        """Stop the orchestration loop."""
        self._stop_event = True
        session.is_running = False
        session.is_paused = False
        self.session_manager._save_session(session)

    def pause_session(self, session: SessionState) -> None:
        """Pause the orchestration loop."""
        session.is_paused = True
        session.is_running = False
        self.session_manager._save_session(session)

    def resume_session(self, session: SessionState) -> None:
        """Resume a paused session."""
        session.is_paused = False
        session.is_running = True
        self._stop_event = False
        self.session_manager._save_session(session)

    def step(self, session: SessionState) -> Optional[Message]:
        """Execute a single step (one agent turn).

        Args:
            session: Current session state.

        Returns:
            The Message from this turn, or None.
        """
        if session.is_paused or not session.is_running:
            return None
        if session.is_complete():
            session.is_running = False
            self.session_manager._save_session(session)
            return None

        message = self.run_turn(session)
        if message:
            session.advance()

        self.session_manager._save_session(session)
        return message

    def run_loop(self, session: SessionState, poll_interval: float = 0.5) -> None:
        """Background loop body. Designed to run in a daemon thread.

        Exits when ``session.is_running`` flips to False, when
        ``session.is_complete()`` is True, or when an exception bubbles up.
        All state changes go through the orchestrator's lock-protected
        accessors so the main (Streamlit) thread can read them safely.
        """
        self._set_loop_running(True)
        try:
            while session.is_running and not session.is_paused:
                if session.is_complete():
                    session.is_running = False
                    break
                try:
                    self.step(session)
                except Exception as exc:  # noqa: BLE001 — top-level guard
                    self._set_last_error(f"{type(exc).__name__}: {exc}")
                    session.is_running = False
                    break
                # Cooperative sleep — keeps the thread cheap to interrupt.
                time.sleep(poll_interval)
        finally:
            self._set_loop_running(False)
            try:
                self.session_manager._save_session(session)
            except Exception:  # noqa: BLE001
                pass

    def start_background(self, session: SessionState) -> threading.Thread:
        """Spawn the orchestration loop in a daemon thread.

        Returns the thread handle so the caller can join() if needed.
        If a previous thread is still alive, returns it without spawning
        a second one.
        """
        existing = self._loop_thread
        if existing is not None and existing.is_alive():
            return existing
        thread = threading.Thread(
            target=self.run_loop,
            args=(session,),
            daemon=True,
        )
        self._loop_thread = thread
        thread.start()
        return thread
