"""Bounded ring buffer with monotonic sequence numbers.

Layer 0 (foundations).

Every appended value gets a sequence number that never repeats, even after the
buffer evicts old entries. Consumers remember the last sequence they saw and
call :meth:`RingBuffer.since` on reconnect: the returned :class:`Replay` says
whether entries were lost while they were away (gap detection), which is what
run-log replay needs.

Sequence numbers start at 0. :meth:`RingBuffer.clear` intentionally keeps the
counter moving so a later replay cannot mistake cleared data for a fresh stream.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

ValueT = TypeVar("ValueT")


@dataclass(frozen=True, slots=True)
class Entry(Generic[ValueT]):
    """A buffered value and the sequence number assigned when it arrived."""

    seq: int
    value: ValueT


@dataclass(frozen=True, slots=True)
class Replay(Generic[ValueT]):
    """Result of :meth:`RingBuffer.since`."""

    requested_seq: int
    oldest_seq: int | None
    entries: tuple[Entry[ValueT], ...]
    missed: int

    @property
    def complete(self) -> bool:
        """``True`` when no entries were evicted before ``requested_seq``."""
        return self.missed == 0


class RingBuffer(Generic[ValueT]):
    """Fixed-capacity buffer that evicts the oldest entry when full."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._items: deque[Entry[ValueT]] = deque(maxlen=capacity)
        self._next_seq = 0

    @property
    def capacity(self) -> int:
        """Maximum number of retained entries."""
        return self._capacity

    @property
    def first_seq(self) -> int | None:
        """Sequence number of the oldest retained entry, or ``None`` if empty."""
        return self._items[0].seq if self._items else None

    @property
    def last_seq(self) -> int | None:
        """Sequence number of the newest retained entry, or ``None`` if empty."""
        return self._items[-1].seq if self._items else None

    @property
    def next_seq(self) -> int:
        """Sequence number that the next appended entry will receive."""
        return self._next_seq

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Entry[ValueT]]:
        return iter(tuple(self._items))

    def append(self, value: ValueT) -> int:
        """Store ``value`` and return its sequence number."""
        entry = Entry(seq=self._next_seq, value=value)
        self._items.append(entry)
        self._next_seq += 1
        return entry.seq

    def at(self, seq: int) -> ValueT | None:
        """Return the value stored at ``seq``, or ``None`` if it is unavailable."""
        oldest = self.first_seq
        if oldest is None:
            return None
        offset = seq - oldest
        if 0 <= offset < len(self._items):
            return self._items[offset].value
        return None

    def since(self, seq: int) -> Replay[ValueT]:
        """Return retained entries with sequence number >= ``seq``.

        ``missed`` counts entries that were evicted before ``seq``, so callers
        can detect a gap instead of silently replaying a truncated log.
        """
        if seq < 0:
            raise ValueError("sequence numbers are non-negative")
        oldest = self.first_seq
        entries = tuple(entry for entry in self._items if entry.seq >= seq)
        missed = 0
        if oldest is not None and seq < oldest:
            missed = oldest - seq
        return Replay(
            requested_seq=seq,
            oldest_seq=oldest,
            entries=entries,
            missed=missed,
        )

    def clear(self) -> None:
        """Drop all entries without resetting the sequence counter."""
        self._items.clear()
