"""Windows implementation of the platform interface.

Layer 0 (foundations). Tier 1 target. ``platformdirs`` maps the SRD 8.1 layout to
``%APPDATA%\\Deckhand`` (config) and ``%LOCALAPPDATA%\\Deckhand`` (state, logs).
"""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import ClassVar

from platformdirs import user_config_dir, user_data_dir, user_log_dir

from deckhand.platform.base import Platform, SecretFilePermissions

APP_NAME = "Deckhand"
"""Capitalised on Windows and macOS; Linux uses the lowercase form."""

CREATE_NEW_PROCESS_GROUP = 0x00000200
"""``subprocess.CREATE_NEW_PROCESS_GROUP``.

Spelled out as a literal because the constant only exists in ``subprocess`` on
Windows, while this module is still importable -- and type-checked -- elsewhere.
"""

ACL_NOT_VERIFIED = (
    "Windows ACL verification is not implemented; secret file permissions are "
    "inherited from the parent directory, which the installer must restrict to "
    "the current user"
)
"""Returned by :meth:`WindowsPlatform.check_secret_file_permissions` (SEC-014)."""


class WindowsPlatform(Platform):
    """OS facts for Windows 10 and 11."""

    name: ClassVar[str] = "windows"

    def config_dir(self) -> Path:
        return Path(user_config_dir(APP_NAME, appauthor=False, roaming=True))

    def state_dir(self) -> Path:
        return Path(user_data_dir(APP_NAME, appauthor=False))

    def log_dir(self) -> Path:
        return Path(user_log_dir(APP_NAME, appauthor=False))

    def is_elevated(self) -> bool:
        windll = getattr(ctypes, "windll", None)
        if windll is None:  # pragma: no cover - only reachable off Windows
            return False
        return bool(windll.shell32.IsUserAnAdmin())

    def process_group_kwargs(self) -> dict[str, object]:
        return {"creationflags": CREATE_NEW_PROCESS_GROUP}

    def check_secret_file_permissions(self, path: str | Path) -> SecretFilePermissions:
        """Report that ACL verification is not enforced on Windows (SEC-014)."""
        return SecretFilePermissions(
            path=Path(path),
            enforced=False,
            ok=True,
            detail=ACL_NOT_VERIFIED,
        )
