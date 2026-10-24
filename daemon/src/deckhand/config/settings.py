"""Pydantic models for ``config.toml`` with the defaults from SRD 8.2.

Layer 0 (foundations). Every key is optional and every section has the exact
default shown in the SRD. Unknown keys are a validation error at every level, so
a typo in a user-edited file fails loudly instead of being ignored.

These models describe configuration only; they never read files. Pair them with
:func:`deckhand.config.loader.load_config`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "LOG_LEVELS",
    "ActionsSettings",
    "LoggingSettings",
    "MdnsSettings",
    "NotifierSettings",
    "RunsSettings",
    "SecuritySettings",
    "ServerSettings",
    "Settings",
    "TelemetrySettings",
]

LOG_LEVELS: frozenset[str] = frozenset({"CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING"})
"""Levels accepted by :class:`LoggingSettings`, upper-cased."""


class _Section(BaseModel):
    """Common configuration: immutable, and unknown keys are rejected."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _default_allowed_networks() -> list[str]:
    """Return the SRD 8.2 default network allowlist (loopback, RFC 1918, CGNAT, ULA)."""
    return [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "fe80::/10",
        "fc00::/7",
    ]


class ServerSettings(_Section):
    """``[server]``."""

    bind: str = "0.0.0.0"  # noqa: S104 - LAN binding is the product; source IPs are filtered
    port: int = Field(default=47800, ge=1, le=65535)
    allowed_networks: list[str] = Field(default_factory=_default_allowed_networks)
    max_connections: int = Field(default=8, ge=1)
    max_unauthenticated: int = Field(default=4, ge=0)


class SecuritySettings(_Section):
    """``[security]``."""

    allow_shell: bool = False
    remote_layout_edit: bool = True
    remote_alert_edit: bool = True


class RunsSettings(_Section):
    """``[runs]``."""

    max_concurrent: int = Field(default=16, ge=1)
    default_timeout_sec: int = Field(default=0, ge=0)
    kill_grace_sec: int = Field(default=5, ge=0)
    kill_on_exit: bool = True
    log_buffer_lines: int = Field(default=5000, ge=1)
    retain_finished: int = Field(default=20, ge=0)
    retain_minutes: int = Field(default=30, ge=0)


class TelemetrySettings(_Section):
    """``[telemetry]``."""

    default_interval_ms: int = Field(default=1000, ge=1)
    libre_hardware_monitor_url: str = ""


class MdnsSettings(_Section):
    """``[mdns]``."""

    enabled: bool = True


class ActionsSettings(_Section):
    """``[actions]`` -- settings *about* ``actions.yaml``, never its contents."""

    watch: bool = True


class LoggingSettings(_Section):
    """``[logging]``."""

    level: str = "INFO"
    json_file: bool = True

    @field_validator("level")
    @classmethod
    def _normalize_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in LOG_LEVELS:
            raise ValueError(f"level must be one of {sorted(LOG_LEVELS)}")
        return normalized


class NotifierSettings(_Section):
    """``[notifier]``."""

    type: Literal["none", "ntfy"] = "none"
    url: str = ""


class Settings(_Section):
    """The whole of ``config.toml`` (SRD 8.2).

    ``Settings()`` is the configuration used when the file does not exist.
    """

    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    runs: RunsSettings = Field(default_factory=RunsSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    mdns: MdnsSettings = Field(default_factory=MdnsSettings)
    actions: ActionsSettings = Field(default_factory=ActionsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    notifier: NotifierSettings = Field(default_factory=NotifierSettings)
