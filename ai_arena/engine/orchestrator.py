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
from ..tools.base import ToolResult
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
        self._stop_event = threading.Event()
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

    def _build_system_prompt(
        self,
        agent: Agent,
        session: SessionState | None = None,
        inject_tools: bool = True,
    ) -> str:
        """Build the system prompt for an agent.

        Args:
            agent: The agent to build the prompt for.
            session: Current session. When provided, ``{ctx_path}`` in
                the agent's prompt is substituted with the session's
                context file path. Without this, agents routinely
                hallucinate file paths like ``/shared/context.txt`` and
                the entire loop dies before any useful output is
                produced. The old ``{round}`` placeholder is gone —
                the file is the state, round numbers are not surfaced
                to the model anymore.
            inject_tools: Whether to inject the tool manual.

        Returns:
            Complete system prompt string.
        """
        prompt = agent.system_prompt
        if session is not None:
            prompt = prompt.replace(
                "{ctx_path}", session.context_file_path
            )
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

        The model sees ONLY the system prompt and a single user message.
        The user message includes the current state of the context file
        inlined as a fenced code block — this is how the orchestrator
        injects the file content into the model. The model does NOT need
        to call ``read_file`` to see the file; the orchestrator handles
        that. The model only calls ``write_file`` with its improved
        version.

        Why inject instead of asking the model to read_file:
        - One shot per turn. The model can't get into a read loop because
          we never re-send a tool envelope back to the same agent.
        - File content is guaranteed to be in the model's context every
          turn, not gated on the model deciding to call read_file.
        - Smaller surface area for the model to misbehave on.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            tool_result_envelope: Optional tool result to inject as the
                user message when retrying after a tool call. With the
                new one-shot flow this is rarely set.

        Returns:
            List of message dicts for the provider.
        """
        messages: list[dict[str, str]] = []

        # System message with agent instructions and tool manual.
        inject_tools = not tool_result_envelope
        system_content = self._build_system_prompt(
            agent, session=session, inject_tools=inject_tools
        )
        messages.append({"role": "system", "content": system_content})

        # Single user message drives this turn.
        # - Tool retry path: hand the tool result envelope back.
        # - Otherwise: inline the current file state so the model can
        #   produce a write_file call without needing read_file.
        if tool_result_envelope:
            messages.append({"role": "user", "content": tool_result_envelope})
        else:
            current = self._read_context(session) or "(empty file)"
            messages.append({
                "role": "user",
                "content": (
                    f"Current state of the context file "
                    f"({session.context_file_path}):\n\n"
                    f"```\n{current}\n```\n\n"
                    "Produce your improved version. Call write_file with "
                    "the COMPLETE new content of the file. "
                    "Do not call read_file — the current state is above."
                ),
            })

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

        if self._stop_event.is_set():
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
            # Return None so step() does NOT advance past the failed agent.
            # The loop will retry this agent on the next iteration.
            return None

        # Process tool calls in the response (one shot per turn).
        # The orchestrator does NOT re-call the agent with the tool
        # envelope — that's how the read loop happened.
        final_response, last_result = self._process_tool_calls(
            agent=agent,
            session=session,
            executor=executor,
            response=response,
        )

        # If final_response is None, a tool call was processed and
        # _process_tool_calls already recorded the envelope message.
        # Skip the duplicate message append.
        if final_response is None:
            session.updated_at = datetime.now()
            self.session_manager._save_session(session)
            return None

        # No tool call was processed — record a normal agent message.
        message = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=final_response,
            round_number=session.current_round,
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
    ) -> tuple[str | None, ToolResult | None]:
        """Process AT MOST ONE tool call in an agent's response, then
        return. The orchestrator does NOT re-call the same agent with the
        tool envelope — that's how the read loop happened.

        One shot per turn:
        1. If the response has no tool call → return (response, None).
        2. If the response has a tool call → execute it (write_file
           updates the context file, read_file is now a no-op since the
           orchestrator already injects the file content in the user
           message), record the envelope in session.messages, and
           return (envelope, last_result).
        3. The next agent then gets a fresh user message with the
           (possibly updated) file content.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            executor: Tool executor instance.
            response: Initial response from the agent.

        Returns:
            Tuple of (final_response, last_result). last_result is None
            when no tool call was processed. final_response is None if
            the session was stopped.
        """
        if self._stop_event.is_set():
            return None, None

        if not has_tool_call(response):
            return response, None

        processed_response, had_tool, last_result = executor.process_response(response)

        if not had_tool or last_result is None:
            return response, None

        # Record the tool result envelope in the message log. We mark
        # it as a system message so the UI shows it under the SYS badge.
        # Do NOT return the raw envelope as the agent message — that's
        # internal protocol data. The caller (run_turn) will NOT append
        # a duplicate message for tool-call turns.
        envelope_msg = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=processed_response,
            round_number=session.current_round,
            is_system=True,
            had_tool_call=True,
            tool_result=last_result.output,
        )
        session.messages.append(envelope_msg)
        self.session_manager._save_session(session)

        # Return None as the agent response so run_turn skips the
        # duplicate message append. The envelope_msg above is the
        # sole record for this turn.
        return None, last_result

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
        self._stop_event.clear()
        session.is_running = True
        session.is_paused = False
        session.current_round = 0
        session.current_agent_index = 0
        session.messages = []
        # Stash the task brief on the session so it can be sent to the
        # model as the first user message on round 0. The context file
        # itself stays as a clean skeleton — agents never see the
        # initial prompt again unless they re-read the file.
        session.initial_prompt = initial_prompt

        # Update the existing rate limiter's delay without rebuilding it,
        # so the previous ``_last_call`` timestamp is preserved and burst
        # protection still applies to the first call after a resume.
        self.rate_limiter.delay_seconds = float(session.rate_limit_seconds)

        # Seed the context file with the initial task. The file is the
        # single source of truth: every subsequent agent reads the file
        # and rewrites it in full. The "## Initial Task" section must
        # be preserved verbatim by every rewrite so the task brief
        # never gets lost, and the "## Working Draft" section is the
        # area agents replace wholesale (write_file, not append_file).
        ctx_path = Path(session.context_file_path)
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        seed = (
            "# Shared Context\n\n"
            "## Initial Task\n"
            f"{initial_prompt or '(no initial prompt provided)'}\n\n"
            "---\n\n"
            "## Working Draft\n"
            "<!-- Agents rewrite everything below this line. "
            "Keep the # Shared Context header and the ## Initial Task "
            "section above intact; replace the rest in full. -->\n"
        )
        ctx_path.write_text(seed, encoding="utf-8")

        self.session_manager._save_session(session)

    def stop_session(self, session: SessionState) -> None:
        """Stop the orchestration loop."""
        self._stop_event.set()
        session.is_running = False
        session.is_paused = False
        self.session_manager._save_session(session)

    def pause_session(self, session: SessionState) -> None:
        """Pause the orchestration loop."""
        self._stop_event.set()
        session.is_paused = True
        session.is_running = False
        self.session_manager._save_session(session)

    def resume_session(self, session: SessionState) -> None:
        """Resume a paused session."""
        session.is_paused = False
        session.is_running = True
        self._stop_event.clear()
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
            while session.is_running and not session.is_paused and not self._stop_event.is_set():
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
