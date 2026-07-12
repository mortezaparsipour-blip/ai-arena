# AI Arena — UI/UX Review & Improvement Plan

> Generated from a review of the Streamlit UI (`ai_arena/ui/`) against the
> `ui-ux-pro-max` skill checklist. All file paths and line numbers refer to the
> repository state at the time of review.

## App Summary

**AI Arena** is a multi-AI orchestration platform built with Streamlit. The main
layout is a **3-column** grid (chat | status | context) with a configuration
sidebar. Theme: dark, slate-900 background with a purple gradient hero.

- Entry point: `run.py` → `ai_arena/ui/app.py::render_app()`
- Page config & theme: `app.py:168-173`, `.streamlit/config.toml`
- Inline theme CSS: `app.py:176-252`
- Modules: `app.py`, `config_panel.py`, `chat_panel.py`, `context_panel.py`

---

## What's Already Good

| # | Strength | Location |
|---|---|---|
| 1 | Consistent dark theme via `config.toml` | `.streamlit/config.toml` |
| 2 | Nice gradient hero banner | `app.py:182-188` |
| 3 | Color-coded agent badges | `chat_panel.py:78-85` |
| 4 | Distinct visual treatment for error/warning/tool-call | `app.py:216-227` |
| 5 | Empty states (`st.info`) in all panels | `app.py:302,318,324` |

---

## Critical Bugs (P0 — must fix)

### 1. `hash()` bug — agent color changes on every rerun

`chat_panel.py:84`:

```python
idx = hash(agent_id) % len(colors)
```

Python's `hash()` is **randomized per process** via `PYTHONHASHSEED`. The same
agent gets a different badge color across reruns/servers → visual
inconsistency. Replace with a stable hash (e.g. `hashlib.md5` or a sum of
ordinals).

### 2. Redundant H1 — two titles for the same thing

- Hero banner `<h1>` at `app.py:254-262`
- `st.title(config.app_name)` at `app.py:269`

This renders two H1 elements, hurting SEO/accessibility (multiple h1s).
Remove the `st.title` line.

### 3. Export writes to disk instead of offering a browser download

`app.py:138-163` — `_export_session` writes the file under `contexts/` and shows
a server-side path string. Use `st.download_button` so the user can actually
download the file in their browser.

---

## Important (P1 — high impact on perceived quality)

### 4. No loading feedback while a session runs

`Start` spawns a daemon thread (`app.py:103-108`) but:

- No `st.spinner`
- Chat only updates on `st.rerun`
- The user cannot tell whether work is happening → **appears hung**

Add a visible running indicator (spinner / animated status / live message
streaming).

### 5. Sidebar becomes very dense

All three sidebar expanders default to `expanded=True`
(`config_panel.py:48,74,168`). With 6 agents configured the sidebar gets tall
and intimidating. Options:

- Set `Agents` expander to `expanded=False` by default
- Or use `st.tabs` inside the sidebar to separate Global / Agents / Sessions

### 6. Initial Prompt collapsed, but required for Start

`app.py:275` — `expanded=False`. The user sees `Start` is not disabled, clicks
it with an empty prompt → the session runs with nothing. Either expand the
prompt by default, or validate and show an error before starting.

### 7. Emoji used instead of vector icons

- `page_icon="🤖"` (`app.py:170`)
- Hero `<h1>🤖` (`app.py:257`)
- Badges show only 2 uppercase letters, no icon (`chat_panel.py:38`)

Per `ui-ux-pro-max` rule `no-emoji-icons`: emojis are font-dependent and render
inconsistently across platforms. Prefer SVG icons (e.g. emoji-free favicon +
inline SVG).

### 8. Center column is just raw `st.json`

`app.py:305-316` — a raw JSON dump for status. Better alternatives:

- `st.metric` cards for Round / Agents (visual cards)
- A larger, prominent progress display

---

## Secondary (P2 — polish)

### 9. Hardcoded hex values, no design tokens

`app.py:176-252` — `#1f2a52`, `#3a2b63`, `#5a2d52`, `#4f1ea`, etc. are all
inline. For maintainability and theming, define semantic color tokens (per
`ui-ux-pro-max §6 color-semantic`) instead of raw hex inside components.

### 10. No `prefers-reduced-motion` support

Button hover uses `translateY(-1px)` with `transition: all .12s`
(`app.py:203-204`). Add a `@media (prefers-reduced-motion: reduce)` block that
disables transforms.

### 11. Three equal columns break on mobile

`st.columns([1,1,1])` (`app.py:296`) — on mobile the three columns get cramped
and hard to scan. Consider `[2,1,2]` or a responsive/stacked layout for narrow
viewports.

### 12. No download/copy for the context file

`context_panel` only renders `st.code` (`context_panel.py:47-52`). Copying is
hard. Add an `st.download_button` for the shared context.

### 13. Chat badge readability

`chat_panel.py:38` — `msg.agent_name[:2].upper()` produces tiny 2-letter
badges. At `font-size:0.8em` on a colored background, contrast should be
verified (rule `color-accessible-pairs`, 4.5:1).

### 14. Touch targets too small

Buttons use `min-height: 0` (`app.py:200`). On mobile this is below the 44px
minimum (rule `touch-target-size`). Raise the min-height for touch.

---

## Priority Summary

| Priority | Issue | Fix Difficulty |
|---|---|---|
| P0 | `hash()` bug → use stable hash | Easy |
| P0 | Remove redundant `st.title` | 1 line |
| P0 | Export → `st.download_button` | Medium |
| P1 | Add spinner/feedback during run | Medium |
| P1 | Collapse sidebar expanders by default | Trivial |
| P1 | Expand Initial Prompt or validate | Easy |
| P1 | Replace emoji with SVG icons | Easy |
| P1 | Use `st.metric` for center column | Easy |
| P2 | CSS tokens, reduced-motion, touch targets | Medium |

---

## Conclusion

There is clear room for improvement — especially the P0 bugs (hash, redundant
title, export) which are very simple to fix. The base UI is well-built, but
**four issues stand out**:

1. **`hash()` bug** — color changes on every rerun (most visible to the user)
2. **No loading feedback** — the app appears hung while running
3. **Sidebar density** — gets very crowded
4. **Export UX** — file is saved server-side instead of downloaded

### Recommended first batch (quick wins)

1. Fix `hash()` bug in `chat_panel.py:84`
2. Remove redundant `st.title` at `app.py:269`
3. Switch export to `st.download_button`
4. Collapse the `Agents` expander by default
