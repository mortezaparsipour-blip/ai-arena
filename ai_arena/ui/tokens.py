"""Design tokens for AI Arena UI.

Single source of truth for colors, used both by:
- Python (e.g. agent badge colors, which are passed as inline styles because
  Streamlit can't inject per-element CSS variables).
- CSS via the :root variables emitted by :func:`css_variables_block`.

To re-theme, edit the ``TOKENS`` dict below and every UI surface picks up
the new values.
"""

from __future__ import annotations


# Flat dict of ``--name: value`` pairs. Add new tokens here; the CSS
# generator picks them up automatically.
TOKENS: dict[str, str] = {
    # Surfaces
    "--bg-base":       "#0f172a",  # body / page
    "--bg-surface":    "#1e293b",  # cards, expanders
    "--bg-elevated":   "#1a2332",  # nested card on a card
    "--bg-error":      "#1a1215",  # error bubble background
    "--bg-warning":    "#1a1a12",  # warning bubble background
    "--bg-tool-card":  "#0f172a",  # tool panel entries

    # Translucent overlays (used for hover, focus rings, etc.)
    "--overlay-1":     "#ffffff0a",
    "--overlay-2":     "#ffffff14",
    "--overlay-3":     "#ffffff1f",
    "--overlay-4":     "#ffffff26",
    "--overlay-5":     "#ffffff55",

    # Borders
    "--border-soft":   "#334155",
    "--border-strong": "#475569",

    # Text
    "--text-primary":  "#f4f1ea",
    "--text-muted":    "#cbd5e1",
    "--text-faint":    "#94a3b8",
    "--text-error":    "#fecaca",
    "--text-warning":  "#fde68a",
    "--text-on-accent": "#ffffff",

    # Accent (hero gradient + buttons)
    "--accent-hero-start": "#1f2a52",
    "--accent-hero-mid":   "#3a2b63",
    "--accent-hero-end":   "#5a2d52",
    "--accent-primary":    "#3a2b63",
    "--accent-secondary":  "#5a2d52",
    "--accent-purple":     "#a78bfa",  # icons, headings
    "--accent-indigo":     "#1e1b4b",  # live indicator chip background

    # Status
    "--status-error":   "#ef4444",
    "--status-warning": "#f59e0b",
    "--status-system":  "#475569",
}


# Agent color palette. Kept as a Python list because Streamlit can only
# receive these via inline ``style="background-color:..."`` (per-message).
# Order matters: it is the deterministic fallback when no agent id is given.
AGENT_PALETTE: list[str] = [
    "#6366f1",  # indigo
    "#10b981",  # emerald
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#8b5cf6",  # violet
    "#ec4899",  # pink
    "#06b6d4",  # cyan
    "#84cc16",  # lime
]


def css_variables_block() -> str:
    """Return a ``<style>`` snippet declaring the tokens as CSS variables.

    Intended to be embedded once at the top of the Streamlit page CSS so the
    rest of the stylesheet can use ``var(--name)`` everywhere.
    """
    lines = [":root {"]
    for name, value in TOKENS.items():
        lines.append(f"  {name}: {value};")
    lines.append("}")
    return "\n".join(lines)
