"""Per-source-IP failure tracking with escalating blocks (SRD 4.7, SEC-010).

Layer 2. Five failures from one source address block that address for 60 s.
After a block ends the next single failure blocks it again for twice as long,
up to 15 minutes. An address that has not failed for an hour is forgotten.

Behavior the SRD leaves open, recorded in ``docs/security/pairing.md``:

* Failures reported for an address that is already blocked are ignored, so an
  attacker cannot extend or escalate a block by hammering through it.
* A successful authentication does not reset the streak; only an hour without
  failures does.
* Failures accumulate with no sliding window.

The tracker runs on an injectable :class:`~deckhand.core.clock.Clock`, keeps
its state on the instance, and is driven from one event loop (not thread-safe).
It stores only addresses and counters, never credentials.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Final

from deckhand.core.clock import Clock

FAILURE_THRESHOLD: Final[int] = 5
BASE_BLOCK_SEC: Final[float] = 60.0
MAX_BLOCK_SEC: Final[float] = 900.0
RESET_AFTER_SEC: Final[float] = 3600.0
DEFAULT_MAX_ENTRIES: Final[int] = 4096

_MAX_DOUBLINGS: Final[int] = 16  # keeps 2**n small; the cap is reached far earlier


@dataclass(frozen=True, slots=True)
class LockoutStatus:
    """Whether a source address is currently blocked."""

    blocked: bool
    retry_after: float = 0.0
    """Seconds until the block ends; ``0.0`` when not blocked."""
    newly_blocked: bool = False
    """True only on the call whose failure started a block."""


@dataclass(slots=True)
class _Entry:
    failures: int = 0
    level: int = 0
    blocked_until: float = 0.0
    last_failure: float = 0.0


def normalize_address(address: str) -> str:
    """Return the canonical key for a source address.

    IPv4-mapped IPv6 addresses collapse to their IPv4 form and IPv6 scope ids
    are dropped, so one host cannot split its failures across spellings.

    Raises:
        ValueError: ``address`` is not an IP address.
    """
    try:
        parsed: ipaddress.IPv4Address | ipaddress.IPv6Address = ipaddress.ip_address(address)
    except ValueError:
        raise ValueError("source address is not a valid IP address") from None
    if isinstance(parsed, ipaddress.IPv6Address):
        mapped = parsed.ipv4_mapped
        parsed = mapped if mapped is not None else ipaddress.IPv6Address(int(parsed))
    return str(parsed)


class LockoutTracker:
    """Escalating per-source-IP blocks for failed auth and pairing attempts."""

    def __init__(
        self,
        clock: Clock,
        *,
        threshold: int = FAILURE_THRESHOLD,
        base_block_sec: float = BASE_BLOCK_SEC,
        max_block_sec: float = MAX_BLOCK_SEC,
        reset_after_sec: float = RESET_AFTER_SEC,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> None:
        if threshold < 1:
            raise ValueError("threshold must be at least 1")
        if base_block_sec <= 0 or max_block_sec < base_block_sec:
            raise ValueError("block durations must satisfy 0 < base <= max")
        if reset_after_sec <= 0:
            raise ValueError("reset_after_sec must be positive")
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._clock = clock
        self._threshold = threshold
        self._base = base_block_sec
        self._max = max_block_sec
        self._reset_after = reset_after_sec
        self._max_entries = max_entries
        self._entries: dict[str, _Entry] = {}

    def __len__(self) -> int:
        """Number of addresses currently tracked."""
        return len(self._entries)

    def check(self, address: str) -> LockoutStatus:
        """Return the block status of ``address`` without recording anything."""
        key = normalize_address(address)
        now = self._clock.monotonic()
        entry = self._live_entry(key, now)
        if entry is None:
            return LockoutStatus(blocked=False)
        return self._status(entry, now)

    def record_failure(self, address: str) -> LockoutStatus:
        """Record one failed attempt and return the resulting status.

        A failure from an address that is already blocked changes nothing.
        """
        key = normalize_address(address)
        now = self._clock.monotonic()
        entry = self._live_entry(key, now)
        if entry is not None:
            current = self._status(entry, now)
            if current.blocked:
                return current
        else:
            self._make_room(now)
            entry = self._entries.setdefault(key, _Entry())

        entry.failures += 1
        entry.last_failure = now
        if entry.failures < self._threshold:
            return LockoutStatus(blocked=False)

        entry.level += 1
        entry.blocked_until = now + self._block_duration(entry.level)
        return LockoutStatus(
            blocked=True,
            retry_after=entry.blocked_until - now,
            newly_blocked=True,
        )

    def _block_duration(self, level: int) -> float:
        doublings = min(level - 1, _MAX_DOUBLINGS)
        return min(self._base * float(1 << doublings), self._max)

    def _status(self, entry: _Entry, now: float) -> LockoutStatus:
        if entry.blocked_until > now:
            return LockoutStatus(blocked=True, retry_after=entry.blocked_until - now)
        return LockoutStatus(blocked=False)

    def _live_entry(self, key: str, now: float) -> _Entry | None:
        """Return the entry for ``key``, forgetting it if it has gone quiet."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        if self._is_stale(entry, now):
            del self._entries[key]
            return None
        return entry

    def _is_stale(self, entry: _Entry, now: float) -> bool:
        return entry.blocked_until <= now and now - entry.last_failure >= self._reset_after

    def _make_room(self, now: float) -> None:
        """Keep the table bounded before a new address is added."""
        if len(self._entries) < self._max_entries:
            return
        for key in [k for k, e in self._entries.items() if self._is_stale(e, now)]:
            del self._entries[key]
        if len(self._entries) < self._max_entries:
            return
        # Still full: forget the entry that matters least. Unblocked entries go
        # first (oldest failure first); if every entry is blocked, drop the one
        # whose block ends soonest.
        idle = [(e.last_failure, k) for k, e in self._entries.items() if e.blocked_until <= now]
        if idle:
            del self._entries[min(idle)[1]]
            return
        soonest = min((e.blocked_until, k) for k, e in self._entries.items())
        del self._entries[soonest[1]]


__all__ = [
    "BASE_BLOCK_SEC",
    "DEFAULT_MAX_ENTRIES",
    "FAILURE_THRESHOLD",
    "MAX_BLOCK_SEC",
    "RESET_AFTER_SEC",
    "LockoutStatus",
    "LockoutTracker",
    "normalize_address",
]
