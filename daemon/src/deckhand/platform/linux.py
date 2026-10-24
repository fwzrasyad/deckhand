"""Linux implementation of the platform interface.

Layer 0 (foundations). Tier 1 target. ``platformdirs`` maps the SRD 8.1 layout to
``~/.config/deckhand`` (config) and ``~/.local/state/deckhand`` (state, logs),
honouring ``XDG_CONFIG_HOME`` and ``XDG_STATE_HOME``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from platformdirs import user_config_dir, user_log_dir, user_state_dir

from deckhand.platform.base import Platform, SecretFilePermissions, check_posix_secret_permissions

APP_NAME = "deckhand"


class LinuxPlatform(Platform):
    """OS facts for Linux desktops."""

    name: ClassVar[str] = "linux"

    def config_dir(self) -> Path:
        return Path(user_config_dir(APP_NAME))

    def state_dir(self) -> Path:
        return Path(user_state_dir(APP_NAME))

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
