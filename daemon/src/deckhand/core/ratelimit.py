"""Token-bucket rate limiting on an injectable clock.

Layer 0 (foundations).

A bucket holds at most ``capacity`` tokens and refills continuously at
``refill_rate`` tokens per second. A burst of up to ``capacity`` requests is
allowed after an idle period; sustained throughput converges on the refill
rate. The bucket is not thread-safe: the daemon drives it from one event loop.
"""

from __future__ import annotations

import math

from deckhand.core.clock import Clock
from deckhand.core.errors import RateLimitError


class TokenBucket:
    """Continuously refilling bucket with a hard burst ceiling."""

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        clock: Clock,
        *,
        initial: float | None = None,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate < 0:
            raise ValueError("refill_rate must not be negative")
        tokens = capacity if initial is None else initial
        if not 0 <= tokens <= capacity:
            raise ValueError("initial tokens must be between 0 and capacity")

        self._capacity = float(capacity)
        self._refill_rate = float(refill_rate)
        self._clock = clock
        self._tokens = float(tokens)
        self._last_refill = clock.monotonic()

    @property
    def capacity(self) -> float:
        """Maximum number of tokens the bucket can hold."""
        return self._capacity

    @property
    def available(self) -> float:
        """Tokens currently available, after refilling."""
        self._refill()
        return self._tokens

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Take ``tokens`` if available; return whether the request succeeded."""
        self._validate_request(tokens)
        self._refill()
        if self._tokens < tokens:
            return False
        self._tokens -= tokens
        return True

    def acquire(self, tokens: float = 1.0) -> None:
        """Take ``tokens`` or raise :class:`RateLimitError`."""
        if self.try_acquire(tokens):
            return
        retry_after = self.retry_after(tokens)
        raise RateLimitError(
            f"rate limit exceeded; retry in {retry_after:.3f}s",
            details={"retry_after": retry_after},
        )

    def retry_after(self, tokens: float = 1.0) -> float:
        """Seconds until ``tokens`` can be taken, or ``inf`` if never."""
        self._validate_request(tokens)
        self._refill()
        if self._tokens >= tokens:
            return 0.0
        if self._refill_rate == 0:
            return math.inf
        return (tokens - self._tokens) / self._refill_rate

    def _refill(self) -> None:
        now = self._clock.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now

    def _validate_request(self, tokens: float) -> None:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self._capacity:
            raise ValueError("request exceeds bucket capacity")
