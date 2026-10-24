"""The platform interface: directories, elevation, secret permissions, process groups.

Layer 0 (foundations). Every OS-specific fact the daemon needs is reached through
one interface; the implementations live in :mod:`deckhand.platform.windows`,
:mod:`deckhand.platform.linux`, and :mod:`deckhand.platform.macos` so that no
OS-specific code leaks into other packages (NFR-011).

The directories returned here are the native OS directories. The *effective*
directories -- including the ``DECKHAND_HOME`` override used by tests -- are
resolved in :mod:`deckhand.config.paths`.
"""

from __future__ import annotations

import stat
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

SECRET_FILE_MODE = 0o600
"""Mode required for secret files on POSIX (SEC-014)."""


@dataclass(frozen=True, slots=True)
class SecretFilePermissions:
    """Outcome of a secret-file permission check (SEC-014).

    ``enforced`` reports whether the platform verified the guarantee at all. On
    Windows ``enforced`` is ``False`` and ``ok`` is ``True``: ACL verification is
    not implemented, so callers must not treat this result as proof that the file
    is private. ``detail`` always explains what was (or was not) checked.
    """

    path: Path
    enforced: bool
    ok: bool
    detail: str


class Platform(ABC):
    """The OS facts the daemon depends on.

    Implementations are stateless; constructing one has no side effects. Use
    :func:`deckhand.platform.current_platform` instead of instantiating a
    concrete class directly, unless a test needs to exercise one OS's behaviour.
    """

    name: ClassVar[str]
    """Short OS name, one of ``windows``, ``linux``, ``macos``."""

    @abstractmethod
    def config_dir(self) -> Path:
        """Directory holding user-edited configuration (SRD 8.1)."""

    @abstractmethod
    def state_dir(self) -> Path:
        """Directory holding daemon-written state, including secrets (SRD 8.1)."""

    @abstractmethod
    def log_dir(self) -> Path:
        """Directory holding ``deckhand.log`` and ``audit.log``."""

    @abstractmethod
    def is_elevated(self) -> bool:
        """Whether the process runs as root (POSIX) or Administrator (Windows)."""

    @abstractmethod
    def process_group_kwargs(self) -> dict[str, object]:
        """Keyword arguments that put a ``subprocess.Popen`` child in its own group.

        This is the minimal primitive the :mod:`deckhand.process` package builds
        on: POSIX passes ``start_new_session``, Windows passes
        ``CREATE_NEW_PROCESS_GROUP``. The caller unpacks the mapping into the
        ``Popen`` call.
        """

    @abstractmethod
    def check_secret_file_permissions(self, path: str | Path) -> SecretFilePermissions:
        """Verify that a secret file is private to the current user (SEC-014)."""


def check_posix_secret_permissions(path: str | Path) -> SecretFilePermissions:
    """Shared SEC-014 check for the POSIX implementations.

    A file passes when it grants no group or other access, i.e. its permission
    bits are a subset of ``0600``. Stricter modes such as ``0400`` therefore pass:
    the requirement is that nobody else can read the secret, not that the exact
    ``0600`` literal is used.
    """
    target = Path(path)
    try:
        mode = stat.S_IMODE(target.stat().st_mode)
    except OSError as exc:
        return SecretFilePermissions(
            path=target,
            enforced=True,
            ok=False,
            detail=f"cannot stat secret file: {exc}",
        )

    ok = (mode & 0o077) == 0
    if ok:
        detail = f"mode is {mode:04o}; no group or other access"
    else:
        detail = f"mode is {mode:04o}; expected 0600 (no group or other access)"
    return SecretFilePermissions(path=target, enforced=True, ok=ok, detail=detail)
