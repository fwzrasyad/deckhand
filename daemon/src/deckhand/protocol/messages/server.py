"""Server-originated message payloads (S->C).

Layer 1. One pydantic model per message type, mirroring
``protocol/schemas/messages/``. Unknown fields are ignored (PROTO-002).
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar

from pydantic import Field

from ..errors import ErrorCode
from .shared import (
    ActionMeta,
    AlertRule,
    AuthFailCode,
    Capabilities,
    Hex64,
    Layout,
    LogLine,
    Nonce,
    OsName,
    PairFailCode,
    PingNonce,
    Proof,
    ProtocolModel,
    RunState,
    ShortId,
    StatusItem,
)

ProtocolVersion = Annotated[int, Field(ge=1)]


class HelloPayload(ProtocolModel):
    TYPE: ClassVar[str] = "HELLO"

    server_id: str
    server_name: str
    daemon_version: str
    protocol_versions: list[ProtocolVersion] = Field(min_length=1)
    os: OsName
    arch: str
    tls_fp: Hex64
    pairing_open: bool
    auth_required: bool


class SessionLimits(ProtocolModel):
    """Effective per-session limits carried by AUTH_OK."""

    max_frame_bytes: int | None = None
    messages_per_sec: int | None = None
    burst: int | None = None
    action_runs_per_sec: int | None = None


class AuthOkPayload(ProtocolModel):
    TYPE: ClassVar[str] = "AUTH_OK"

    session_id: str
    device_name: str
    protocol_version: int = Field(ge=1)
    server_time_ms: int = Field(ge=0)
    limits: SessionLimits


class AuthFailPayload(ProtocolModel):
    TYPE: ClassVar[str] = "AUTH_FAIL"

    code: AuthFailCode
    retry_after_sec: int | None = Field(default=None, ge=0)


class PairChallengePayload(ProtocolModel):
    TYPE: ClassVar[str] = "PAIR_CHALLENGE"

    server_nonce: Nonce


class PairOkPayload(ProtocolModel):
    TYPE: ClassVar[str] = "PAIR_OK"

    device_token: Hex64
    server_proof: Proof


class PairFailPayload(ProtocolModel):
    TYPE: ClassVar[str] = "PAIR_FAIL"

    code: PairFailCode


class PongPayload(ProtocolModel):
    """Answer to a PING; either side may send PONG (SRD 7.5)."""

    TYPE: ClassVar[str] = "PONG"

    nonce: PingNonce


class ServerShutdownPayload(ProtocolModel):
    TYPE: ClassVar[str] = "SERVER_SHUTDOWN"

    reason: str
    reconnect_after_sec: int = Field(ge=0)


class ErrorPayload(ProtocolModel):
    TYPE: ClassVar[str] = "ERROR"

    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None


class AlertRules(ProtocolModel):
    rev: int = Field(ge=0)
    rules: list[AlertRule]


class SnapshotPayload(ProtocolModel):
    TYPE: ClassVar[str] = "SNAPSHOT"

    capabilities: Capabilities
    actions: list[ActionMeta]
    layout: Layout
    statuses: list[StatusItem]
    active_runs: list[RunState]
    alert_rules: AlertRules
    active_alerts: list[dict[str, Any]]


class ActionAcceptedPayload(ProtocolModel):
    TYPE: ClassVar[str] = "ACTION_ACCEPTED"

    run_id: ShortId


class RunStatePayload(RunState):
    TYPE: ClassVar[str] = "RUN_STATE"


class ProcessLogPayload(ProtocolModel):
    TYPE: ClassVar[str] = "PROCESS_LOG"

    run_id: ShortId
    lines: list[LogLine]
    truncated: bool | None = None


class RunsPayload(ProtocolModel):
    TYPE: ClassVar[str] = "RUNS"

    runs: list[RunState]


__all__ = [
    "ActionAcceptedPayload",
    "AlertRules",
    "AuthFailPayload",
    "AuthOkPayload",
    "ErrorPayload",
    "HelloPayload",
    "PairChallengePayload",
    "PairFailPayload",
    "PairOkPayload",
    "PongPayload",
    "ProcessLogPayload",
    "RunStatePayload",
    "RunsPayload",
    "ServerShutdownPayload",
    "SessionLimits",
    "SnapshotPayload",
]
