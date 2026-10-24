"""Tests for atomic and permission-restricted file writes."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from deckhand.core import atomic_io
from deckhand.core.atomic_io import (
    atomic_write_bytes,
    atomic_write_text,
    write_private_file,
)

POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")


def test_atomic_write_creates_the_file_and_parents(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deeper" / "state.json"

    result = atomic_write_bytes(target, b"hello")

    assert result == target
    assert target.read_bytes() == b"hello"


def test_atomic_write_replaces_existing_content(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")

    atomic_write_bytes(target, b"new")

    assert target.read_bytes() == b"new"


def test_atomic_write_leaves_no_temporary_files(tmp_path: Path) -> None:
    target = tmp_path / "state.json"

    atomic_write_bytes(target, b"one")
    atomic_write_bytes(target, b"two")

    assert sorted(path.name for path in tmp_path.iterdir()) == ["state.json"]


def test_atomic_write_text_uses_utf8(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"

    atomic_write_text(target, "héllo")

    assert target.read_text(encoding="utf-8") == "héllo"


def test_atomic_write_text_honours_custom_encoding(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"

    atomic_write_text(target, "héllo", encoding="utf-16")

    assert target.read_text(encoding="utf-16") == "héllo"


@POSIX_ONLY
def test_atomic_write_restricts_permissions(tmp_path: Path) -> None:
    target = tmp_path / "secret"

    atomic_write_bytes(target, b"token")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_atomic_write_preserves_old_file_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")

    def fail_replace(self: Path, target: str | Path) -> Path:
        raise OSError("rename failed")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="rename failed"):
        atomic_write_bytes(target, b"new")

    assert target.read_bytes() == b"old"
    assert [path for path in tmp_path.iterdir() if path.suffix == ".tmp"] == []


def test_write_private_file_creates_new_file(tmp_path: Path) -> None:
    target = tmp_path / "token"

    result = write_private_file(target, b"secret")

    assert result == target
    assert target.read_bytes() == b"secret"


def test_write_private_file_defaults_to_empty_content(tmp_path: Path) -> None:
    target = tmp_path / "token"

    write_private_file(target)

    assert target.read_bytes() == b""


@POSIX_ONLY
def test_write_private_file_restricts_permissions(tmp_path: Path) -> None:
    target = tmp_path / "token"

    write_private_file(target, b"secret")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_write_private_file_refuses_to_clobber(tmp_path: Path) -> None:
    target = tmp_path / "token"
    target.write_bytes(b"keep")

    with pytest.raises(FileExistsError):
        write_private_file(target, b"replace")

    assert target.read_bytes() == b"keep"


def test_write_private_file_can_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "token"
    target.write_bytes(b"keep")

    write_private_file(target, b"replace", overwrite=True)

    assert target.read_bytes() == b"replace"


def test_write_private_file_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "state" / "tls" / "key.pem"

    write_private_file(target, b"key")

    assert target.read_bytes() == b"key"


def test_write_private_file_removes_partial_file_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "token"

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="fsync failed"):
        write_private_file(target, b"secret")

    assert not target.exists()


def test_write_private_file_keeps_existing_file_after_failed_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "token"
    target.write_bytes(b"keep")

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="fsync failed"):
        write_private_file(target, b"secret", overwrite=True)

    assert target.exists()


def test_fsync_directory_ignores_unopenable_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        raise OSError("cannot open directory")

    monkeypatch.setattr(os, "open", fail_open)

    atomic_io._fsync_directory(tmp_path)


def test_fsync_directory_flushes_and_closes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = tmp_path / "probe"
    probe.write_bytes(b"x")
    real_open = os.open
    opened: list[int] = []

    def fake_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        descriptor = real_open(probe, os.O_RDONLY)
        opened.append(descriptor)
        return descriptor

    monkeypatch.setattr(os, "open", fake_open)

    atomic_io._fsync_directory(tmp_path)

    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])


def test_fsync_directory_swallows_fsync_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = tmp_path / "probe"
    probe.write_bytes(b"x")
    real_open = os.open
    opened: list[int] = []

    def fake_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        descriptor = real_open(probe, os.O_RDONLY)
        opened.append(descriptor)
        return descriptor

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError("fsync unsupported")

    monkeypatch.setattr(os, "open", fake_open)
    monkeypatch.setattr(os, "fsync", fail_fsync)

    atomic_io._fsync_directory(tmp_path)

    with pytest.raises(OSError):
        os.fstat(opened[0])
