"""Encode and decode envelope frames, mapping failures to protocol errors.

Layer 1. No I/O and no transport knowledge: :func:`decode` takes text and
returns a typed :class:`~deckhand.protocol.envelope.Envelope`; :func:`encode`
does the reverse. Unknown fields are ignored (PROTO-002) and every failure is
reported as a :class:`~deckhand.protocol.errors.ProtocolError`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Final, NoReturn

from pydantic import BaseModel, ValidationError

from .envelope import Envelope, WireEnvelope
from .errors import ErrorCode, ProtocolError
from .messages.client import (
    ActionRunPayload,
    AuthPayload,
    PairProofPayload,
    PairRequestPayload,
    PingPayload,
    RunSignalPayload,
    RunsListPayload,
    SnapshotGetPayload,
    UnpairSelfPayload,
)
from .messages.server import (
    ActionAcceptedPayload,
    AuthFailPayload,
    AuthOkPayload,
    ErrorPayload,
    HelloPayload,
    PairChallengePayload,
    PairFailPayload,
    PairOkPayload,
    PongPayload,
    ProcessLogPayload,
    RunsPayload,
    RunStatePayload,
    ServerShutdownPayload,
    SnapshotPayload,
)
from .messages.shared import ProtocolModel

MESSAGE_MODELS: Final[Mapping[str, type[ProtocolModel]]] = MappingProxyType(
    {
        model.TYPE: model
        for model in (
            ActionAcceptedPayload,
            ActionRunPayload,
            AuthFailPayload,
            AuthOkPayload,
            AuthPayload,
            ErrorPayload,
            HelloPayload,
            PairChallengePayload,
            PairFailPayload,
            PairOkPayload,
            PairProofPayload,
            PairRequestPayload,
            PingPayload,
            PongPayload,
            ProcessLogPayload,
            RunSignalPayload,
            RunStatePayload,
            RunsListPayload,
            RunsPayload,
            ServerShutdownPayload,
            SnapshotGetPayload,
            SnapshotPayload,
            UnpairSelfPayload,
        )
    }
)


def _reject_constant(token: str) -> NoReturn:
    """Reject NaN/Infinity, which are not valid JSON (RFC 8259)."""
    raise ValueError(f"non-finite JSON number: {token}")


def _validation_detail(error: ValidationError) -> str:
    """Describe validation failures using field locations only.

    Pydantic's ``str(error)`` includes ``input_value``, which may contain
    paths, argv, or environment data. Only the location and error kind are
    safe to put on the wire (PROTO-005).
    """
    parts: list[str] = []
    for item in error.errors(include_input=False):
        location = ".".join(str(part) for part in item["loc"])
        kind = item["type"]
        parts.append(f"{location}:{kind}" if location else kind)
        if len(parts) == 3:
            break
    return ", ".join(parts) if parts else "validation failed"


def _decode(text: str) -> Envelope[Any]:
    try:
        raw: Any = json.loads(text, parse_constant=_reject_constant)
    except Exception as exc:
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Message is not valid JSON") from exc

    if not isinstance(raw, dict):
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Message envelope must be a JSON object")

    try:
        envelope = WireEnvelope.model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError(
            ErrorCode.PROTO_MALFORMED,
            f"Invalid envelope ({_validation_detail(exc)})",
        ) from exc
    except Exception as exc:
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Invalid envelope") from exc

    payload_model = MESSAGE_MODELS.get(envelope.type)
    if payload_model is None:
        raise ProtocolError(ErrorCode.PROTO_UNKNOWN_TYPE, "Unknown message type")

    try:
        payload = payload_model.model_validate(envelope.payload)
    except ValidationError as exc:
        raise ProtocolError(
            ErrorCode.PROTO_MALFORMED,
            f"Invalid payload ({_validation_detail(exc)})",
        ) from exc
    except Exception as exc:
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Invalid payload") from exc

    return Envelope[Any](
        v=envelope.v,
        type=envelope.type,
        id=envelope.id,
        ts=envelope.ts,
        reply_to=envelope.reply_to,
        payload=payload,
    )


def decode(text: str) -> Envelope[Any]:
    """Decode one wire frame into a typed message.

    Raises :class:`ProtocolError` with ``PROTO_MALFORMED`` for invalid JSON,
    envelope failures, and payload validation failures, and
    ``PROTO_UNKNOWN_TYPE`` for a well-formed envelope with an unknown type.
    No other exception escapes, whatever the input.
    """
    try:
        return _decode(text)
    except ProtocolError:
        raise
    except Exception as exc:
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Message could not be decoded") from exc


def _payload_to_json(payload: Any) -> Any:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    return payload


def encode(message: Envelope[Any]) -> str:
    """Encode a typed message as a compact UTF-8 JSON text frame."""
    try:
        document: dict[str, Any] = {
            "v": message.v,
            "type": message.type,
            "id": message.id,
            "ts": message.ts,
        }
        if message.reply_to is not None:
            document["reply_to"] = message.reply_to
        document["payload"] = _payload_to_json(message.payload)
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except Exception as exc:
        raise ProtocolError(ErrorCode.PROTO_MALFORMED, "Message cannot be encoded") from exc


__all__ = ["MESSAGE_MODELS", "decode", "encode"]
