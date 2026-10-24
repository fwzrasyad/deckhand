"""OS-specific facts behind one interface.

Layer 0 (foundations). OS-specific code is confined to this package, the
:mod:`deckhand.process` package, and :mod:`deckhand.telemetry.providers`
(NFR-011). Everything else imports :func:`current_platform` or the module-level
convenience functions below.

``platformdirs`` is used only in this package; :mod:`deckhand.config.paths` adds
the ``DECKHAND_HOME`` override on top of the native directories.
"""

from __future__ import annotations

import sys
from pathlib import Path

from deckhand.core.errors import DeckhandError
from deckhand.platform.base import Platform, SecretFilePermissions
from deckhand.platform.linux import LinuxPlatform
from deckhand.platform.macos import MacOSPlatform
from deckhand.platform.windows import WindowsPlatform

__all__ = [
    "Platform",
    "SecretFilePermissions",
    "UnsupportedOperatingSystemError",
    "check_secret_file_permissions",
    "current_platform",
    "is_elevated",
]


class UnsupportedOperatingSystemError(DeckhandError):
    """The current OS has no :class:`Platform` implementation."""


def current_platform() -> Platform:
    """Return the implementation for the running OS.

    A fresh, stateless instance is returned on every call, so nothing caches a
    decision taken before a test monkeypatches ``sys.platform``.
    """
    current = str(sys.platform)
    if current == "win32":
        return WindowsPlatform()
    if current == "darwin":
        return MacOSPlatform()
    if current.startswith("linux"):
        return LinuxPlatform()
    raise UnsupportedOperatingSystemError(f"unsupported operating system: {current}")


def is_elevated() -> bool:
    """Whether the process is running as root or Administrator (SEC-013).

    This is only the check. Whether an elevated process is allowed to start is
    decided by the CLI, which owns the ``--allow-elevated`` flag.
    """
    return current_platform().is_elevated()


def check_secret_file_permissions(path: str | Path) -> SecretFilePermissions:
    """Verify a secret file's permissions on the running OS (SEC-014)."""
    return current_platform().check_secret_file_permissions(path)
