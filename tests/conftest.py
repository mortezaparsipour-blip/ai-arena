"""Shared pytest fixtures for the AI Arena test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the package importable when tests are run directly via
# ``python tests/test_x.py`` as well as via ``pytest``.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _reset_file_tool_sandbox() -> None:
    """Reset the file-tool sandbox between tests.

    The sandbox's active-context-path is a process-wide global (it has
    to be, so the stateless ``WriteFileTool`` instances can see it).
    Without a reset, a test that binds a context path leaks that binding
    into every later test in the same process, turning isolated tool
    calls into unexpected rejections. This autouse fixture clears the
    binding before each test runs.
    """
    from ai_arena.tools.file_tools import set_active_context_path

    set_active_context_path(None)
    yield
    set_active_context_path(None)
