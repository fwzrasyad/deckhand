"""Client-originated message payloads (C->S).

Layer 1. One pydantic model per message type, mirroring
``protocol/schemas/messages/``. Unknown fields are ignored (PROTO-002).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from .shared import (
    ClientPlatform,
    Hex64,
    Nonce,
    Proof,
    ProtocolModel,
    ShortId,
    Signal,
    UuidString,
)


class ClientInfo(ProtocolModel):
    """Client identification metadata carried by AUTH."""

    app_version: str
    platform: ClientPlatform


class AuthPayload(ProtocolModel):
    TYPE: ClassVar[str] = "AUTH"

    device_id: UuidString
    token: Hex64
    protocol_version: int = Field(ge=1)
    client: ClientInfo


class PairRequestPayload(ProtocolModel):
    TYPE: ClassVar[str] = "PAIR_REQUEST"

    device_id: UuidString
    device_name: str = Field(min_length=1)
    client_nonce: Nonce


class PairProofPayload(ProtocolModel):
    TYPE: ClassVar[str] = "PAIR_PROOF"

    proof: Proof


class UnpairSelfPayload(ProtocolModel):
    TYPE: ClassVar[str] = "UNPAIR_SELF"


class PingPayload(ProtocolModel):
    """Keepalive/RTT probe; either side may send PING (SRD 7.5)."""

    TYPE: ClassVar[str] = "PING"

    nonce: Nonce


class ActionRunPayload(ProtocolModel):
    TYPE: ClassVar[str] = "ACTION_RUN"

    action_id: ShortId
    params: dict[str, Any]
    confirmed: bool | None = None


class RunSignalPayload(ProtocolModel):
    TYPE: ClassVar[str] = "RUN_SIGNAL"

    run_id: ShortId
    signal: Signal


class RunsListPayload(ProtocolModel):
    TYPE: ClassVar[str] = "RUNS_LIST"

    limit: int | None = Field(default=None, ge=1)


class SnapshotGetPayload(ProtocolModel):
    TYPE: ClassVar[str] = "SNAPSHOT_GET"


__all__ = [
    "ActionRunPayload",
    "AuthPayload",
    "ClientInfo",
    "PairProofPayload",
    "PairRequestPayload",
    "PingPayload",
    "RunSignalPayload",
    "RunsListPayload",
    "SnapshotGetPayload",
    "UnpairSelfPayload",
]
