# Refactor Plan: File as Single Source of Truth

**Status:** approved (awaiting execution)
**Date:** 2026-07-19

## Goal

Replace the "agent appends a section each turn" pattern with a true
"file as state, agents rewrite" pattern. The file is the only durable
state; each agent reads the current state and writes a better version.
The file grows organically (in **quality**, not in literal sections
chained together).

## Design rules

1. **One context file** per session. Path: `contexts/<session_id>.md`.
2. **`start_session`** seeds the file with the initial task. The file
   is the source of truth — `session.initial_prompt` is metadata only
   (used for UI display), not for the API call.
3. **Each agent turn** = `read_file` → analyze → `write_file` (REPLACE,
   never `append_file`). The whole file is rewritten.
4. **Model input** = `system_prompt` + a single short nudge
   ("Your turn. Read the file at {ctx_path}, then rewrite it.").
   No "Initial task: …" user message — the task lives in the file.
5. **Tool result envelopes** still flow back to the model so the
   `read_file → write_file` loop works.
6. **`session.messages`** stays populated for log/debug, but is never
   sent to the model.
7. **Initial Task** is preserved across rewrites. Every agent's
   rewritten file keeps the `# Shared Context` header and the
   `## Initial Task` section verbatim, then replaces the working area
   below the `---` separator.

## File format (after `start_session`)

```markdown
# Shared Context

## Initial Task
<the user's initial prompt>

---

## Working Draft
<!-- Agents rewrite everything below this line. -->
```

After Agent A (Critic) acts, the file might look like:

```markdown
# Shared Context

## Initial Task
<initial prompt>

---

## Working Draft

### Critical Analysis
- The task asks for X, but the current state lacks Y.
- The proposed approach misses Z.
- ...
```

After Agent B (Optimist) acts:

```markdown
# Shared Context

## Initial Task
<initial prompt>

---

## Working Draft

### Critical Analysis
- The task asks for X, but the current state lacks Y.
- ...

### Constructive Response
- Addressing the critique: ...
- New opportunities: ...
```

The file's working area is replaced wholesale each turn — never
appended to — so there are no duplicate headers or "Round N" drift.

## Changes

### `ai_arena/engine/orchestrator.py`

**`start_session`** — write the seeded file (header + initial task +
working-draft section), not a bare skeleton. Keep `session.initial_prompt`
as a metadata field for the UI but do not depend on it for the API.

**`_build_messages`** — single user message for every turn (tool
envelope aside): "Your turn. Read the file at {ctx_path}, then rewrite
it." Drop the "Initial task: …" branch entirely.

**`_build_system_prompt`** — keep `{ctx_path}` substitution. Drop
`{round}` (no longer meaningful — the file is the state, not a round
counter).

### `sys_prompts/critic.md` (rewrite)

- Runtime context: `{ctx_path}`
- Mandatory workflow: `read_file` → critique → `write_file` with the
  full new file content
- Rule: preserve `# Shared Context` header and `## Initial Task` verbatim
- Rule: use `write_file`, never `append_file`
- Output: the new file content (markdown), not a "section"

### `sys_prompts/optimist.md` (rewrite)

Same structure as critic, framed as the opportunity-builder. Reads
the critic's version, then rewrites with constructive additions.

### `sys_prompts/synthesizer.md` (rewrite)

Same structure. Produces the final synthesis file. The file's working
area after the synthesizer's turn is the session's final output.

### `sys_prompts/summarizer.md` (rewrite)

Same structure. Produces a condensed file. Can be invoked at any point
to collapse the working area into a shorter form.

## Smoke tests (`tests/test_file_sot_refactor.py`)

1. `start_session` writes a file containing `## Initial Task` and the
   initial prompt.
2. `_build_messages` for round 0 has no "Initial task:" branch — every
   turn gets the same short nudge.
3. `_build_messages` with a `tool_result_envelope` still injects it as
   the user message.
4. `session.initial_prompt` is stored on the session for the UI but is
   not part of any API message.

## Files touched

- `ai_arena/engine/orchestrator.py`
- `sys_prompts/critic.md`
- `sys_prompts/optimist.md`
- `sys_prompts/synthesizer.md`
- `sys_prompts/summarizer.md`
- `tests/test_file_sot_refactor.py` (new)

## Files not touched

- `ai_arena/config.py`
- `ai_arena/models/*`
- `ai_arena/tools/file_tools.py`
- `ai_arena/engine/session.py` (only if a side effect shows up;
  otherwise no)
- `ai_arena/ui/*` (no UI changes needed for this refactor)

## Execution order

1. Save this plan (done).
2. Update `start_session` to seed the file with the initial task.
3. Simplify `_build_messages` (drop "Initial task" branch).
4. Drop `{round}` substitution in `_build_system_prompt` (keep
   `{ctx_path}`).
5. Rewrite the four system prompts.
6. Write & run the smoke tests.
7. Manual end-to-end run via Streamlit.

## Open risks

- Models occasionally ignore the "rewrite, don't append" rule and
  include their own "## Round N" header. If that surfaces during the
  end-to-end run, the prompts need to be tightened (e.g. explicit
  "NEVER include 'Round' or 'Critic —' headers in your output").
- Some providers may not respect a "you MUST call read_file first"
  instruction. If a model skips `read_file` and writes blind, the
  orchestrator could pre-fill the file content into the user message as
  a fallback. Not implementing the fallback preemptively; revisit only
  if the run shows the problem.
