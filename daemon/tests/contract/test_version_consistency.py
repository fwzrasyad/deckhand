"""Version numbers must agree across the daemon, the package metadata, and the protocol.

A drift between ``pyproject.toml``, :mod:`deckhand.version`, and
``protocol/VERSION`` breaks release notes and the compatibility table in the
README (SRD 13.3).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from deckhand import version


def test_pyproject_version_matches_package_version(daemon_root: Path) -> None:
    metadata = tomllib.loads((daemon_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["version"] == version.__version__


def test_protocol_version_matches_package_constant(repo_root: Path) -> None:
    protocol_version = (repo_root / "protocol" / "VERSION").read_text(encoding="utf-8").strip()

    assert protocol_version == "1"
    assert f"deckhand.v{protocol_version}" == version.PROTOCOL_NAME
