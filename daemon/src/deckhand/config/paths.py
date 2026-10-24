"""Resolves config, state, and log directories.

Layer 0 (foundations). The native locations come from
:class:`deckhand.platform.Platform`, which wraps ``platformdirs`` and therefore
keeps the OS-specific naming in one place (NFR-011). Setting ``DECKHAND_HOME``
replaces all three with ``config/``, ``state/``, and ``logs/`` below that root;
tests use it so they never read or write the developer's real directories
(SRD 8.1).
"""

from __future__ import annotations

import os
from pathlib import Path

from deckhand.config.defaults import (
    CONFIG_FILENAME,
    HOME_ENV_VAR,
    OVERRIDE_CONFIG_DIR,
    OVERRIDE_LOG_DIR,
    OVERRIDE_STATE_DIR,
)
from deckhand.platform import current_platform


def home_override() -> Path | None:
    """Return the ``DECKHAND_HOME`` root, or ``None`` when unset or empty."""
    value = os.environ.get(HOME_ENV_VAR, "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def config_dir() -> Path:
    """Directory holding ``config.toml`` and ``actions.yaml``."""
    override = home_override()
    if override is not None:
        return override / OVERRIDE_CONFIG_DIR
    return current_platform().config_dir()


def state_dir() -> Path:
    """Directory holding daemon-written state and secrets."""
    override = home_override()
    if override is not None:
        return override / OVERRIDE_STATE_DIR
    return current_platform().state_dir()


def log_dir() -> Path:
    """Directory holding ``deckhand.log`` and ``audit.log``."""
    override = home_override()
    if override is not None:
        return override / OVERRIDE_LOG_DIR
    return current_platform().log_dir()


def config_file() -> Path:
    """Path of ``config.toml`` inside :func:`config_dir`."""
    return config_dir() / CONFIG_FILENAME
