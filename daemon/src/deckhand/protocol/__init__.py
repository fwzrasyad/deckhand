"""Wire protocol models and codec. No I/O.

Layer 1. May import :mod:`deckhand.core` only. The schemas under ``/protocol``
are the single source of truth; these models mirror them.
"""

from __future__ import annotations

from .codec import MESSAGE_MODELS, decode, encode
from .envelope import Envelope, WireEnvelope
from .errors import CLOSE_CODES, ERROR_CODES, CloseCode, ErrorCode, ProtocolError
from .versions import (
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    is_supported,
    negotiate_version,
)

__all__ = [
    "CLOSE_CODES",
    "CURRENT_VERSION",
    "ERROR_CODES",
    "MESSAGE_MODELS",
    "SUPPORTED_VERSIONS",
    "CloseCode",
    "Envelope",
    "ErrorCode",
    "ProtocolError",
    "WireEnvelope",
    "decode",
    "encode",
    "is_supported",
    "negotiate_version",
]
