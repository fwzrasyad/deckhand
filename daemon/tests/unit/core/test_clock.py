"""Tests for the injectable clock."""

from __future__ import annotations

import time

import pytest

from deckhand.core.clock import Clock, FakeClock, SystemClock


def test_system_clock_reads_real_time() -> None:
    clock = SystemClock()

    before = time.time()
    now = clock.now()
    after = time.time()

    assert before <= now <= after
    assert clock.monotonic() >= 0
    clock.sleep(0)
    assert isinstance(clock, Clock)


def test_system_clock_rejects_negative_sleep() -> None:
    with pytest.raises(ValueError, match="negative"):
        SystemClock().sleep(-0.5)


def test_fake_clock_starts_where_asked() -> None:
    clock = FakeClock(epoch=1000.0, monotonic=5.0)

    assert clock.now() == 1000.0
    assert clock.monotonic() == 5.0
    assert clock.sleeps == []


def test_fake_clock_advance_moves_both_clocks() -> None:
    clock = FakeClock(epoch=1000.0, monotonic=5.0)

    clock.advance(2.5)

    assert clock.now() == 1002.5
    assert clock.monotonic() == 7.5


def test_fake_clock_sleep_advances_and_records() -> None:
    clock = FakeClock(epoch=1000.0, monotonic=0.0)

    clock.sleep(1.5)
    clock.sleep(0.5)

    assert clock.monotonic() == 2.0
    assert clock.sleeps == [1.5, 0.5]


def test_fake_clock_cannot_move_backwards() -> None:
    clock = FakeClock()

    with pytest.raises(ValueError, match="backwards"):
        clock.advance(-1)
    with pytest.raises(ValueError, match="backwards"):
        clock.sleep(-1)

    assert clock.monotonic() == 0.0


def test_fake_clock_set_epoch_only_touches_wall_clock() -> None:
    clock = FakeClock(epoch=1000.0, monotonic=42.0)

    clock.set_epoch(2000.0)

    assert clock.now() == 2000.0
    assert clock.monotonic() == 42.0
