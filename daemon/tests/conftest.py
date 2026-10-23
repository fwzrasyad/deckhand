"""Shared fixtures for the daemon test suite.

Everything the daemon touches on disk is redirected into ``tmp_path`` so tests
never read or write the developer's real config, state, or log directories
(SRD 8.1, ``DECKHAND_HOME``).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def daemon_root() -> Path:
    """Absolute path to the ``daemon/`` project directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root(daemon_root: Path) -> Path:
    """Absolute path to the monorepo root."""
    return daemon_root.parent


@pytest.fixture
def deckhand_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point every Deckhand path at an empty temporary directory."""
    home = tmp_path / "deckhand-home"
    home.mkdir()
    monkeypatch.setenv("DECKHAND_HOME", str(home))
    return home
