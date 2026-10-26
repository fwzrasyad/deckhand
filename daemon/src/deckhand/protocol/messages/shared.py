"""Payload shapes used by both directions (``ActionMeta``, ``RunState``, ...).

Layer 1. These models mirror ``protocol/schemas/shared/`` exactly, with the
SRD 7.6 field names frozen for protocol v1. Unknown fields are ignored
(PROTO-002).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Any, Final

from pydantic import BaseModel, ConfigDict, Field

ShortId = Annotated[str, Field(min_length=1, max_length=64)]
# Pairing nonces are exactly 16 bytes as 22 unpadded base64url characters.
Nonce = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{22}$")]
# PING/PONG nonces are opaque keepalive values, unrelated to pairing.
PingNonce = Annotated[str, Field(max_length=64)]
Proof = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{43}$")]
Hex64 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
UuidString = Annotated[
    str,
    Field(
        pattern=(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        )
    ),
]


class ProtocolModel(BaseModel):
    """Base for every payload model: unknown fields are ignored (PROTO-002)."""

    model_config = ConfigDict(extra="ignore")


class RunMode(StrEnum):
    PIPE = "pipe"
    PTY = "pty"


class ParamType(StrEnum):
    STRING = "string"
    INT = "int"
    NUMBER = "number"
    BOOL = "bool"
    ENUM = "enum"


class RunStateValue(StrEnum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    EXITED = "EXITED"
    FAILED_TO_START = "FAILED_TO_START"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class Signal(StrEnum):
    INTERRUPT = "INTERRUPT"
    TERMINATE = "TERMINATE"
    KILL = "KILL"


class LayoutCellKind(StrEnum):
    ACTION = "action"
    WIDGET = "widget"


class WidgetKind(StrEnum):
    CPU = "cpu"
    RAM = "ram"
    GPU = "gpu"
    DISK = "disk"
    NET = "net"
    BATTERY = "battery"


class AlertOperator(StrEnum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class LogStream(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


class ClientPlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"


class OsName(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class AuthFailCode(StrEnum):
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"  # noqa: S105 - protocol code, not a secret
    AUTH_REVOKED = "AUTH_REVOKED"
    AUTH_LOCKED_OUT = "AUTH_LOCKED_OUT"
    PROTO_VERSION_UNSUPPORTED = "PROTO_VERSION_UNSUPPORTED"


class PairFailCode(StrEnum):
    PAIR_WINDOW_CLOSED = "PAIR_WINDOW_CLOSED"
    PAIR_BAD_PROOF = "PAIR_BAD_PROOF"
    PAIR_LOCKED_OUT = "PAIR_LOCKED_OUT"


class ParamSpec(ProtocolModel):
    """One action parameter (SRD 7.6)."""

    name: ShortId
    label: str
    type: ParamType
    required: bool
    default: Any = None
    choices: list[Any] | None = None
    min: float | None = None
    max: float | None = None
    max_length: int | None = Field(default=None, ge=0)
    pattern: str | None = None
    secret: bool | None = None
    placeholder: str | None = None


class ActionMeta(ProtocolModel):
    """What the phone may know about an action (SRD 7.6).

    The run block -- argv, cwd, env, shell -- is deliberately absent and is
    never emitted by this model.
    """

    id: ShortId
    label: str
    icon: str
    category: str
    description: str
    mode: RunMode
    interactive: bool
    confirm: bool
    parallel: bool
    has_status: bool
    params: list[ParamSpec]


class RunStep(ProtocolModel):
    """Macro progress for a run."""

    index: int = Field(ge=0)
    total: int = Field(ge=1)


class RunState(ProtocolModel):
    """State of one run (SRD 7.6)."""

    run_id: ShortId
    action_id: ShortId
    state: RunStateValue
    started_at_ms: int = Field(ge=0)
    ended_at_ms: int | None = Field(default=None, ge=0)
    exit_code: int | None = None
    signal: Signal | None = None
    reason: str | None = None
    step: RunStep | None = None


class LayoutCell(ProtocolModel):
    col: int = Field(ge=0)
    row: int = Field(ge=0)
    col_span: int | None = Field(default=None, ge=1)
    row_span: int | None = Field(default=None, ge=1)
    kind: LayoutCellKind
    action_id: ShortId | None = None
    widget: WidgetKind | None = None


class LayoutPage(ProtocolModel):
    id: ShortId
    title: str
    cols: int = Field(ge=1, le=6)
    rows: int = Field(ge=1, le=8)
    cells: list[LayoutCell] = Field(max_length=48)


class Layout(ProtocolModel):
    rev: int = Field(ge=0)
    pages: list[LayoutPage] = Field(max_length=12)


class AlertRule(ProtocolModel):
    id: ShortId
    metric: str = Field(min_length=1)
    op: AlertOperator
    threshold: float
    for_sec: float = Field(ge=0)
    clear_margin: float = Field(ge=0)
    cooldown_sec: int = Field(ge=0)
    severity: Severity
    enabled: bool


class LogLine(ProtocolModel):
    seq: int = Field(ge=0)
    stream: LogStream
    ts: int = Field(ge=0)
    text: str


class StatusItem(ProtocolModel):
    action_id: ShortId
    state: str
    detail: str | None = None
    since_ms: int = Field(ge=0)


class CapabilitiesTelemetry(ProtocolModel):
    cpu_temp: bool
    gpu: bool
    gpu_vendors: list[str]
    battery: bool
    disk: bool
    net: bool


class CapabilitiesFeatures(ProtocolModel):
    pty: bool
    signals: list[Signal]
    probes: list[str]
    notifier: str


class Capabilities(ProtocolModel):
    """What the daemon host can do (SRD 7.6), frozen for protocol v1."""

    os: OsName
    telemetry: CapabilitiesTelemetry
    features: CapabilitiesFeatures


SHARED_MODELS: Final[Mapping[str, type[ProtocolModel]]] = MappingProxyType(
    {
        "ActionMeta": ActionMeta,
        "AlertRule": AlertRule,
        "Capabilities": Capabilities,
        "Layout": Layout,
        "LogLine": LogLine,
        "ParamSpec": ParamSpec,
        "RunState": RunState,
        "StatusItem": StatusItem,
    }
)

__all__ = [
    "SHARED_MODELS",
    "ActionMeta",
    "AlertOperator",
    "AlertRule",
    "AuthFailCode",
    "Capabilities",
    "CapabilitiesFeatures",
    "CapabilitiesTelemetry",
    "ClientPlatform",
    "Hex64",
    "Layout",
    "LayoutCell",
    "LayoutCellKind",
    "LayoutPage",
    "LogLine",
    "LogStream",
    "Nonce",
    "OsName",
    "PairFailCode",
    "ParamSpec",
    "ParamType",
    "Proof",
    "ProtocolModel",
    "RunMode",
    "RunState",
    "RunStateValue",
    "RunStep",
    "Severity",
    "ShortId",
    "Signal",
    "StatusItem",
    "UuidString",
    "WidgetKind",
]
