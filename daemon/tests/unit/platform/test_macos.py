"""macOS-only tests for :mod:`deckhand.platform.macos`.

Like Windows, ``platformdirs`` uses fixed home-relative folders on macOS, so the
module-level functions are patched rather than the environment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from deckhand.platform import macos
from deckhand.platform.macos import MacOSPlatform

pytestmark = [
    pytest.mark.posix,
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS only"),
]


def test_config_dir_is_in_application_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(macos, "user_config_dir", lambda *args, **kwargs: str(tmp_path / "support"))

    assert MacOSPlatform().config_dir() == tmp_path / "support"


def test_state_dir_is_a_state_subdirectory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(macos, "user_data_dir", lambda *args, **kwargs: str(tmp_path / "support"))

    assert MacOSPlatform().state_dir() == tmp_path / "support" / "state"


def test_log_dir_is_under_library_logs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(macos, "user_log_dir", lambda *args, **kwargs: str(tmp_path / "logs"))

    assert MacOSPlatform().log_dir() == tmp_path / "logs"


def test_process_group_kwargs_start_a_new_session() -> None:
    assert MacOSPlatform().process_group_kwargs() == {"start_new_session": True}


def test_secret_permissions_are_enforced(tmp_path: Path) -> None:
    secret = tmp_path / "key.pem"
    secret.write_text("secret", encoding="utf-8")
    secret.chmod(0o600)

    result = MacOSPlatform().check_secret_file_permissions(secret)

    assert result.enforced is True
    assert result.ok is True
