"""Lucide-style SVG icon library for AI Arena UI.

Each icon is a 24x24 stroked SVG snippet (no fill, currentColor stroke) so
it can be embedded directly in markdown/HTML and inherit theme colors.
Names follow Lucide's naming where possible.

Usage:
    from .icons import ICONS
    st.markdown(f"<span class='icon'>{ICONS['bot']}</span>", unsafe_allow_html=True)
"""

from __future__ import annotations

# Common SVG attributes for every icon in this module. Keeping them in a
# constant avoids repeating width/height/fill on every snippet.
_BASE_ATTRS = (
    'xmlns="http://www.w3.org/2000/svg" width="20" height="20" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
)


def _wrap(body: str) -> str:
    return f"<svg {_BASE_ATTRS}>{body}</svg>"


# Each entry is the inner SVG markup (children only). ``_wrap`` adds the
# root <svg> element. If you need a one-off size, just inline the full SVG.
ICONS: dict[str, str] = {
    "bot": _wrap(
        '<path d="M12 8V4H8"/>'
        '<rect width="16" height="12" x="4" y="8" rx="2"/>'
        '<path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>'
    ),
    "play": _wrap('<polygon points="6 3 20 12 6 21 6 3"/>'),
    "pause": _wrap('<rect width="4" height="16" x="6" y="4"/><rect width="4" height="16" x="14" y="4"/>'),
    "stop": _wrap('<rect width="16" height="16" x="4" y="4" rx="1"/>'),
    "download": _wrap(
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>'
    ),
    "settings": _wrap(
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "users": _wrap(
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "sliders": _wrap(
        '<line x1="4" x2="4" y1="21" y2="14"/>'
        '<line x1="4" x2="4" y1="10" y2="3"/>'
        '<line x1="12" x2="12" y1="21" y2="12"/>'
        '<line x1="12" x2="12" y1="8" y2="3"/>'
        '<line x1="20" x2="20" y1="21" y2="16"/>'
        '<line x1="20" x2="20" y1="12" y2="3"/>'
        '<line x1="1" x2="7" y1="14" y2="14"/>'
        '<line x1="9" x2="15" y1="8" y2="8"/>'
        '<line x1="17" x2="23" y1="16" y2="16"/>'
    ),
    "network": _wrap(
        '<rect x="16" y="16" width="6" height="6" rx="1"/>'
        '<rect x="2" y="16" width="6" height="6" rx="1"/>'
        '<rect x="9" y="2" width="6" height="6" rx="1"/>'
        '<path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/>'
        '<path d="M12 12V8"/>'
    ),
    "message": _wrap(
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    ),
    "zap": _wrap('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'),
    "file_text": _wrap(
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" x2="8" y1="13" y2="13"/>'
        '<line x1="16" x2="8" y1="17" y2="17"/>'
        '<line x1="10" x2="8" y1="9" y2="9"/>'
    ),
    "terminal": _wrap(
        '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>'
    ),
    "alert": _wrap(
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" x2="12" y1="8" y2="12"/>'
        '<line x1="12" x2="12.01" y1="16" y2="16"/>'
    ),
    "check": _wrap('<polyline points="20 6 9 17 4 12"/>'),
    "x": _wrap('<line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/>'),
    "sparkles": _wrap(
        '<path d="M12 3l1.9 5.8L20 11l-6.1 1.9L12 19l-1.9-6.1L4 11l6.1-2.2L12 3z"/>'
        '<path d="M5 3v4M3 5h4M19 17v4M17 19h4"/>'
    ),
    "cpu": _wrap(
        '<rect x="4" y="4" width="16" height="16" rx="2"/>'
        '<rect x="9" y="9" width="6" height="6"/>'
        '<path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>'
    ),
    "info": _wrap(
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" x2="12" y1="16" y2="12"/>'
        '<line x1="12" x2="12.01" y1="8" y2="8"/>'
    ),
    "wrench": _wrap(
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "arrow_right": _wrap(
        '<line x1="5" x2="19" y1="12" y2="12"/>'
        '<polyline points="12 5 19 12 12 19"/>'
    ),
    "refresh": _wrap(
        '<polyline points="23 4 23 10 17 10"/>'
        '<polyline points="1 20 1 14 7 14"/>'
        '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'
    ),
    "trash": _wrap(
        '<polyline points="3 6 5 6 21 6"/>'
        '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
        '<path d="M10 11v6M14 11v6"/>'
        '<path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
    ),
}


def icon(name: str, size: int = 18) -> str:
    """Return a sized SVG string for the named icon.

    Args:
        name: Key in :data:`ICONS`.
        size: Pixel size for both width and height.

    Returns:
        SVG markup, or an empty string if the icon is unknown.
    """
    raw = ICONS.get(name, "")
    if not raw:
        return ""
    return raw.replace('width="20" height="20"', f'width="{size}" height="{size}"', 1)
