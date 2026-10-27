"""The pairing window state machine and proof verification (SRD 4.4, SEC-007).

Layer 2. A :class:`PairingWindow` owns the lifecycle of one pairing secret:

* ``open()`` starts a 120 s window with a fresh secret. It is refused during
  the 30 s cooldown that follows the fifth failed proof.
* ``begin()`` handles ``PAIR_REQUEST`` and returns the server nonce for
  ``PAIR_CHALLENGE``. ``submit()`` handles ``PAIR_PROOF``; each challenge
  allows exactly one proof attempt.
* At most five failed proofs are allowed across all clients. The fifth closes
  the window and starts the cooldown. The first success closes the window.

Failures are also reported to the shared per-IP :class:`LockoutTracker`
(SEC-010). A proof failure counts toward both the window's five and the IP's
five; a request that finds the window closed or cooling down counts toward the
IP only. A blocked IP is answered ``PAIR_LOCKED_OUT`` without further counting.

The window has no timers. Expiry is evaluated against the injected clock on
every call, and the owner may call :meth:`PairingWindow.expire_if_due` from a
timer so the "window closed" event is delivered promptly. All methods are
synchronous and meant to be driven from one event loop.

The pairing secret and the plaintext device token exist only in the objects
returned to the caller; they are hidden from ``repr`` and never placed in
exception messages (SEC-016).
"""

from __future__ import annotations

import re
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Protocol

from deckhand.core.clock import Clock
from deckhand.core.errors import DeckhandError
from deckhand.protocol.errors import ErrorCode
from deckhand.security.crypto import (
    b64url_decode,
    b64url_encode,
    compute_proof,
    generate_pairing_secret,
    normalize_secret,
    verify_proof,
)
from deckhand.security.lockout import LockoutTracker
from deckhand.security.tokens import generate_token, hash_token

WINDOW_SEC: Final[float] = 120.0
MAX_FAILED_PROOFS: Final[int] = 5
COOLDOWN_SEC: Final[float] = 30.0
NONCE_BYTES: Final[int] = 16
MAX_PENDING_CHALLENGES: Final[int] = 16

_FINGERPRINT_PATTERN: Final[re.Pattern[str]] = re.compile(r"[0-9a-f]{64}")


class WindowState(StrEnum):
    """Where the pairing window is in its lifecycle."""

    CLOSED = "closed"
    OPEN = "open"
    COOLDOWN = "cooldown"


class CloseReason(StrEnum):
    """Why a window closed (for the audit log, SRD 4.8)."""

    EXPIRED = "expired"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    TOO_MANY_FAILURES = "too_many_failures"


class PairingUnavailableError(DeckhandError):
    """A window cannot be opened right now because of the post-lockout cooldown."""

    def __init__(self, retry_after_sec: float) -> None:
        super().__init__("pairing is cooling down after too many failed attempts")
        self.retry_after_sec = retry_after_sec


class PairingEvents(Protocol):
    """Observer for security events; the audit log (step 3c) implements this."""

    def window_opened(self, expires_in_sec: float) -> None:
        """A window opened."""
        ...  # pragma: no cover - protocol declaration

    def window_closed(self, reason: CloseReason) -> None:
        """The window closed."""
        ...  # pragma: no cover - protocol declaration

    def pair_success(self, device_id: str, source_ip: str) -> None:
        """A device paired successfully."""
        ...  # pragma: no cover - protocol declaration

    def pair_failure(self, code: ErrorCode, source_ip: str) -> None:
        """A pairing attempt was refused."""
        ...  # pragma: no cover - protocol declaration


class _NoEvents:
    def window_opened(self, expires_in_sec: float) -> None:
        return None

    def window_closed(self, reason: CloseReason) -> None:
        return None

    def pair_success(self, device_id: str, source_ip: str) -> None:
        return None

    def pair_failure(self, code: ErrorCode, source_ip: str) -> None:
        return None


@dataclass(frozen=True, slots=True)
class OpenedWindow:
    """What the CLI and tray show while a window is open."""

    secret: str = field(repr=False)
    """Grouped ``XXXX-XXXX-XXXX`` secret to show as text and in the QR code."""
    expires_in_sec: float


@dataclass(frozen=True, slots=True)
class Challenge:
    """The answer to ``PAIR_REQUEST``: send ``server_nonce`` in ``PAIR_CHALLENGE``."""

    server_nonce: str
    handle: str = field(repr=False)
    """Opaque reference the transport session passes back to ``submit``."""


@dataclass(frozen=True, slots=True)
class PairingSuccess:
    """A verified pairing. The plaintext device token is available only here."""

    device_id: str
    device_name: str
    server_proof: str
    token_sha256: str
    device_token: str = field(repr=False)
    """Send in ``PAIR_OK`` and then discard; only ``token_sha256`` is stored."""


@dataclass(frozen=True, slots=True)
class PairingFailure:
    """A refused attempt: send ``PAIR_FAIL`` with ``code`` and close with 4401."""

    code: ErrorCode
    retry_after_sec: float | None = None


@dataclass(slots=True)
class _Pending:
    device_id: str
    device_name: str
    client_nonce: str
    server_nonce: str


class PairingWindow:
    """The pairing window for one daemon, following SRD 4.4 exactly."""

    def __init__(
        self,
        clock: Clock,
        lockout: LockoutTracker,
        cert_fingerprint: str,
        *,
        rng: Callable[[int], bytes] | None = None,
        events: PairingEvents | None = None,
        window_sec: float = WINDOW_SEC,
        max_failed_proofs: int = MAX_FAILED_PROOFS,
        cooldown_sec: float = COOLDOWN_SEC,
    ) -> None:
        if not _FINGERPRINT_PATTERN.fullmatch(cert_fingerprint):
            raise ValueError("certificate fingerprint must be 64 lowercase hex characters")
        if window_sec <= 0 or cooldown_sec <= 0 or max_failed_proofs < 1:
            raise ValueError("window, cooldown and attempt limits must be positive")
        self._clock = clock
        self._lockout = lockout
        self._fingerprint = cert_fingerprint
        self._rng = secrets.token_bytes if rng is None else rng
        self._events: PairingEvents = _NoEvents() if events is None else events
        self._window_sec = window_sec
        self._max_failed = max_failed_proofs
        self._cooldown_sec = cooldown_sec

        self._state = WindowState.CLOSED
        self._deadline = 0.0  # window expiry while OPEN, cooldown end while COOLDOWN
        self._failed_proofs = 0
        self._secret: str | None = None  # normalized, only while OPEN
        self._display_secret: str | None = None
        self._pending: dict[str, _Pending] = {}

    def __repr__(self) -> str:
        return f"PairingWindow(state={self.state.value!r})"

    # ── State ─────────────────────────────────────────────────────────────

    @property
    def state(self) -> WindowState:
        """Current state, after applying any expiry that is due."""
        self._refresh()
        return self._state

    @property
    def is_open(self) -> bool:
        """Whether a client may pair right now (drives the mDNS ``pair`` flag)."""
        return self.state is WindowState.OPEN

    @property
    def remaining_sec(self) -> float:
        """Seconds left in the open window, or in the cooldown; ``0.0`` if idle."""
        self._refresh()
        if self._state is WindowState.CLOSED:
            return 0.0
        return max(self._deadline - self._clock.monotonic(), 0.0)

    def expire_if_due(self) -> None:
        """Apply expiry now so the ``window_closed`` event is not delayed."""
        self._refresh()

    # ── Window control (CLI, tray, control channel) ───────────────────────

    def open(self) -> OpenedWindow:
        """Open a window, or return the one that is already open.

        Raises:
            PairingUnavailableError: the post-lockout cooldown is still running.
        """
        self._refresh()
        if self._state is WindowState.COOLDOWN:
            raise PairingUnavailableError(self.remaining_sec)
        if self._state is WindowState.OPEN:
            return self._opened()

        display = generate_pairing_secret(self._rng)
        self._display_secret = display
        self._secret = normalize_secret(display)
        self._state = WindowState.OPEN
        self._deadline = self._clock.monotonic() + self._window_sec
        self._failed_proofs = 0
        self._pending.clear()
        self._events.window_opened(self._window_sec)
        return self._opened()

    def cancel(self) -> bool:
        """Close an open window (``deckhand pair --cancel``); return whether one was open."""
        self._refresh()
        if self._state is not WindowState.OPEN:
            return False
        self._close(CloseReason.CANCELLED)
        return True

    # ── Handshake (transport handlers) ────────────────────────────────────

    def begin(
        self,
        source_ip: str,
        device_id: str,
        device_name: str,
        client_nonce: str,
    ) -> Challenge | PairingFailure:
        """Handle ``PAIR_REQUEST``: return the challenge to send, or a failure."""
        self._refresh()
        refused = self._gate(source_ip)
        if refused is not None:
            return refused
        if not _is_canonical_uuid(device_id) or not _is_nonce(client_nonce):
            return self._fail(ErrorCode.PAIR_BAD_PROOF, source_ip)

        server_nonce = b64url_encode(self._rng(NONCE_BYTES))
        handle = b64url_encode(self._rng(NONCE_BYTES))
        self._pending[handle] = _Pending(device_id, device_name, client_nonce, server_nonce)
        while len(self._pending) > MAX_PENDING_CHALLENGES:
            del self._pending[next(iter(self._pending))]
        return Challenge(server_nonce=server_nonce, handle=handle)

    def submit(self, source_ip: str, handle: str, proof: str) -> PairingSuccess | PairingFailure:
        """Handle ``PAIR_PROOF``: verify the client proof and complete or refuse."""
        self._refresh()
        refused = self._gate(source_ip)
        if refused is not None:
            return refused

        pending = self._pending.pop(handle, None)
        secret = self._secret
        if pending is None or secret is None:
            return self._bad_proof(source_ip)
        verified = verify_proof(
            secret,
            "client",
            self._fingerprint,
            pending.client_nonce,
            pending.server_nonce,
            pending.device_id,
            proof,
        )
        if not verified:
            return self._bad_proof(source_ip)

        server_proof = compute_proof(
            secret,
            "server",
            self._fingerprint,
            pending.client_nonce,
            pending.server_nonce,
            pending.device_id,
        )
        device_token = generate_token(self._rng)
        self._close(CloseReason.SUCCESS)
        self._events.pair_success(pending.device_id, source_ip)
        return PairingSuccess(
            device_id=pending.device_id,
            device_name=pending.device_name,
            server_proof=server_proof,
            token_sha256=hash_token(device_token),
            device_token=device_token,
        )

    # ── Internals ─────────────────────────────────────────────────────────

    def _opened(self) -> OpenedWindow:
        display = self._display_secret
        if display is None:  # pragma: no cover - OPEN always has a secret
            raise RuntimeError("pairing window is open without a secret")
        return OpenedWindow(secret=display, expires_in_sec=self.remaining_sec)

    def _refresh(self) -> None:
        """Apply time-based transitions: window expiry and cooldown end."""
        now = self._clock.monotonic()
        if self._state is WindowState.OPEN and now >= self._deadline:
            self._close(CloseReason.EXPIRED)
        elif self._state is WindowState.COOLDOWN and now >= self._deadline:
            self._state = WindowState.CLOSED

    def _close(self, reason: CloseReason) -> None:
        self._secret = None
        self._display_secret = None
        self._pending.clear()
        self._failed_proofs = 0
        if reason is CloseReason.TOO_MANY_FAILURES:
            self._state = WindowState.COOLDOWN
            self._deadline = self._clock.monotonic() + self._cooldown_sec
        else:
            self._state = WindowState.CLOSED
        self._events.window_closed(reason)

    def _gate(self, source_ip: str) -> PairingFailure | None:
        """Refuse requests that cannot proceed: blocked IP, cooldown, closed window."""
        status = self._lockout.check(source_ip)
        if status.blocked:
            return self._fail(
                ErrorCode.PAIR_LOCKED_OUT,
                source_ip,
                retry_after_sec=status.retry_after,
                count_against_ip=False,
            )
        if self._state is WindowState.COOLDOWN:
            return self._fail(
                ErrorCode.PAIR_LOCKED_OUT,
                source_ip,
                retry_after_sec=self.remaining_sec,
            )
        if self._state is WindowState.CLOSED:
            return self._fail(ErrorCode.PAIR_WINDOW_CLOSED, source_ip)
        return None

    def _bad_proof(self, source_ip: str) -> PairingFailure:
        """Count one failed proof against the window and the IP."""
        self._failed_proofs += 1
        failure = self._fail(ErrorCode.PAIR_BAD_PROOF, source_ip)
        if self._failed_proofs >= self._max_failed:
            self._close(CloseReason.TOO_MANY_FAILURES)
        return failure

    def _fail(
        self,
        code: ErrorCode,
        source_ip: str,
        *,
        retry_after_sec: float | None = None,
        count_against_ip: bool = True,
    ) -> PairingFailure:
        if count_against_ip:
            self._lockout.record_failure(source_ip)
        self._events.pair_failure(code, source_ip)
        return PairingFailure(code=code, retry_after_sec=retry_after_sec)


def _is_canonical_uuid(value: str) -> bool:
    """Whether ``value`` is a UUID in lowercase hyphenated form (one identity per device)."""
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _is_nonce(value: str) -> bool:
    """Whether ``value`` is unpadded base64url for exactly 16 bytes."""
    try:
        return len(b64url_decode(value)) == NONCE_BYTES
    except ValueError:
        return False


__all__ = [
    "COOLDOWN_SEC",
    "MAX_FAILED_PROOFS",
    "MAX_PENDING_CHALLENGES",
    "NONCE_BYTES",
    "WINDOW_SEC",
    "Challenge",
    "CloseReason",
    "OpenedWindow",
    "PairingEvents",
    "PairingFailure",
    "PairingSuccess",
    "PairingUnavailableError",
    "PairingWindow",
    "WindowState",
]
