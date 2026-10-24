"""macOS implementation of the platform interface.

Layer 0 (foundations). Tier 2 target. ``platformdirs`` maps the SRD 8.1 layout to
``~/Library/Application Support/Deckhand`` (config), ``.../Deckhand/state``
(state), and ``~/Library/Logs/Deckhand`` (logs).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from platformdirs import user_config_dir, user_data_dir, user_log_dir

from deckhand.platform.base import Platform, SecretFilePermissions, check_posix_secret_permissions

APP_NAME = "Deckhand"

STATE_SUBDIRECTORY = "state"


class MacOSPlatform(Platform):
    """OS facts for macOS."""

    name: ClassVar[str] = "macos"

    def config_dir(self) -> Path:
        return Path(user_config_dir(APP_NAME))

    def state_dir(self) -> Path:
        return Path(user_data_dir(APP_NAME)) / STATE_SUBDIRECTORY

    def log_dir(self) -> Path:
        return Path(user_log_dir(APP_NAME))

    def is_elevated(self) -> bool:
        geteuid = getattr(os, "geteuid", None)
        if geteuid is None:  # pragma: no cover - only reachable off POSIX
            return False
        return bool(geteuid() == 0)

    def process_group_kwargs(self) -> dict[str, object]:
        return {"start_new_session": True}

    def check_secret_file_permissions(self, path: str | Path) -> SecretFilePermissions:
        return check_posix_secret_permissions(path)
