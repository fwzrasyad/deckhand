"""The error code registry and close-code constants (SRD 7.7).

Layer 1. Messages raised by this module are safe to send to a client: they
never contain argv, filesystem paths, environment values, or stack traces
(PROTO-005). Structured detail belongs in the daemon log, not on the wire.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from enum import IntEnum, StrEnum
from types import MappingProxyType
from typing import Final

from deckhand.core.errors import DeckhandError


class ErrorCode(StrEnum):
    """Machine-readable error codes from SRD 7.7, in registry order."""

    PROTO_MALFORMED = "PROTO_MALFORMED"
    PROTO_UNKNOWN_TYPE = "PROTO_UNKNOWN_TYPE"
    PROTO_VERSION_UNSUPPORTED = "PROTO_VERSION_UNSUPPORTED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"  # noqa: S105 - protocol code, not a secret
    AUTH_REVOKED = "AUTH_REVOKED"
    AUTH_LOCKED_OUT = "AUTH_LOCKED_OUT"
    PAIR_WINDOW_CLOSED = "PAIR_WINDOW_CLOSED"
    PAIR_BAD_PROOF = "PAIR_BAD_PROOF"
    PAIR_LOCKED_OUT = "PAIR_LOCKED_OUT"
    RATE_LIMITED = "RATE_LIMITED"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    PARAM_INVALID = "PARAM_INVALID"
    ACTION_BUSY = "ACTION_BUSY"
    RUN_LIMIT_REACHED = "RUN_LIMIT_REACHED"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_NOT_ACTIVE = "RUN_NOT_ACTIVE"
    RUN_NOT_INTERACTIVE = "RUN_NOT_INTERACTIVE"
    SIGNAL_UNSUPPORTED = "SIGNAL_UNSUPPORTED"
    LAYOUT_CONFLICT = "LAYOUT_CONFLICT"
    LAYOUT_INVALID = "LAYOUT_INVALID"
    ALERT_RULES_INVALID = "ALERT_RULES_INVALID"
    UNSUPPORTED_ON_HOST = "UNSUPPORTED_ON_HOST"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CloseCode(IntEnum):
    """WebSocket close codes used by the daemon (SRD 7.7)."""

    NORMAL = 1000
    GOING_AWAY = 1001
    BINARY_NOT_SUPPORTED = 1003
    MESSAGE_TOO_BIG = 1009
    INTERNAL_ERROR = 1011
    PROTOCOL_ERROR = 4400
    AUTH_FAILED = 4401
    AUTH_TIMEOUT = 4408
    RATE_LIMITED = 4429
    SHUTTING_DOWN = 4503


_DEFAULT_MESSAGES: Final[Mapping[ErrorCode, str]] = MappingProxyType(
    {
        ErrorCode.PROTO_MALFORMED: "Message does not match the protocol",
        ErrorCode.PROTO_UNKNOWN_TYPE: "Unknown message type",
        ErrorCode.PROTO_VERSION_UNSUPPORTED: "No compatible protocol version",
        ErrorCode.AUTH_REQUIRED: "Authentication is required",
        ErrorCode.AUTH_INVALID_TOKEN: "Authentication failed",
        ErrorCode.AUTH_REVOKED: "This device is no longer authorised",
        ErrorCode.AUTH_LOCKED_OUT: "Too many authentication failures",
        ErrorCode.PAIR_WINDOW_CLOSED: "The pairing window is closed",
        ErrorCode.PAIR_BAD_PROOF: "Pairing proof did not match",
        ErrorCode.PAIR_LOCKED_OUT: "Too many pairing failures",
        ErrorCode.RATE_LIMITED: "Too many messages",
        ErrorCode.ACTION_NOT_FOUND: "Action not found",
        ErrorCode.PARAM_INVALID: "Invalid parameters",
        ErrorCode.ACTION_BUSY: "Action is already running",
        ErrorCode.RUN_LIMIT_REACHED: "Run limit reached",
        ErrorCode.RUN_NOT_FOUND: "Run not found",
        ErrorCode.RUN_NOT_ACTIVE: "Run is not active",
        ErrorCode.RUN_NOT_INTERACTIVE: "Run is not interactive",
        ErrorCode.SIGNAL_UNSUPPORTED: "Signal is not supported",
        ErrorCode.LAYOUT_CONFLICT: "Layout revision conflict",
        ErrorCode.LAYOUT_INVALID: "Layout is invalid",
        ErrorCode.ALERT_RULES_INVALID: "Alert rules are invalid",
        ErrorCode.UNSUPPORTED_ON_HOST: "Not supported on this host",
        ErrorCode.SHUTTING_DOWN: "Daemon is shutting down",
        ErrorCode.INTERNAL_ERROR: "Internal error",
    }
)

_UNSAFE_WORDS: Final[re.Pattern[str]] = re.compile(r"traceback|argv", re.IGNORECASE)
_ENV_ASSIGNMENT: Final[re.Pattern[str]] = re.compile(r"\b[A-Z][A-Z0-9_]{2,}=[^\s]+")


def sanitize_error_message(message: str) -> str:
    """Return ``message`` with unsafe wire content removed.

    Path separators are replaced, stack-trace markers and ``argv`` words are
    redacted, environment-looking assignments are dropped, and control
    characters (including NUL) are collapsed to spaces.
    """
    cleaned = _ENV_ASSIGNMENT.sub("setting", message)
    cleaned = cleaned.replace("/", " ").replace("\\", " ")
    cleaned = _UNSAFE_WORDS.sub("details", cleaned)
    cleaned = "".join(char if char.isprintable() else " " for char in cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned or "Protocol error"


class ProtocolError(DeckhandError):
    """A protocol failure with a stable code and a wire-safe message.

    ``message`` is sanitised in the constructor. Callers may attach structured
    ``details`` for local logging, but those details must never be serialised
    into an ERROR payload.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        *,
        close_code: CloseCode | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        safe_message = (
            _DEFAULT_MESSAGES[code] if message is None else sanitize_error_message(message)
        )
        super().__init__(safe_message, details=details)
        self.code = code
        self.close_code = close_code


ERROR_CODES: Final[tuple[ErrorCode, ...]] = tuple(ErrorCode)
CLOSE_CODES: Final[tuple[CloseCode, ...]] = tuple(CloseCode)

__all__ = [
    "CLOSE_CODES",
    "ERROR_CODES",
    "CloseCode",
    "ErrorCode",
    "ProtocolError",
    "sanitize_error_message",
]
