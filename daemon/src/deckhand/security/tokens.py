"""Device token generation, storage hashing and constant-time verification.

Layer 2. Tokens are 256-bit random values shown to the phone exactly once
(SEC-008). The daemon stores only the lowercase hex SHA-256 hash; the plaintext
is never retained, logged, or included in exception messages.

This module has no mutable module-level state and performs no I/O.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from typing import Final

TOKEN_BYTES: Final[int] = 32
TOKEN_HEX_LENGTH: Final[int] = TOKEN_BYTES * 2


def generate_token(rng: Callable[[int], bytes] | None = None) -> str:
    """Return a new 256-bit device token as 64 lowercase hex characters.

    ``rng`` is injectable for tests and must return the requested number of
    random bytes; it defaults to ``secrets.token_bytes``.
    """
    source = secrets.token_bytes if rng is None else rng
    raw = source(TOKEN_BYTES)
    if len(raw) != TOKEN_BYTES:
        raise ValueError(f"random source must return {TOKEN_BYTES} bytes")
    return raw.hex()


def hash_token(token: str) -> str:
    """Return the SHA-256 hash to store for a token.

    The plaintext token is not returned, stored, or included in any error.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_sha256: str) -> bool:
    """Return whether a presented token matches the stored hash.

    The comparison uses ``hmac.compare_digest`` and never compares plaintext
    tokens or hashes with ``==``.
    """
    computed = hash_token(token)
    return hmac.compare_digest(computed.encode("ascii"), token_sha256.encode("utf-8"))


__all__ = [
    "TOKEN_BYTES",
    "TOKEN_HEX_LENGTH",
    "generate_token",
    "hash_token",
    "verify_token",
]
