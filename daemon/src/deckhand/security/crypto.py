"""Pairing cryptography: secrets, fingerprints, transcripts and HMAC proofs.

Layer 2. This module is pure computation with no I/O and no mutable module
state. It mirrors SRD 4.4 exactly so the daemon and the Dart app can be tested
against the same vectors in ``protocol/test_vectors/pairing.json``.

Definitions (SRD 4.4):

* ``fp`` is the lowercase hex SHA-256 of the daemon certificate in DER form.
* ``K`` is the normalized pairing secret encoded as ASCII bytes.
* ``transcript(role)`` is
  ``deckhand-pair-v1|<role>|<fp>|<client_nonce>|<server_nonce>|<device_id>``.
* A proof is the unpadded base64url encoding of
  ``HMAC-SHA256(K, transcript(role))``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from collections.abc import Callable
from typing import Final, Literal

from deckhand.core.errors import DeckhandError

Role = Literal["client", "server"]

CROCKFORD_ALPHABET: Final[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
SECRET_LENGTH: Final[int] = 12

_PAIRING_PREFIX: Final[str] = "deckhand-pair-v1"
_ROLES: Final[frozenset[str]] = frozenset({"client", "server"})
_BASE64URL_ALPHABET: Final[frozenset[str]] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
)
_SECRET_RANDOM_BYTES: Final[int] = 8  # 64 bits, of which the top 60 are used


class InvalidSecretError(DeckhandError, ValueError):
    """A pairing secret is not a valid 12-character Crockford Base32 code."""


def _random_source(rng: Callable[[int], bytes] | None) -> Callable[[int], bytes]:
    """Return the injected random source, or the ``secrets`` default."""
    return secrets.token_bytes if rng is None else rng


def generate_pairing_secret(rng: Callable[[int], bytes] | None = None) -> str:
    """Return 60 random bits as ``XXXX-XXXX-XXXX`` Crockford Base32.

    ``rng`` is injectable for tests and must return the requested number of
    random bytes; it defaults to ``secrets.token_bytes`` (SRD 4.4).
    """
    source = _random_source(rng)
    raw = source(_SECRET_RANDOM_BYTES)
    if len(raw) != _SECRET_RANDOM_BYTES:
        raise ValueError(f"random source must return {_SECRET_RANDOM_BYTES} bytes")
    value = int.from_bytes(raw, "big") >> 4  # keep exactly 60 uniform bits
    chars = "".join(
        CROCKFORD_ALPHABET[(value >> (5 * (SECRET_LENGTH - 1 - index))) & 0x1F]
        for index in range(SECRET_LENGTH)
    )
    return f"{chars[:4]}-{chars[4:8]}-{chars[8:]}"


def normalize_secret(text: str) -> str:
    """Return the canonical 12-character form of a typed pairing secret.

    Uppercases, strips all whitespace and hyphens, and maps the Crockford
    look-alikes ``I``/``L`` to ``1`` and ``O`` to ``0`` (SRD 4.4).

    Raises:
        InvalidSecretError: the normalized text is not exactly 12 characters or
            contains a character outside the Crockford Base32 alphabet.
    """
    normalized = "".join(char for char in text.upper() if char != "-" and not char.isspace())
    normalized = normalized.replace("I", "1").replace("L", "1").replace("O", "0")
    if len(normalized) != SECRET_LENGTH:
        raise InvalidSecretError(
            f"pairing secret must be {SECRET_LENGTH} characters after normalization"
        )
    invalid = sorted({char for char in normalized if char not in CROCKFORD_ALPHABET})
    if invalid:
        rendered = ", ".join(repr(char) for char in invalid)
        raise InvalidSecretError(f"pairing secret contains invalid characters: {rendered}")
    return normalized


def fingerprint(cert_der: bytes) -> str:
    """Return the lowercase hex SHA-256 of a DER-encoded certificate (SEC-006)."""
    return hashlib.sha256(cert_der).hexdigest()


def transcript(
    role: Role,
    fp: str,
    client_nonce: str,
    server_nonce: str,
    device_id: str,
) -> str:
    """Return the exact UTF-8 transcript string covered by a pairing proof."""
    if role not in _ROLES:
        raise ValueError(f"unknown pairing role: {role!r}")
    return f"{_PAIRING_PREFIX}|{role}|{fp}|{client_nonce}|{server_nonce}|{device_id}"


def b64url_encode(data: bytes) -> str:
    """Return unpadded base64url for ``data``; ``=`` is never emitted."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(text: str) -> bytes:
    """Decode unpadded base64url, rejecting padding and non-alphabet input."""
    if "=" in text:
        raise ValueError("base64url input must not be padded")
    if any(char not in _BASE64URL_ALPHABET for char in text):
        raise ValueError("base64url input contains characters outside the alphabet")
    if len(text) % 4 == 1:
        raise ValueError("base64url input has an impossible length")
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def compute_proof(
    secret: str,
    role: Role,
    fp: str,
    client_nonce: str,
    server_nonce: str,
    device_id: str,
) -> str:
    """Return the unpadded base64url proof for one side of a pairing.

    ``secret`` may be typed or already normalized; it is normalized here, so
    ``K`` always matches the canonical form defined by SRD 4.4.
    """
    key = normalize_secret(secret).encode("ascii")
    message = transcript(role, fp, client_nonce, server_nonce, device_id).encode("utf-8")
    return b64url_encode(hmac.new(key, message, hashlib.sha256).digest())


def verify_proof(
    secret: str,
    role: Role,
    fp: str,
    client_nonce: str,
    server_nonce: str,
    device_id: str,
    proof: str,
) -> bool:
    """Return whether ``proof`` matches, using a constant-time comparison.

    Malformed base64url input simply fails verification; it is never echoed in
    the result or in an exception.
    """
    expected = compute_proof(secret, role, fp, client_nonce, server_nonce, device_id)
    try:
        provided = b64url_decode(proof)
    except ValueError:
        return False
    return hmac.compare_digest(b64url_decode(expected), provided)


__all__ = [
    "CROCKFORD_ALPHABET",
    "SECRET_LENGTH",
    "InvalidSecretError",
    "Role",
    "b64url_decode",
    "b64url_encode",
    "compute_proof",
    "fingerprint",
    "generate_pairing_secret",
    "normalize_secret",
    "transcript",
    "verify_proof",
]
