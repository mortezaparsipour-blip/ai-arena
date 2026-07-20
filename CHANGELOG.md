# Changelog

All notable changes to this project will be documented in this file.

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
