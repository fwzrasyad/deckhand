"""Configuration loading and platform paths.

Layer 0 (foundations). Never reads or writes ``actions.yaml``; that file belongs
to :mod:`deckhand.actions`.

The public surface is :func:`load_config` for ``config.toml`` and the directory
helpers in :mod:`deckhand.config.paths`, which apply the ``DECKHAND_HOME``
override.
"""

from __future__ import annotations

from deckhand.config.loader import ConfigError, load_config
from deckhand.config.paths import config_dir, config_file, home_override, log_dir, state_dir
from deckhand.config.settings import (
    ActionsSettings,
    LoggingSettings,
    MdnsSettings,
    NotifierSettings,
    RunsSettings,
    SecuritySettings,
    ServerSettings,
    Settings,
    TelemetrySettings,
)

__all__ = [
    "ActionsSettings",
    "ConfigError",
    "LoggingSettings",
    "MdnsSettings",
    "NotifierSettings",
    "RunsSettings",
    "SecuritySettings",
    "ServerSettings",
    "Settings",
    "TelemetrySettings",
    "config_dir",
    "config_file",
    "home_override",
    "load_config",
    "log_dir",
    "state_dir",
]
