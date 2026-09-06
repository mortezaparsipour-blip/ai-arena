"""Core orchestration engine for AI Arena.

The Orchestrator acts as middleware between AI agents in a ping-pong loop.
It detects, executes, and validates tool calls, with retry logic and
audit logging.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

from ..engine.rate_limiter import RateLimiter
from ..engine.tool_executor import ToolExecutor
from ..engine.tool_registry import ToolRegistry, tool_registry
from ..engine.tool_parser import has_tool_call
from ..models.agent import Agent
from ..models.message import Message
from ..models.session_state import SessionState
from ..providers.base import BaseProvider, ProviderError
from ..tools.base import ToolResult
from ..tools.file_tools import compute_diff, set_active_context_path
from .session import SessionManager


class Orchestrator:
    """Main orchestration engine acting as middleware between AI agents.

    One shot per turn:
    1. Call the agent with its system prompt + a single user message that
       inlines the current context file content
    2. Detect whether the response contains a tool call
    3. If tool call → execute it once → record the envelope message → the
       turn ends (the provider is NOT re-called with the result)
    4. If no tool call → record the agent message + a no-write warning
    5. Either way the turn's message is returned, and the caller (step)
       advances to the next agent. Only a failed/stopped turn returns None
       and leaves the loop positioned on the same agent.
    """

    # Id of the session the background loop is currently executing. Kept as
    # a class attribute default so ``__new__``-constructed test fakes that
    # never run ``__init__`` still read ``None`` instead of raising.
    _loop_session_id: Optional[str] = None

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        rate_limiter: RateLimiter | None = None,
        tool_registry_instance: ToolRegistry | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            session_manager: Session manager instance. Created if not provided.
            rate_limiter: Rate limiter instance. Created if not provided.
            tool_registry_instance: Tool registry. Uses global if not provided.
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

    def get_running_session_id(self) -> Optional[str]:
        """Return the id of the session the background loop is executing."""
        with self._state_lock:
            return self._loop_session_id

    def _set_loop_session_id(self, session_id: Optional[str]) -> None:
        with self._state_lock:
            self._loop_session_id = session_id

    def ensure_startable(self, session: SessionState) -> None:
        """Raise if the background loop is busy with a *different* session.

        Starting session B while the loop still runs session A would flag B
        as ``is_running`` with no worker actually processing it — the UI
        then shows a phantom "Running" state. Callers (UI Start/Resume)
        catch the error and tell the user to stop the current session first.

        Raises:
            RuntimeError: If the loop thread is alive on another session.
        """
        if self.is_loop_alive() and self.get_running_session_id() != session.id:
            raise RuntimeError(
                "Another session is already running in the background. "
                "Stop it before starting this one."
            )

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

        Returns:
            List of message dicts for the provider.
        """
        messages: list[dict[str, str]] = []

        # System message with agent instructions and tool manual.
        system_content = self._build_system_prompt(
            agent, session=session, inject_tools=True
        )
        messages.append({"role": "system", "content": system_content})

        # Single user message drives this turn: inline the current file
        # state so the model can produce a write_file call without needing
        # read_file.
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
    ) -> str:
        """Call the provider API for the given agent.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.

        Returns:
            Response text from the model.

        Raises:
            ProviderError: If the API call fails.
        """
        provider = self.get_provider(agent.provider)
        if provider is None:
            raise ProviderError(f"Provider '{agent.provider}' is not registered.")

        messages = self._build_messages(agent, session)

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

    def run_turn(
        self,
        session: SessionState,
    ) -> Optional[Message]:
        """Execute a single agent turn with full middleware logic.

        One shot per turn:
        1. Call the agent exactly once
        2. If the response carries a tool call, execute it once and record
           the envelope message (the provider is NOT re-called)
        3. Otherwise record the agent message + a no-write warning

        Args:
            session: Current session state.

        Returns:
            The Message created by this turn — the envelope message for
            tool-call turns, the agent message for prose turns — or None
            when the turn failed (provider error) or the session was
            stopped. The caller advances to the next agent only on a
            non-None result.
        """
        agent = session.get_current_agent()
        if agent is None:
            return None

        if self._stop_event.is_set():
            return None

        # Wait for rate limit
        self.rate_limiter.wait()

        # Bind the file-tool sandbox to this session's context file for
        # the duration of the turn. Mutating tools (write/append/patch)
        # will refuse any path that doesn't resolve to it, so a
        # hallucinated ``write_file {"path": ".env"}`` is rejected
        # before touching disk.
        set_active_context_path(session.context_file_path)

        # Initialize tool executor for this turn
        executor = ToolExecutor(
            registry=self.tool_registry,
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
            # Bump the consecutive-error counter. If the threshold is
            # reached, stop the session outright so a persistent failure
            # (bad API key, dead endpoint) cannot spin the loop forever.
            # Below the threshold, leave is_running True so transient
            # failures (rate-limit, brief network blip) get another try.
            should_stop = session.record_provider_error()
            if should_stop:
                session.is_running = False
                self._set_last_error(
                    f"Stopping after {session.max_consecutive_errors} consecutive "
                    f"provider errors. Last: {exc}"
                )
            # Return None so step() does NOT advance past the failed
            # agent — the next iteration either retries the same agent
            # or, once the threshold trips, exits via is_running.
            # Persistence is owned by step(), which saves after we return.
            return None

        # Process tool calls in the response (one shot per turn).
        # The orchestrator does NOT re-call the agent with the tool
        # envelope — that's how the read loop happened.
        final_response, last_result, turn_message = self._process_tool_calls(
            agent=agent,
            session=session,
            executor=executor,
            response=response,
        )

        # Tool-call turn: _process_tool_calls already recorded the envelope
        # message. Return it so step() advances to the next agent — this is
        # the fix for the regression that left the loop positioned on the
        # same agent forever, re-billing an API call on every retry.
        if turn_message is not None:
            session.record_success()
            return turn_message

        if final_response is None:
            # The session was stopped before/while processing the tool
            # call — nothing to record, nothing to advance.
            return None

        # No tool call was processed — record a normal agent message.
        message = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=final_response,
            round_number=session.current_round,
        )
        session.messages.append(message)
        # Surface a warning so the user knows this turn produced no
        # file change. Without it, an agent that replies with prose
        # looks indistinguishable from a successful rewrite — the next
        # agent then re-reads an unchanged file and the session stalls
        # without any visible signal. We DON'T fail the turn: prose is
        # a valid response, just an unproductive one.
        warning = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=(
                f"[WARNING] {agent.name} did not call write_file this turn — "
                f"the shared context was not updated. The next agent will see "
                f"the same file state."
            ),
            round_number=session.current_round,
            is_system=True,
        )
        session.messages.append(warning)
        session.record_success()

        return message

    def _process_tool_calls(
        self,
        agent: Agent,
        session: SessionState,
        executor: ToolExecutor,
        response: str,
    ) -> tuple[str | None, ToolResult | None, Message | None]:
        """Process AT MOST ONE tool call in an agent's response, then
        return. The orchestrator does NOT re-call the same agent with the
        tool envelope — that's how the read loop happened.

        One shot per turn:
        1. If the response has no tool call → return (response, None, None).
        2. If the response has a tool call → execute it (write_file
           updates the context file, read_file is now a no-op since the
           orchestrator already injects the file content in the user
           message), record the envelope in session.messages, and
           return (None, last_result, envelope_msg).
        3. The next agent then gets a fresh user message with the
           (possibly updated) file content.

        Args:
            agent: The agent whose turn it is.
            session: Current session state.
            executor: Tool executor instance.
            response: Initial response from the agent.

        Returns:
            Tuple of (final_response, last_result, turn_message).
            - No tool call (or an unparseable fence): ``(response, None,
              None)`` — the caller treats the response as prose.
            - Tool call processed: ``(None, last_result, envelope_msg)`` —
              the envelope message is the sole record for this turn and is
              already appended to session.messages. The caller returns it
              so step() advances to the next agent.
            - Session stopped: ``(None, None, None)``.
        """
        if self._stop_event.is_set():
            return None, None, None

        if not has_tool_call(response):
            return response, None, None

        # Snapshot the context file BEFORE the tool runs. After execution
        # we diff old vs new so the UI's "Diff" tab and the per-message
        # "Context Diff" expander actually have something to show. This
        # is the only place the orchestrator learns what the write
        # changed — write_file itself just reports a byte count.
        old_context = self._read_context(session)

        processed_response, had_tool, last_result = executor.process_response(response)

        if not had_tool or last_result is None:
            return response, None, None

        # Compute the diff for the just-applied write (if any). Only
        # surface a non-empty diff when the file actually changed, so
        # the UI doesn't show noise for read-only or no-op tool calls.
        new_context = self._read_context(session)
        diff = ""
        if new_context != old_context:
            diff = compute_diff(old_context, new_context)

        # Record the tool result envelope in the message log. We mark
        # it as a system message so the UI shows it under the SYS badge.
        # Do NOT return the raw envelope as the agent message — that's
        # internal protocol data. The envelope_msg is the sole record
        # for this turn; the caller returns it so step() advances.
        envelope_msg = Message(
            agent_id=agent.id,
            agent_name=agent.name,
            content=processed_response,
            round_number=session.current_round,
            is_system=True,
            had_tool_call=True,
            tool_result=last_result.output,
            context_diff=diff or None,
        )
        session.messages.append(envelope_msg)

        return None, last_result, envelope_msg

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
        # Fresh start: clear any stale error streak from a prior run so
        # the loop doesn't immediately bail out because of failures that
        # happened before the user hit Start again.
        session.consecutive_errors = 0
        # Keep the task brief on the session for persistence and export.
        # The model never receives ``initial_prompt`` as a message — the
        # brief reaches agents through the context file, which is seeded
        # with it right below. One channel, one source of truth.
        session.initial_prompt = initial_prompt

        # Update the existing rate limiter's delay without rebuilding it,
        # so the previous ``_last_call`` timestamp is preserved and burst
        # protection still applies to the first call after a resume.
        self.rate_limiter.delay_seconds = float(session.rate_limit_seconds)

        ctx_path = Path(session.context_file_path)
        ctx_path.parent.mkdir(parents=True, exist_ok=True)

        # If the context file already holds agent work (not just a fresh
        # seed), preserve a backup before we overwrite it. ``start_session``
        # is "restart from scratch" semantics; users who wanted to pick
        # up where they left off should hit Resume instead. But clicking
        # Start by accident shouldn't be destructive — the snapshot is
        # cheap insurance and lives next to the live file.
        self._backup_context_if_needed(ctx_path)

        # Seed the context file with the initial task. The file is the
        # single source of truth: every subsequent agent reads the file
        # and rewrites it in full. The "## Initial Task" section must
        # be preserved verbatim by every rewrite so the task brief
        # never gets lost, and the "## Working Draft" section is the
        # area agents replace wholesale (write_file, not append_file).
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

    @staticmethod
    def _backup_context_if_needed(ctx_path: Path) -> None:
        """Copy ``ctx_path`` to a ``.bak.md`` sibling if it holds real work.

        "Real work" means the working draft has content beyond the seed
        placeholder comment. A freshly seeded file (or an empty one) is
        not backed up — there is nothing to lose.

        Failures are swallowed: backups are best-effort safety nets and
        must never block a start.
        """
        if not ctx_path.exists():
            return
        try:
            content = ctx_path.read_text(encoding="utf-8")
        except OSError:
            return
        # Skip if the working draft is empty / just the seed placeholder.
        marker = "## Working Draft"
        idx = content.find(marker)
        if idx < 0:
            return
        body = content[idx + len(marker):]
        # Strip the seed comment and whitespace; anything left means an
        # agent wrote something worth keeping.
        stripped = body.replace(
            "<!-- Agents rewrite everything below this line. "
            "Keep the # Shared Context header and the ## Initial Task "
            "section above intact; replace the rest in full. -->",
            "",
        ).strip()
        if not stripped:
            return
        backup_path = ctx_path.with_suffix(".bak.md")
        try:
            backup_path.write_text(content, encoding="utf-8")
        except OSError:
            pass

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
            The Message from this turn — the agent message for prose
            turns or the envelope message for tool-call turns — or None
            when the turn failed or was stopped. Only a non-None result
            advances the loop to the next agent.
        """
        if session.is_paused or not session.is_running:
            return None
        if session.is_complete():
            session.is_running = False
            self.session_manager._save_session(session)
            return None
        # No enabled agents means the loop has nothing to do. Bail out
        # instead of spinning forever calling run_turn → None.
        if not session.has_enabled_agents():
            session.is_running = False
            self._set_last_error(
                "Session has no enabled agents. Enable at least one agent "
                "in the sidebar before starting."
            )
            self.session_manager._save_session(session)
            return None

        message = self.run_turn(session)
        if message is not None:
            session.advance()

        # Single persistence point per turn: run_turn mutates messages and
        # the success/error counters, advance() mutates the loop position —
        # one save here covers both.
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
        self._set_loop_session_id(session.id)
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
            self._set_loop_session_id(None)
            try:
                self.session_manager._save_session(session)
            except Exception:  # noqa: BLE001
                pass

    def start_background(self, session: SessionState) -> threading.Thread:
        """Spawn the orchestration loop in a daemon thread.

        Returns the thread handle so the caller can join() if needed.
        If the loop is already alive on this same session, returns the
        existing thread instead of spawning a second one.

        Raises:
            RuntimeError: If the loop is alive on a *different* session.
                Starting a second session would leave it flagged
                ``is_running`` with no worker processing it (the phantom
                "Running" state). Callers should stop the current session
                first — the UI does this via ``ensure_startable``.
        """
        existing = self._loop_thread
        if existing is not None and existing.is_alive():
            self.ensure_startable(session)
            return existing
        # Claim the loop slot before starting the thread so a concurrent
        # start_background call sees the correct session id immediately.
        self._set_loop_session_id(session.id)
        thread = threading.Thread(
            target=self.run_loop,
            args=(session,),
            daemon=True,
        )
        self._loop_thread = thread
        thread.start()
        return thread
