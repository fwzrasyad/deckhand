"""Integration: ``python -m deckhand`` runs in a real subprocess.

Phase 0 only proves the entry point is wired and exits cleanly with every path
redirected into a temporary ``DECKHAND_HOME``. Real server integration tests
start in Phase 1.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_module_entrypoint_reports_version(daemon_root: Path, deckhand_home: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "deckhand", "--version"],
        cwd=daemon_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "deckhand 0.1.0"
    assert deckhand_home.is_dir()


@pytest.mark.integration
def test_module_entrypoint_without_arguments_shows_help(daemon_root: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "deckhand"],
        cwd=daemon_root,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = result.stdout + result.stderr

    assert "Usage" in combined
    assert result.returncode != 0
