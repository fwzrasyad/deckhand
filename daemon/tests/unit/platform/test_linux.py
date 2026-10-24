"""Linux-only tests for :mod:`deckhand.platform.linux`."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from deckhand.platform.linux import LinuxPlatform

pytestmark = [
    pytest.mark.posix,
    pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux only"),
]


def test_directories_honour_xdg_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    platform = LinuxPlatform()

    assert platform.config_dir() == tmp_path / "xdg-config" / "deckhand"
    assert platform.state_dir() == tmp_path / "xdg-state" / "deckhand"
    assert platform.log_dir() == tmp_path / "xdg-state" / "deckhand" / "log"


def test_process_group_kwargs_start_a_new_session() -> None:
    assert LinuxPlatform().process_group_kwargs() == {"start_new_session": True}


def test_is_elevated_tracks_the_effective_uid() -> None:
    assert LinuxPlatform().is_elevated() is (
        getattr(os, "geteuid")() == 0  # noqa: B009 - POSIX-only, absent from the Windows typeshed
    )


def test_secret_permissions_are_enforced(tmp_path: Path) -> None:
    secret = tmp_path / "control.token"
    secret.write_text("secret", encoding="utf-8")
    secret.chmod(0o600)
    assert LinuxPlatform().check_secret_file_permissions(secret).ok is True

    secret.chmod(0o644)
    result = LinuxPlatform().check_secret_file_permissions(secret)
    assert result.enforced is True
    assert result.ok is False
