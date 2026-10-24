"""Tests for the token-bucket rate limiter."""

from __future__ import annotations

import math

import pytest

from deckhand.core.clock import FakeClock
from deckhand.core.errors import RateLimitError
from deckhand.core.ratelimit import TokenBucket


def test_burst_uses_full_capacity_then_denies() -> None:
    bucket = TokenBucket(capacity=3, refill_rate=1, clock=FakeClock())

    results = [bucket.try_acquire() for _ in range(3)]

    assert results == [True, True, True]
    assert bucket.try_acquire() is False
    assert bucket.available == 0


def test_refills_continuously() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=10, refill_rate=2, clock=clock)

    assert bucket.try_acquire(10) is True
    clock.advance(1.5)

    assert bucket.available == pytest.approx(3.0)
    assert bucket.try_acquire(3) is True
    assert bucket.try_acquire() is False


def test_refill_is_clamped_to_capacity() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=4, refill_rate=5, clock=clock, initial=1)

    clock.advance(100)

    assert bucket.available == 4
    assert bucket.try_acquire(4) is True


def test_fractional_requests_are_supported() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, clock=clock, initial=0)

    clock.advance(2.5)

    assert bucket.try_acquire(2.5) is True
    assert bucket.available == pytest.approx(0.0)


def test_acquire_raises_with_retry_hint() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_rate=1, clock=clock, initial=0)
    clock.advance(0.5)

    with pytest.raises(RateLimitError) as info:
        bucket.acquire()

    assert info.value.details["retry_after"] == pytest.approx(0.5)
    assert "0.500" in str(info.value)


def test_acquire_succeeds_when_tokens_are_available() -> None:
    bucket = TokenBucket(capacity=1, refill_rate=1, clock=FakeClock())

    bucket.acquire()

    assert bucket.try_acquire() is False


def test_retry_after_is_zero_when_available() -> None:
    bucket = TokenBucket(capacity=2, refill_rate=1, clock=FakeClock())

    assert bucket.retry_after() == 0.0


def test_retry_after_is_infinite_without_refill() -> None:
    bucket = TokenBucket(capacity=2, refill_rate=0, clock=FakeClock(), initial=0)

    assert bucket.retry_after() == math.inf


def test_time_at_same_monotonic_instant_does_not_refill() -> None:
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_rate=10, clock=clock, initial=0)

    assert bucket.available == 0
    assert bucket.try_acquire() is False


def test_capacity_and_rate_are_exposed() -> None:
    bucket = TokenBucket(capacity=7, refill_rate=1, clock=FakeClock())

    assert bucket.capacity == 7


@pytest.mark.parametrize(
    ("capacity", "refill_rate", "initial", "message"),
    [
        (0, 1.0, None, "capacity"),
        (-1, 1.0, None, "capacity"),
        (1, -1.0, None, "refill_rate"),
        (1, 1.0, -0.1, "initial"),
        (1, 1.0, 2.0, "initial"),
    ],
)
def test_constructor_validation(
    capacity: float,
    refill_rate: float,
    initial: float | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        TokenBucket(capacity=capacity, refill_rate=refill_rate, clock=FakeClock(), initial=initial)


@pytest.mark.parametrize("tokens", [0.0, -1.0, 4.0])
def test_request_validation(tokens: float) -> None:
    bucket = TokenBucket(capacity=3, refill_rate=1, clock=FakeClock())

    with pytest.raises(ValueError):
        bucket.try_acquire(tokens)
    with pytest.raises(ValueError):
        bucket.retry_after(tokens)
