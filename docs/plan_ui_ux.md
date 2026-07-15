# AI Arena — UI/UX Review & Improvement Plan

> Generated from a review of the Streamlit UI (`ai_arena/ui/`) against the
> `ui-ux-pro-max` skill checklist. All file paths and line numbers refer to the
> repository state at the time of review.
>
> **Audit performed 2026-07-15** against the live codebase. Original
> review listed 50+ icons; actual count is 25. A few claims in the
> "done" column were partially fixed or replaced with a different
> solution. See **Verification Notes** at the end of each section.
>
> **All five newly-discovered issues (N1–N5) were fixed in the same
> audit pass.** See "New Issues" → "Resolution" at the bottom.

## App Summary

**AI Arena** is a multi-AI orchestration platform built with Streamlit. The main
layout is a **3-column** grid (chat | status | context) with a configuration
sidebar. Theme: dark, slate-900 background with a purple gradient hero.

- Entry point: `run.py` → `ai_arena/ui/app.py::render_app()`
- Page config & theme: `app.py:241-247`, `.streamlit/config.toml`
- Inline theme CSS: `app.py:248-376`
- Modules: `app.py`, `config_panel.py`, `chat_panel.py`, `context_panel.py`
- **New:** `icons.py` — 25 Lucide SVG icons
- **New:** `tokens.py` — design tokens (single source of truth for colors)

---

## What's Already Good

| # | Strength | Location |
|---|---|---|
| 1 | Consistent dark theme via `config.toml` | `.streamlit/config.toml` |
| 2 | Nice gradient hero banner | `app.py:380-389` |
| 3 | Color-coded agent badges (stable) | `chat_panel.py:31-34` |
| 4 | Distinct visual treatment for error/warning/tool-call | `app.py:308-314` |
| 5 | Empty-state card in all panels (one design, reused) | `app.py:201-214` |

---

## Critical Bugs (P0 — must fix) ✅ **ALL FIXED**

### 1. `hash()` bug — agent color changes on every rerun ✅ **FIXED**

**Before** (`chat_panel.py:84`):
```python
idx = hash(agent_id) % len(colors)
```

**After** — Stable MD5 hash (`chat_panel.py:32`):
```python
idx = int(hashlib.md5(agent_id.encode()).hexdigest(), 16) % len(_AGENT_COLORS)
```

Python's `hash()` is randomized per process via `PYTHONHASHSEED`. Fixed with stable MD5.

### 2. Redundant H1 — two titles for the same thing ✅ **FIXED**

- Hero banner `<h1>` at `app.py:380-389`
- `st.title(config.app_name)` — **REMOVED**

### 3. Export writes to disk instead of offering a browser download ✅ **FIXED**

`app.py:167-176` — Now uses `st.download_button` with generated markdown content.

---

## Important (P1 — high impact on perceived quality)

### 4. No loading feedback while a session runs ⚠️ **PARTIAL**

**Planned:** add `st.spinner` during session run + validation before start.
**Actual implementation** (`app.py:430-433`, `app.py:100-108`):

- Validation on Start: blank prompt → `st.error(...)` + `st.stop()` ✓
- Loading feedback: instead of `st.spinner`, a **"Live:" indicator**
  (`app.py:425-432`) shows which agent is currently working.
- Auto-refresh every 2s via `streamlit_autorefresh` (with JS-reload fallback).

**Why this is fine:** the spinner would only show during the synchronous
launch, not the long async loop. The Live indicator + auto-refresh gives
better feedback over the whole run. Functionally equivalent, visually nicer.

**Caveat (new problem):** `streamlit_autorefresh` is imported at
`app.py:227` but is **not declared in `requirements.txt`**. The JS fallback
works, so this is not a runtime error — but a fresh install won't pick it up.
Tracked in **New Issues** below.

### 5. Sidebar becomes very dense ⚠️ **PARTIALLY FIXED (intentional)**

Plan: all three sidebar expanders default to `expanded=False`.
**Actual:**

| Section | `expanded` | Line | Why |
|---|---|---|---|
| Global Settings | **`True`** | `config_panel.py:78` | Entry point — must be visible before "Create Session" |
| Agents | `False` | `config_panel.py:117` | Second-visit choice |
| Sessions | `False` | `config_panel.py:230` | Second-visit choice |

**Decision:** keep `Global Settings` open. The settings are the entry
point to creating a session (rounds, rate limit, dry-run, tool retries
must all be visible) — hiding them would force an extra click on every
session. The other two expanders do follow the plan.

**Sidebar scroll containment** is added in N5 below so the open
expander doesn't push the Start button off-screen.

### 6. Initial Prompt collapsed, but required for Start ✅ **FIXED**

- Prompt expander is `expanded=True` at `app.py:405`
- Start button validates prompt is not empty (`app.py:103-106`),
  shows `st.error` and `st.stop()` if blank.

### 7. Emoji used instead of vector icons ✅ **FIXED (count adjusted)**

- `page_icon="🤖"` in `st.set_page_config` → replaced with `.streamlit/favicon.svg`
  (still falls back to `"🛰"` if the file is missing — see **New Issues**).
- Hero `<h1>🤖 ...` → Replaced with Lucide **BOT** SVG icon (`app.py:386`)
- Badges: added **ZAP** icon for tool-call summary (`chat_panel.py:154`)
- Sidebar: every section header has an icon (`config_panel.py:40-44`)

`ai_arena/ui/icons.py` contains **25 Lucide SVG icons** (not 50+ as
originally stated): `bot, play, pause, stop, download, settings, users,
sliders, network, message, zap, file_text, terminal, alert, check, x,
sparkles, cpu, info, wrench, arrow_right, refresh, trash`. Enough for
the current surface, room to grow.

### 8. Center column is just raw `st.json` ✅ **FIXED**

Replaced with `st.metric` cards + progress bar (`app.py:188-196`):

- Session name
- Round (current/max)
- Status (Running/Paused/Idle/Complete)
- Dry Run (Yes/No)
- Agent count
- Progress bar
- "Active agent" indicator when running

---

## Secondary (P2 — polish)

### 9. Hardcoded hex values, no design tokens ✅ **FIXED (better than planned)**

`ai_arena/ui/tokens.py` is now the **single source of truth** for every
color in the app:

- `TOKENS` dict (surfaces, overlays, borders, text, accent, status)
- `AGENT_PALETTE` list (8 colors used by both `chat_panel.py` and
  `config_panel.py` so the sidebar preview and the chat badge share the
  same colors)
- `css_variables_block()` emits a `:root { --token: value; ... }` block
  that `app.py` injects once at the top of the page.

This is an upgrade over the original "addressed" plan. The only place
hex values still appear in Python source is `tokens.py` itself, which is
intentional — it's the single point to edit when re-theming.

### 10. No `prefers-reduced-motion` support ✅ **FIXED**

`app.py:371-376` — added `@media (prefers-reduced-motion: reduce)` block
disabling transforms/transitions on buttons.

### 11. Three equal columns break on mobile ✅ **IMPROVED**

`app.py:447` — `st.columns([1,1,1], gap="medium")`. Streamlit still
stacks the columns at narrow widths; the gap only helps at tablet+ sizes.

### 12. No download/copy for the context file ✅ **FIXED**

`context_panel.py:51-58` — added `st.download_button` for shared context file.

### 13. Chat badge readability ✅ **FIXED**

`chat_panel.py:50-57`:

- font-size: `0.85em`
- font-weight: `600`
- padding: `6px 10px`
- min-width: `36px`
- flexbox centering via parent columns

### 14. Touch targets too small ✅ **FIXED**

`app.py:276` — buttons: `min-height: 44px` (WCAG-recommended minimum).

---

## Priority Summary

| Priority | Issue | Status |
|---|---|---|
| P0 | `hash()` bug → use stable hash | ✅ Done |
| P0 | Remove redundant `st.title` | ✅ Done |
| P0 | Export → `st.download_button` | ✅ Done |
| P1 | Add spinner/feedback during run | ✅ Done (Live indicator instead of spinner) |
| P1 | Collapse sidebar expanders by default | ⚠️ Partial (intentional — Global Settings kept open) |
| P1 | Expand Initial Prompt or validate | ✅ Done |
| P1 | Replace emoji with SVG icons | ✅ Done (25 icons, not 50+) |
| P1 | Use `st.metric` for center column | ✅ Done |
| P2 | CSS tokens, reduced-motion, touch targets | ✅ Done (tokens became full system) |
| P2 | Download button for context file | ✅ Done |
| P2 | Chat badge readability/contrast | ✅ Done |
| P2 | Responsive columns for mobile | ✅ Improved |
| N1 | Add `streamlit-autorefresh` to requirements | ✅ Fixed (2026-07-15) |
| N2 | Remove emoji fallback in `page_icon` | ✅ Fixed (2026-07-15) |
| N3 | Global Settings expander decision | ✅ Resolved (kept open by design) |
| N4 | `msg_color_for` ordering + dead code | ✅ Fixed (2026-07-15) |
| N5 | Sidebar scroll containment | ✅ Fixed (2026-07-15) |

---

## New Issues Discovered During Audit

These were **not in the original plan** but came up while verifying the
"done" items.

### N1. `streamlit-autorefresh` not in `requirements.txt` ✅ **FIXED**
**File:** `app.py:227` (import), `requirements.txt` (was missing).
**Fix applied:** added `streamlit-autorefresh>=1.0.0` to
`requirements.txt` with a comment pointing at the consumer. Fresh
installs now get the smoother auto-refresh path.

### N2. `page_icon` still has an emoji fallback ✅ **FIXED**
**File:** was `app.py:242`:
```python
page_icon=str(_FAVICON) if _FAVICON.exists() else "🛰",
```
**Fix applied:** removed the on-disk dependency. The favicon is now an
inline SVG serialized as a `data:` URI (`_FAVICON_DATA_URI` constant at
`app.py:38-54`) and passed directly to `st.set_page_config`. The emoji
fallback is gone. No behavior change for users on a normal install, but
the page icon can no longer be lost if the file is deleted.

### N3. `Global Settings` expander state contradicts the plan ✅ **RESOLVED (kept as-is)**
**Decision:** keep `expanded=True` at `config_panel.py:78`.
**Rationale:** Global Settings is the entry point to creating a
session — the user has to set rounds, dry-run, and rate limit before
hitting "Create Session". Hiding it forces an extra click on every
session. Agents and Sessions are still `expanded=False` because they
are second-visit choices.
**Plan updated:** §5 is now marked ⚠️ as a deliberate divergence.

### N4. `msg_color_for` ordering + dead-code branch in `_bubble_badge` ✅ **FIXED**
**File:** `chat_panel.py` (helpers in the 50–70 range).
**Issues found beyond the ordering one:**
- `msg_color_for` was defined *after* `_bubble_badge` (late binding
  masked the smell).
- `_bubble_badge` had `if msg_color_for(...) is None:` — but
  `msg_color_for` never returns `None`, so the `is None` branch was
  dead code and the function called the helper twice.
**Fix applied:** moved `msg_color_for` above `_bubble_badge`,
collapsed the badge to a single call, expanded the docstring on
`msg_color_for` to document that the variant always wins over the
agent color.

### N5. Sidebar config panel has no scroll containment ✅ **FIXED**
**File:** `app.py:386-402` (CSS).
**Fix applied:** added a CSS rule on
`[data-testid="stSidebar"] > div:first-child` that caps the sidebar
height to `calc(100vh - 60px)` and turns on internal vertical scroll.
Thin scrollbar styled to match the theme (`--overlay-4`).
The initial prompt and Start button stay anchored in the main column
regardless of how tall the sidebar gets.

---

## Files Modified (this plan)

- `ai_arena/ui/app.py` — Hero, metrics, spinner/deviation, CSS, exports, autorefresh
- `ai_arena/ui/chat_panel.py` — Stable hash, icon badges, bubble variants
- `ai_arena/ui/config_panel.py` — Collapsed expanders, sidebar icons, Tools panel
- `ai_arena/ui/context_panel.py` — Context download button
- `ai_arena/ui/icons.py` (new) — 25 Lucide SVG icons
- `ai_arena/ui/tokens.py` (new) — Design tokens (CSS variables + palette)
- `.streamlit/favicon.svg` (new) — Replaces `🤖` page icon

## Out of Scope (acknowledged)

- File-level locking beyond per-session lock
- `tool_max_retries` UI control (already exists, just not in the
  original P0/P1 list — was added in `plan_review_fixes.md`)
- `max_tokens` UI override (already exists, see `config_panel.py:154-165`)
- Stale docstring in `models/agent.py:24`
