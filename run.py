#!/usr/bin/env python3
"""AI Arena - entry points for the Streamlit application.

``main`` runs the app inside an already-running Streamlit runtime — this is
what ``streamlit run run.py`` executes.

``console_main`` is the ``ai-arena`` console script: it hands off to
``streamlit run`` so the app always runs in a proper Streamlit runtime.
Calling ``render_app()`` from a bare interpreter (the old console-script
behavior) raises ScriptRunContext warnings and breaks every ``st.*`` call.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from ai_arena.ui.app import render_app


def main() -> None:
    """Launch the AI Arena Streamlit application (inside `streamlit run`)."""
    render_app()


def console_main() -> None:
    """Console-script entry point: delegate to `streamlit run run.py`."""
    script = str(Path(__file__).resolve())
    raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", script]))


if __name__ == "__main__":
    main()
