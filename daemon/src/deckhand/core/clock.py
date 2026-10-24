"""Injectable clock so time-dependent logic is testable (SRD 12.1).

Layer 0 (foundations).

Two notions of time are exposed:

* ``now()`` -- wall-clock time as POSIX seconds since the epoch.
* ``monotonic()`` -- a non-decreasing clock suitable for measuring durations.

Use ``monotonic()`` for timeouts, rate limiters, and retry backoff; use
``now()`` only where a human-visible or persistent timestamp is required.
"""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Read and wait on time without touching the real clock in tests."""

    def now(self) -> float:
        """Return wall-clock time as POSIX seconds since the epoch."""
        ...  # pragma: no cover - protocol declaration

    def monotonic(self) -> float:
        """Return a monotonically non-decreasing time in seconds."""
        ...  # pragma: no cover - protocol declaration

    def sleep(self, seconds: float) -> None:
        """Block for ``seconds`` seconds."""
        ...  # pragma: no cover - protocol declaration


class SystemClock:
    """Production :class:`Clock` backed by :mod:`time`."""

    def now(self) -> float:
        """Return wall-clock time as POSIX seconds since the epoch."""
        return time.time()

    def monotonic(self) -> float:
        """Return a monotonically non-decreasing time in seconds."""
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        """Sleep for ``seconds`` seconds."""
        if seconds < 0:
            raise ValueError("sleep duration must not be negative")
        time.sleep(seconds)


class FakeClock:
    """Deterministic clock for tests; time only moves when told to.

    ``advance`` moves both the wall clock and the monotonic clock, mirroring
    the real world. ``set_epoch`` changes only the wall clock, which is handy
    for simulating clock skew. Recorded sleeps are available in ``sleeps`` so
    tests can assert on backoff without waiting.
    """

    def __init__(
        self,
        *,
        epoch: float = 1_700_000_000.0,
        monotonic: float = 0.0,
    ) -> None:
        self._epoch = epoch
        self._monotonic = monotonic
        self.sleeps: list[float] = []

    def now(self) -> float:
        """Return the simulated wall-clock time."""
        return self._epoch

    def monotonic(self) -> float:
        """Return the simulated monotonic time."""
        return self._monotonic

    def sleep(self, seconds: float) -> None:
        """Advance the simulated clock instead of blocking."""
        self.advance(seconds)
        self.sleeps.append(seconds)

    def advance(self, seconds: float) -> None:
        """Move both clocks forward by ``seconds``."""
        if seconds < 0:
            raise ValueError("cannot move a clock backwards")
        self._epoch += seconds
        self._monotonic += seconds

    def set_epoch(self, epoch: float) -> None:
        """Jump the wall clock without affecting the monotonic clock."""
        self._epoch = epoch
