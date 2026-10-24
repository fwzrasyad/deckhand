"""ULID-style identifiers built on an injectable clock and RNG.

Layer 0 (foundations).

A ULID is 26 characters of Crockford base32: a 48-bit millisecond timestamp
(10 characters) followed by 80 bits of randomness (16 characters). Lexicographic
order therefore matches creation order, which later lets run IDs, log entries,
and audit records be sorted without parsing.

Everything is injectable so tests are deterministic: pass a
:class:`deckhand.core.clock.Clock` and a ``randbytes(n) -> bytes`` callable.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable

from deckhand.core.clock import Clock

ULID_LENGTH = 26
TIMESTAMP_LENGTH = 10
RANDOMNESS_LENGTH = 16
RANDOMNESS_BYTES = 10

CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
"""Crockford base32, excluding I, L, O, and U (ULID spec)."""

MAX_TIMESTAMP_MS = (1 << 48) - 1
_MAX_RANDOM = (1 << 80) - 1
_ALPHABET_INDEX = {character: index for index, character in enumerate(CROCKFORD_ALPHABET)}

RandomBytes = Callable[[int], bytes]


def _encode(value: int, length: int) -> str:
    """Encode ``value`` as ``length`` Crockford base32 characters."""
    characters: list[str] = []
    for _ in range(length):
        characters.append(CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(characters))


def _decode(text: str) -> int:
    """Decode a Crockford base32 string into an integer."""
    value = 0
    for character in text.upper():
        try:
            digit = _ALPHABET_INDEX[character]
        except KeyError:
            raise ValueError(f"invalid Crockford base32 character: {character!r}") from None
        value = (value << 5) | digit
    return value


def format_ulid(timestamp_ms: int, randomness: bytes) -> str:
    """Build a ULID string from a millisecond timestamp and 10 random bytes."""
    if not 0 <= timestamp_ms <= MAX_TIMESTAMP_MS:
        raise ValueError("timestamp_ms must fit in 48 bits")
    if len(randomness) != RANDOMNESS_BYTES:
        raise ValueError(f"randomness must be exactly {RANDOMNESS_BYTES} bytes")
    random_int = int.from_bytes(randomness, byteorder="big")
    return _encode(timestamp_ms, TIMESTAMP_LENGTH) + _encode(random_int, RANDOMNESS_LENGTH)


def timestamp_ms(ulid: str) -> int:
    """Return the millisecond timestamp encoded in ``ulid``."""
    if not is_valid(ulid):
        raise ValueError(f"not a valid ULID: {ulid!r}")
    return _decode(ulid[:TIMESTAMP_LENGTH].upper())


def is_valid(ulid: str) -> bool:
    """Return ``True`` if ``ulid`` is a well-formed 26-character ULID."""
    if len(ulid) != ULID_LENGTH:
        return False
    upper = ulid.upper()
    if not all(character in _ALPHABET_INDEX for character in upper):
        return False
    return _decode(upper[:TIMESTAMP_LENGTH]) <= MAX_TIMESTAMP_MS


class IdGenerator:
    """Generate strictly increasing ULIDs from an injectable clock and RNG.

    If the wall clock does not advance between two calls, the random component
    is incremented instead of re-drawn. That keeps IDs unique and ordered even
    on coarse clocks or when time appears to move backwards.
    """

    def __init__(self, clock: Clock, randbytes: RandomBytes = secrets.token_bytes) -> None:
        self._clock = clock
        self._randbytes = randbytes
        self._last_ms = -1
        self._last_random = -1

    def new(self) -> str:
        """Return the next ULID."""
        now_ms = int(self._clock.now() * 1000)
        now_ms = max(now_ms, self._last_ms)

        if now_ms == self._last_ms:
            random_int = self._last_random + 1
            if random_int > _MAX_RANDOM:
                raise OverflowError("ULID randomness exhausted for this millisecond")
        else:
            randomness = self._randbytes(RANDOMNESS_BYTES)
            if len(randomness) != RANDOMNESS_BYTES:
                raise ValueError(f"randbytes must return {RANDOMNESS_BYTES} bytes")
            random_int = int.from_bytes(randomness, byteorder="big")

        self._last_ms = now_ms
        self._last_random = random_int
        return _encode(now_ms, TIMESTAMP_LENGTH) + _encode(random_int, RANDOMNESS_LENGTH)


def new_ulid(clock: Clock, randbytes: RandomBytes = secrets.token_bytes) -> str:
    """Return a single ULID without cross-call ordering guarantees.

    Use :class:`IdGenerator` when IDs generated within the same millisecond
    must remain ordered.
    """
    randomness = randbytes(RANDOMNESS_BYTES)
    if len(randomness) != RANDOMNESS_BYTES:
        raise ValueError(f"randbytes must return {RANDOMNESS_BYTES} bytes")
    return format_ulid(int(clock.now() * 1000), randomness)
