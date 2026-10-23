"""End-to-end: the installed ``deckhand`` console script works.

This is the only test that exercises the packaged entry point exactly as a user
would invoke it (``deckhand --version``). A full scripted session against a real
daemon arrives in Phase 1.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _console_script() -> Path:
    name = "deckhand.exe" if sys.platform == "win32" else "deckhand"
    return Path(sys.executable).parent / name


@pytest.mark.integration
def test_console_script_is_installed() -> None:
    script = _console_script()

    assert script.is_file(), f"{script} missing; run `uv sync`"


@pytest.mark.integration
def test_console_script_reports_version() -> None:
    result = subprocess.run(
        [str(_console_script()), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "deckhand 0.1.0"
