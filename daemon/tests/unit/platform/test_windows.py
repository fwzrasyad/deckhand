"""Windows-only tests for :mod:`deckhand.platform.windows`.

``platformdirs`` resolves Windows folders through the shell API, so the
``APPDATA`` environment variable cannot redirect it. These tests therefore patch
the ``platformdirs`` functions the module imported and assert that the module
forwards the right arguments; nothing is written to the real user profile.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from deckhand.platform import windows
from deckhand.platform.windows import CREATE_NEW_PROCESS_GROUP, WindowsPlatform

pytestmark = [
    pytest.mark.windows,
    pytest.mark.skipif(sys.platform != "win32", reason="Windows only"),
]


def test_config_dir_uses_roaming_appdata_without_appauthor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[str, bool | None, bool]] = []

    def fake(name: str, *, appauthor: bool | None = None, roaming: bool = False) -> str:
        calls.append((name, appauthor, roaming))
        return str(tmp_path / "roaming")

    monkeypatch.setattr(windows, "user_config_dir", fake)

    assert WindowsPlatform().config_dir() == tmp_path / "roaming"
    assert calls == [("Deckhand", False, True)]


def test_state_dir_uses_local_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, bool | None]] = []

    def fake(name: str, *, appauthor: bool | None = None) -> str:
        calls.append((name, appauthor))
        return str(tmp_path / "local")

    monkeypatch.setattr(windows, "user_data_dir", fake)

    assert WindowsPlatform().state_dir() == tmp_path / "local"
    assert calls == [("Deckhand", False)]


def test_log_dir_is_below_local_appdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(windows, "user_log_dir", lambda *args, **kwargs: str(tmp_path / "logs"))

    assert WindowsPlatform().log_dir() == tmp_path / "logs"


def test_process_group_kwargs_use_create_new_process_group() -> None:
    assert WindowsPlatform().process_group_kwargs() == {"creationflags": CREATE_NEW_PROCESS_GROUP}


def test_is_elevated_reads_the_admin_flag() -> None:
    assert isinstance(WindowsPlatform().is_elevated(), bool)


def test_secret_permissions_are_reported_as_not_enforced(tmp_path: Path) -> None:
    secret = tmp_path / "key.pem"
    secret.write_text("secret", encoding="utf-8")

    result = WindowsPlatform().check_secret_file_permissions(secret)

    assert result.enforced is False
    assert result.ok is True
    assert result.path == secret
    assert "ACL" in result.detail
    assert "not implemented" in result.detail
