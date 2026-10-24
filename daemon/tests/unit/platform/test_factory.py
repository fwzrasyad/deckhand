"""Tests for the platform factory and the module-level convenience functions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from deckhand.platform import (
    UnsupportedOperatingSystemError,
    check_secret_file_permissions,
    current_platform,
    is_elevated,
)
from deckhand.platform.base import Platform, SecretFilePermissions
from deckhand.platform.linux import LinuxPlatform
from deckhand.platform.macos import MacOSPlatform
from deckhand.platform.windows import WindowsPlatform

IMPLEMENTATIONS = [WindowsPlatform, LinuxPlatform, MacOSPlatform]


def test_factory_returns_the_running_os_implementation() -> None:
    expected: type[Platform]
    if sys.platform == "win32":
        expected = WindowsPlatform
    elif sys.platform == "darwin":
        expected = MacOSPlatform
    else:
        expected = LinuxPlatform

    assert type(current_platform()) is expected


def test_factory_returns_a_fresh_instance_each_time() -> None:
    assert current_platform() is not current_platform()


@pytest.mark.parametrize(
    ("os_name", "name"),
    [("win32", "windows"), ("darwin", "macos"), ("linux", "linux"), ("linux2", "linux")],
)
def test_factory_selects_by_os(monkeypatch: pytest.MonkeyPatch, os_name: str, name: str) -> None:
    monkeypatch.setattr(sys, "platform", os_name)

    assert current_platform().name == name


def test_factory_rejects_unknown_os(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "freebsd13")

    with pytest.raises(UnsupportedOperatingSystemError, match="freebsd13"):
        current_platform()


def test_is_elevated_returns_a_bool() -> None:
    assert isinstance(is_elevated(), bool)


@pytest.mark.parametrize("implementation", IMPLEMENTATIONS)
def test_every_implementation_satisfies_the_interface(
    implementation: type[Platform], tmp_path: Path
) -> None:
    platform = implementation()
    secret = tmp_path / f"{platform.name}.token"
    secret.write_text("secret", encoding="utf-8")

    assert platform.name in {"windows", "linux", "macos"}
    for directory in (platform.config_dir(), platform.state_dir(), platform.log_dir()):
        assert isinstance(directory, Path)
        assert directory.is_absolute()
    assert isinstance(platform.is_elevated(), bool)
    assert platform.process_group_kwargs()
    permissions = platform.check_secret_file_permissions(secret)
    assert isinstance(permissions, SecretFilePermissions)
    assert permissions.path == secret
    assert permissions.detail


def test_secret_permission_check_uses_the_running_platform(tmp_path: Path) -> None:
    secret = tmp_path / "control.token"
    secret.write_text("secret", encoding="utf-8")

    result = check_secret_file_permissions(secret)

    assert result == current_platform().check_secret_file_permissions(secret)
