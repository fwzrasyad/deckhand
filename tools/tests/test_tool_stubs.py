"""Smoke tests for the Phase 0 tool stubs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]

STUBS = [
    pytest.param(TOOLS_DIR / "mock_daemon" / "main.py", id="mock_daemon"),
    pytest.param(TOOLS_DIR / "loadtest" / "main.py", id="loadtest"),
]


@pytest.mark.parametrize("script", STUBS)
def test_stub_runs_and_exits_zero(script: Path) -> None:
    """Each stub prints its Phase 1 purpose and exits 0."""
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "not implemented yet" in result.stdout
