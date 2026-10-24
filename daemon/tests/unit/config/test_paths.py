"""Tests for directory resolution and the ``DECKHAND_HOME`` override (SRD 8.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from deckhand.config import paths
from deckhand.config.defaults import CONFIG_FILENAME
from deckhand.platform import current_platform


def test_override_replaces_every_directory(deckhand_home: Path) -> None:
    assert paths.home_override() == deckhand_home
    assert paths.config_dir() == deckhand_home / "config"
    assert paths.state_dir() == deckhand_home / "state"
    assert paths.log_dir() == deckhand_home / "logs"


def test_config_file_lives_in_the_config_directory(deckhand_home: Path) -> None:
    assert paths.config_file() == deckhand_home / "config" / CONFIG_FILENAME


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_override_counts_as_unset(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("DECKHAND_HOME", value)

    assert paths.home_override() is None


def test_unset_override_falls_back_to_the_platform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DECKHAND_HOME", raising=False)
    platform = current_platform()

    assert paths.config_dir() == platform.config_dir()
    assert paths.state_dir() == platform.state_dir()
    assert paths.log_dir() == platform.log_dir()
    assert paths.config_file() == platform.config_dir() / CONFIG_FILENAME


def test_override_expands_a_leading_tilde(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DECKHAND_HOME", "~/deckhand-test-home")

    assert paths.home_override() == Path.home() / "deckhand-test-home"
