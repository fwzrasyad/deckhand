"""Atomic and permission-restricted file writes.

Layer 0 (foundations).

``atomic_write_*`` writes to a temporary file in the destination directory,
flushes and fsyncs it, then renames it over the target. Readers therefore see
either the old file or the new one, never a partial write -- which is what
state files such as ``layout.json`` and ``devices.json`` need.

``write_private_file`` creates a new file with owner-only permissions and
refuses to clobber an existing one unless asked. Use it for secrets such as the
control token and the TLS private key.

Windows limitation: ``os.chmod`` only toggles the read-only flag there, so the
POSIX 0600 guarantee cannot be expressed with the standard library alone. Files
inherit the ACL of their parent directory; secret directories must therefore be
created with an owner-only ACL by the installer or by the platform layer. This
module never widens access: newly created files grant nothing beyond what the
parent directory already grants.
"""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path


def atomic_write_bytes(path: str | Path, data: bytes, *, mode: int = 0o600) -> Path:
    """Atomically replace ``path`` with ``data`` and return the target path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            temporary.chmod(mode)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except BaseException:
        with suppress(OSError):
            temporary.unlink()
        raise

    _fsync_directory(target.parent)
    return target


def atomic_write_text(
    path: str | Path,
    text: str,
    *,
    encoding: str = "utf-8",
    mode: int = 0o600,
) -> Path:
    """Atomically replace ``path`` with encoded ``text``."""
    return atomic_write_bytes(path, text.encode(encoding), mode=mode)


def write_private_file(
    path: str | Path,
    data: bytes = b"",
    *,
    mode: int = 0o600,
    overwrite: bool = False,
) -> Path:
    """Create ``path`` with owner-only permissions and write ``data``.

    Raises :class:`FileExistsError` when the file exists and ``overwrite`` is
    false. Unlike :func:`atomic_write_bytes` this is not an atomic replace:
    use it to create secrets once, or pass ``overwrite=True`` knowing that a
    failed write may leave the file truncated.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()

    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_BINARY", 0)
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    file_descriptor = os.open(target, flags, mode)
    try:
        target.chmod(mode)
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        if not existed:
            with suppress(OSError):
                target.unlink()
        raise

    _fsync_directory(target.parent)
    return target


def _fsync_directory(directory: Path) -> None:
    """Flush a directory entry to disk where the platform supports it."""
    try:
        file_descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        # Windows cannot open directories; the rename is still durable enough.
        return
    try:
        os.fsync(file_descriptor)
    except OSError:
        pass
    finally:
        os.close(file_descriptor)
