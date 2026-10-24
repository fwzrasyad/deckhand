"""Tests for the shared pieces of the platform interface (SEC-014)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from deckhand.platform.base import (
    SECRET_FILE_MODE,
    SecretFilePermissions,
    check_posix_secret_permissions,
)

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits required")


def test_secret_file_mode_constant() -> None:
    assert SECRET_FILE_MODE == 0o600


def test_secret_file_permissions_carries_its_fields(tmp_path: Path) -> None:
    result = SecretFilePermissions(path=tmp_path, enforced=True, ok=False, detail="because")

    assert result.path == tmp_path
    assert result.enforced is True
    assert result.ok is False
    assert result.detail == "because"


@posix_only
@pytest.mark.posix
def test_owner_only_file_passes(tmp_path: Path) -> None:
    secret = tmp_path / "control.token"
    secret.write_text("secret", encoding="utf-8")
    secret.chmod(0o600)

    result = check_posix_secret_permissions(secret)

    assert result.enforced is True
    assert result.ok is True
    assert "0600" not in result.detail
    assert "no group or other access" in result.detail


@posix_only
@pytest.mark.posix
def test_stricter_mode_passes(tmp_path: Path) -> None:
    secret = tmp_path / "key.pem"
    secret.write_text("secret", encoding="utf-8")
    secret.chmod(0o400)

    result = check_posix_secret_permissions(secret)

    assert result.ok is True


@posix_only
@pytest.mark.posix
@pytest.mark.parametrize("mode", [0o644, 0o640, 0o604, 0o660])
def test_group_or_other_access_fails(tmp_path: Path, mode: int) -> None:
    secret = tmp_path / "devices.json"
    secret.write_text("secret", encoding="utf-8")
    secret.chmod(mode)

    result = check_posix_secret_permissions(secret)

    assert result.enforced is True
    assert result.ok is False
    assert "expected 0600" in result.detail
    assert f"{mode:04o}" in result.detail


@posix_only
@pytest.mark.posix
def test_missing_file_fails_instead_of_passing(tmp_path: Path) -> None:
    missing = tmp_path / "absent.token"

    result = check_posix_secret_permissions(missing)

    assert result.enforced is True
    assert result.ok is False
    assert "cannot stat" in result.detail
    assert result.path == missing
