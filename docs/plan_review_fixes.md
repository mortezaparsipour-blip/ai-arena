# AI Arena — Review & Fix Plan (2026-07-15)

> Follow-up to `plan_ui_ux.md`. Several items in that doc were marked "Done"
> but were not actually implemented. This plan covers both the un-fixed items
> and additional bugs found during a fresh code review.

## P0 — Critical Bugs (must fix)

### P0-1. SessionManager never reloads from disk
**File:** `ai_arena/engine/session.py:14-23`
**Symptom:** Sessions appear, then vanish on the next Streamlit rerun
because `_sessions` is an in-memory dict that nothing repopulates after a rerun.
**Fix:** Add `_load_from_disk` and call it from `__init__`.

### P0-2. Tool parser regex rejects nested JSON
**File:** `ai_arena/engine/tool_parser.py:78,99`
**Symptom:** Tool calls with nested `arguments` (i.e. every real call) silently
fail to parse because `\{[^{}]*"tool"[^{}]*\}` cannot match braces inside.
**Fix:** Use `json.JSONDecoder.raw_decode` to scan the response for the next
top-level JSON object, instead of regex.

### P0-3. Background thread writes to st.session_state (race)
**File:** `ai_arena/ui/app.py:72-82, 92-97, 110-119`
**Symptom:** `_run_loop` mutates `st.session_state["orchestrator_running"]`
and `["last_error"]` from a non-main thread. Streamlit session state is not
thread-safe; this can corrupt UI state under load.
**Fix:** Move running/error state onto a thread-safe `Orchestrator` attribute
and read it from the main thread via `st.rerun` polling. Wrap any unavoidable
session_state writes with a `threading.Lock`.

### P0-4. `start_session` resets RateLimiter state
**File:** `ai_arena/engine/orchestrator.py:281`
**Symptom:** Each start/resume rebuilds the rate limiter and forgets
`_last_call`, so the first call goes out with zero delay. Burst protection is lost.
**Fix:** Mutate `delay_seconds` on the existing limiter and call `reset()` only
when user explicitly opts in (or just leave the existing time-since-last-call intact).

## P1 — Important Bugs

### P1-5. Audit log silently swallows IO errors
**File:** `ai_arena/engine/tool_executor.py:90-91`
**Symptom:** `except Exception: pass` hides every logging error.
**Fix:** Log to `stderr` at least, and re-raise only if it is not a permission/IO problem.

### P1-6. `_save_session` not atomic; two writers can corrupt the JSON
**Files:** `ai_arena/engine/session.py:114-138`, `orchestrator.py:run_turn, step`
**Fix:** Write to `*.json.tmp` and `os.replace` (atomic on POSIX and Windows).
Add a `threading.Lock` per session_id.

## P2 / UI-UX — Polish (mostly "claimed but not done" in plan_ui_ux.md)

### UI-11. `ai_arena/ui/icons.py` was planned but never created
Build the file with 30+ Lucide SVG icons rendered as raw `<svg>` markup
(consistent with the existing inline-style rendering in this app).

### UI-12. Emojis still in app.py
- `app.py:184`: `page_icon="🤖"` → use a Bot SVG
- `app.py:254`: `<h1>🤖 AI Arena...</h1>` → inline Bot SVG

### UI-13. `.chat-bubble` CSS classes are defined but never used
**File:** `ai_arena/ui/chat_panel.py:78-95`
**Fix:** Wrap each message in `<div class="chat-bubble [variant]">` and use the
CSS already declared in `app.py:216-227`.

### UI-14. Sidebar has no visual hierarchy
**File:** `ai_arena/ui/config_panel.py`
**Fix:** Add icon + header color per expander.

### UI-15. "No active session" repeated in 3 columns
**Fix:** Replace the three identical empty states with a single onboarding card.

### UI-16. Progress bar lives in the right column
**Fix:** Move the round progress + active agent indicator into the center
metrics column where users expect to look.

### UI-17. Tools not visible to the user
**Fix:** Add a "Available Tools" expander in the sidebar that shows each
tool's name, description, and a one-line example.

### UI-18. No auto-refresh during long sessions
**Fix:** When session is running, schedule a `st.rerun` via
`st_autorefresh` or a polling loop every 2s.

## Out of scope (acknowledged but deferred)

- Design tokens / `var(--color-*)` extraction
- File-level locking beyond per-session lock
- `tool_max_retries` UI control
- `max_tokens` UI override
- Stale docstring in `models/agent.py:24`
