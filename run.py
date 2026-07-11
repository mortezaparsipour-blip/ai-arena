#!/usr/bin/env python3
"""AI Arena - Entry point for the Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

import streamlit as st

from ai_arena.ui.app import render_app


def main() -> None:
    """Launch the AI Arena Streamlit application."""
    render_app()


if __name__ == "__main__":
    main()
