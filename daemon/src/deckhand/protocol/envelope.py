"""The message envelope: ``v``, ``type``, ``id``, ``reply_to``, ``ts``, ``payload``.

Layer 1. ``Envelope`` is generic over the payload: the wire form uses a plain
JSON object, while :func:`deckhand.protocol.codec.decode` returns an envelope
whose ``payload`` is the typed pydantic model for the message.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

PayloadT = TypeVar("PayloadT")


class Envelope(BaseModel, Generic[PayloadT]):
    """Every Deckhand WebSocket text frame (SRD 7.2)."""

    model_config = ConfigDict(extra="ignore")

    v: int = Field(ge=1, description="Protocol version integer.")
    type: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]*$",
        description="Message type in SCREAMING_SNAKE_CASE.",
    )
    id: str = Field(
        min_length=1,
        max_length=64,
        description="Sender-generated identifier, unique within the session.",
    )
    ts: int = Field(ge=0, description="Sender wall clock in milliseconds since the epoch.")
    reply_to: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Optional id of the request being answered.",
    )
    payload: PayloadT


WireEnvelope = Envelope[dict[str, Any]]

__all__ = ["Envelope", "PayloadT", "WireEnvelope"]
