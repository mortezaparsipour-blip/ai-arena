# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-09-05

### Fixed (P0 + security + 20 findings from the full code review in `docs/glm5.3-flash final/`)

#### HIGH
- **No advance after tool-call turns (P0)** — `run_turn` returned `None` for tool-call turns and `step()` only advanced on a truthy message, so the loop stayed on the same agent forever: the model was re-prompted to `write_file` again, every iteration billed an API call, and `is_complete()` could never become True. Tool-call turns now return the envelope message and `step()` advances on any non-None result; only failed/stopped turns stay put. Regression test added (`test_one_shot_flow.py::test_7_step_advances_after_tool_call`).
- **`read_file` could read `.env` and session JSONs (SEC-1)** — the read sandbox only rejected paths *outside* the project root, but `.env`, `contexts/session_*.json` (which carries every agent's API key), `audit_*.log`, `.streamlit/` and `.git/` all live inside it. A deny-list (`config.is_sensitive_read_path`) now rejects those paths even inside the root.
- **Phantom "Running" after switching sessions (P1-1)** — `start_background` returned the alive thread of a *different* session, leaving the new session flagged running with no worker. The orchestrator now tracks the running session id, `start_background`/`ensure_startable` raise on a mismatch, and the UI shows an error instead of silently mis-starting.
- **`_save_session` was not atomic despite its docstring (P1-2)** — the write went straight to the target file, so a crash mid-write produced a truncated JSON that `_load_from_disk` silently skipped (losing the whole session). Now writes to `session_<id>.json.tmp` + `os.replace` with a short Windows `PermissionError` retry; corrupted files are logged as warnings on load.
- **OpenRouter key precedence was reversed (P1-3)** — `config.get_api_key("openrouter")` preferred `OPENAI_API_KEY` over `OPENROUTER_API_KEY`, sending the wrong key when both were set (401). The provider-specific variable now wins; `OPENAI_API_KEY` is only a fallback.

#### MEDIUM
- **Dead retry path removed (P1-4)** — the `tool_result_envelope` parameter of `_build_messages`/`_call_provider` was never passed (the one-shot flow never re-calls the provider). Removed, and the class/`run_turn` docstrings now describe the actual flow.
- **Tool manual misled the model (P2-3)** — it promised "you will receive a `tool_result` block" and "retry with corrected arguments", neither of which happens in the one-shot flow. Rewritten: at most one tool call per turn, no result comes back, no retry.
- **Tool executor retried deterministic failures (P1-4/P2-3)** — `_execute_with_retry` re-ran identical arguments up to 3 times. Tools now execute exactly once; the error envelope notes the call was NOT retried. The dead `tool_max_retries` session knob and its UI widget were removed with it.
- **Tests wiped the real `contexts/` directory (P2-4)** — `test_comprehensive.py`, `test_dryrun_5rounds.py` and `test_openrouter.py` deleted every `session_*.json`/`*.md` from the live runtime dir. They now run entirely under `tmp_path`/temp dirs, as does the user-specific hardcoded path in `test_middleware.py`.
- **Rate-limit default unified at 5s (P2-2)** — docs/config said 60 while the UI and `SessionState` used 5. `config.default_rate_limit` is now the single source (5) consumed by the UI, `create_session`, deserialization defaults and `RateLimiter`.
- **`streamlit-autorefresh` missing from pyproject (P2-1)** — `pip install .` silently produced an app with no live refresh; the ImportError was swallowed. Added to dependencies and the UI now warns once instead of failing silently. The docstring no longer claims a nonexistent `st.fragment` fallback.
- **Audit log grew unbounded and duplicated content (SEC-3)** — `log_tool_call` recorded the full `write_file` content. Long values are now clipped to 300 chars.
- **Status badge priority drift (P3-8)** — the run bar ranked `complete` before `running`, the context panel the reverse. Both now use the shared `ui/status.py` helpers (complete > running > paused > idle, with a loop-liveness check).
- **File-tool sandbox was process-wide (SEC-6)** — the active-context binding is now thread-local, so two Streamlit tabs (two threads) can run sessions without the last setter winning the sandbox.

#### LOW
- **Rate limiter let concurrent waiters pass together (P3-1)** — `_last_call` was set after sleeping. The slot is now reserved before the sleep.
- **`delete_session` left orphan files (P3-3)** — the `.bak.md` backup and `audit_<id>.log` are now removed with the session.
- **Three saves per turn (P3-4)** — `_process_tool_calls`, `run_turn` and `step` each persisted; persistence now happens exactly once per turn in `step()`.
- **`compute_diff` emitted stray blank lines (P3-9)** — `keepends=True` combined with `lineterm=""` produced an empty line after every content line; the diff is clean now.
- **`enabled` had no UI control (P3-12)** — a per-agent checkbox was added to the config panel.
- **Console script ran the UI outside Streamlit (P3-7)** — `ai-arena` now delegates to `streamlit run run.py` (`run:console_main`) instead of calling `render_app()` bare.
- **Export rebuilt on every rerun (P3-11)** — the export body is memoized on the session's change signature, so auto-refresh ticks no longer re-read the context file.
- **Contradictory `initial_prompt` comments (P2-5)** — both now state the truth: the brief is seeded into the context file and never sent to the model as a message.
- **Dead imports removed** — `orchestrator.py` (`datetime`, `config`, `build_tool_result_envelope`, `ToolCallParseError`, `parse_tool_call`), `tool_executor.py` (`time`, `Path`, `has_tool_call`, `ToolError`), `tool_registry.py` (empty `TYPE_CHECKING` block), `rate_limiter.py` (`Optional`), `agent.py` (`field`, `Optional`), `run.py` (`streamlit`), and the unused `ToolExecutorError` class.

### Changed
- `.gitignore` now un-ignores `pyrightconfig.json` (previously swallowed by the global `*.json` rule).
- `pydantic` removed from `requirements.txt` — it is imported nowhere; the README tech-stack claim was removed.
- The file-tool sandbox resolves the project root from `config.project_root` (single source of truth).
- The tool manual's "Tool Result Format" section became "What Happens After Your Tool Call".

### Tests
- New regression tests: advance-after-tool-call (P0), OpenRouter key precedence, sensitive-path read deny (SEC-1), thread-local sandbox (SEC-6), second-session start guard (P1-1), clean `compute_diff`, orphan cleanup on delete (P3-3).
- Updated `test_one_shot_flow.py` for the new turn contract (envelope message returned and advance verified), `test_middleware.py`/`test_quick.py`/`test_comprehensive.py` for the single-attempt executor.
- All tests run hermetically under `tmp_path`; the suite passes (67 passed, 4 live-API tests skipped).

## [Unreleased] - 2026-07-20

### Fixed (15 bugs)

#### HIGH
- **Message serialization data loss** — `Message.to_dict()` was dropping `had_tool_call` and `tool_result` fields. These are now properly serialized and deserialized, so tool-call badges survive session save/load cycles.
- **Tool manual only injected on round 0** — Agents lost tool access from round 1 onward because `inject_tools` was gated on `current_round == 0`. Now injected on every round.
- **Duplicate messages on tool-call turns** — `_process_tool_calls` recorded an envelope message, then `run_turn` appended a duplicate. The orchestrator now records only the envelope message for tool-call turns and returns `None` from `run_turn` to skip the second append.

#### MEDIUM
- **`_save_locks` TOCTOU race** — Two threads creating a lock for the same new session could end up with different locks. Fixed by using `dict.setdefault()`.
- **Provider errors advancing the session** — When an API call failed, `run_turn` returned an error message and `step()` called `advance()`, skipping the failed agent forever. Now returns `None` so the agent is retried on the next loop iteration.
- **`patch_file` with empty `old_text`** — `str.count("")` matches everywhere and `str.replace("")` inserts between every character, destroying the file. Now explicitly rejects empty `old_text`.
- **Auto-refresh blocking the UI** — When `streamlit_autorefresh` was not installed, the fallback `time.sleep(2)` blocked the entire Streamlit event loop, making Pause/Stop buttons unresponsive. The blocking sleep has been removed.
- **"Round N+1 / N" display** — Completed sessions showed `Round 3 / 2` because the counter was not clamped. Now clamped with `min(current_round + 1, max_rounds)`.

#### LOW
- **Audit log hardcoded `attempt=1`** — `_execute_with_retry` now returns the actual success attempt number, and `process_response` passes it to the audit logger.
- **`has_tool_call` vs `parse_tool_call` mismatch** — `has_tool_call` only checked for a `"tool"` key while `parse_tool_call` required both `"tool"` and `"arguments"`. Aligned to require both.
- **`SummarizeContextTool` size undercount** — The `max_length` check did not account for `\n` characters added by `"\n".join()`. Now includes the newline cost.
- **`_stop_event` plain bool → `threading.Event`** — Replaced the unsafe plain bool with a proper `threading.Event` for correct cross-thread signaling.
- **RateLimiter lock held during sleep** — The lock was held for the entire `time.sleep(wait_time)` duration (up to 300s). Now the sleep happens outside the lock.
- **OpenRouter key prefix inconsistency** — Config panel used `"sk-or-v1-"` while the validator accepted any `"sk-or-*"`. Aligned to `"sk-or-"`.
- **Agent message content was raw envelope JSON** — For tool-call turns, the agent message contained the internal protocol envelope. Now only the system envelope message is recorded; no duplicate raw JSON is exposed.

### Removed
- Deleted obsolete plan documents (`plan_file_source_of_truth.md`, `plan_review_fixes.md`, `plan_ui_ux.md`) — all changes from these plans have been implemented.

### Tests
- Updated `test_one_shot_flow.py` for `threading.Event` and the new one-shot flow behavior (tool-call turns return `None`).
- Fixed `test_comprehensive.py` assertion (`"Initial Prompt"` → `"Initial Task"`).
- All 34 tests passing, 4 skipped (live provider tests require API keys).
