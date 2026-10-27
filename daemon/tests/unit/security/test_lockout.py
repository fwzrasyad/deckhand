"""Per-source-IP lockout (SRD 4.7, SEC-010)."""

from __future__ import annotations

from typing import Any

import pytest

from deckhand.core.clock import FakeClock
from deckhand.security.lockout import (
    BASE_BLOCK_SEC,
    FAILURE_THRESHOLD,
    MAX_BLOCK_SEC,
    RESET_AFTER_SEC,
    LockoutStatus,
    LockoutTracker,
    normalize_address,
)

IP = "192.168.1.20"
OTHER_IP = "192.168.1.21"


def _fail(tracker: LockoutTracker, address: str, times: int) -> LockoutStatus:
    status = LockoutStatus(blocked=False)
    for _ in range(times):
        status = tracker.record_failure(address)
    return status


def _block_and_wait(clock: FakeClock, tracker: LockoutTracker, address: str) -> float:
    """Trigger one block, wait it out, and return its length."""
    status = tracker.record_failure(address)
    assert status.blocked
    clock.advance(status.retry_after)
    assert not tracker.check(address).blocked
    return status.retry_after


def test_spec_constants() -> None:
    assert FAILURE_THRESHOLD == 5
    assert BASE_BLOCK_SEC == 60.0
    assert MAX_BLOCK_SEC == 900.0
    assert RESET_AFTER_SEC == 3600.0


def test_unknown_address_is_not_blocked() -> None:
    tracker = LockoutTracker(FakeClock())

    assert tracker.check(IP) == LockoutStatus(blocked=False)
    assert len(tracker) == 0


def test_check_never_records_a_failure() -> None:
    tracker = LockoutTracker(FakeClock())

    for _ in range(20):
        tracker.check(IP)

    assert len(tracker) == 0


def test_first_four_failures_do_not_block() -> None:
    tracker = LockoutTracker(FakeClock())

    for _ in range(FAILURE_THRESHOLD - 1):
        assert tracker.record_failure(IP) == LockoutStatus(blocked=False)

    assert not tracker.check(IP).blocked


def test_fifth_failure_blocks_for_sixty_seconds() -> None:
    tracker = LockoutTracker(FakeClock())

    status = _fail(tracker, IP, FAILURE_THRESHOLD)

    assert status.blocked
    assert status.newly_blocked
    assert status.retry_after == pytest.approx(60.0)


def test_block_counts_down_and_then_ends() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD)

    clock.advance(45)
    during = tracker.check(IP)
    assert during.blocked
    assert not during.newly_blocked
    assert during.retry_after == pytest.approx(15.0)

    clock.advance(15)
    assert tracker.check(IP) == LockoutStatus(blocked=False)


def test_after_a_block_ends_one_failure_reblocks_with_double_the_time() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD)
    clock.advance(60)

    status = tracker.record_failure(IP)

    assert status.blocked
    assert status.newly_blocked
    assert status.retry_after == pytest.approx(120.0)


def test_block_length_doubles_up_to_fifteen_minutes() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD - 1)

    lengths = [_block_and_wait(clock, tracker, IP) for _ in range(8)]

    assert lengths == [60.0, 120.0, 240.0, 480.0, 900.0, 900.0, 900.0, 900.0]


def test_failures_during_a_block_are_ignored() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD)
    clock.advance(10)

    hammered = _fail(tracker, IP, 50)

    assert hammered.blocked
    assert not hammered.newly_blocked
    assert hammered.retry_after == pytest.approx(50.0)
    clock.advance(50)
    # Only one escalation happened: the next block is level two (120 s), not more.
    assert tracker.record_failure(IP).retry_after == pytest.approx(120.0)


def test_addresses_are_tracked_independently() -> None:
    tracker = LockoutTracker(FakeClock())

    _fail(tracker, IP, FAILURE_THRESHOLD)

    assert tracker.check(IP).blocked
    assert not tracker.check(OTHER_IP).blocked
    assert not tracker.record_failure(OTHER_IP).blocked


def test_streak_is_forgotten_after_an_hour_without_failures() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD)  # level 1 block
    clock.advance(RESET_AFTER_SEC)

    assert tracker.check(IP) == LockoutStatus(blocked=False)
    assert len(tracker) == 0
    # A clean slate: it takes five failures again, and the block is 60 s again.
    assert not _fail(tracker, IP, FAILURE_THRESHOLD - 1).blocked
    assert tracker.record_failure(IP).retry_after == pytest.approx(60.0)


def test_failures_less_than_an_hour_apart_keep_accumulating() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, FAILURE_THRESHOLD - 1)
    clock.advance(RESET_AFTER_SEC - 1)

    assert tracker.record_failure(IP).blocked


def test_quiet_period_is_measured_from_the_last_failure() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock)
    _fail(tracker, IP, 2)
    clock.advance(RESET_AFTER_SEC - 1)
    tracker.record_failure(IP)
    clock.advance(RESET_AFTER_SEC - 1)

    # Three failures are still on record, so two more reach the threshold.
    assert not tracker.record_failure(IP).blocked
    assert tracker.record_failure(IP).blocked


def test_custom_threshold_and_durations() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(
        clock, threshold=1, base_block_sec=2, max_block_sec=5, reset_after_sec=100
    )

    assert tracker.record_failure(IP).retry_after == pytest.approx(2.0)
    clock.advance(2)
    assert tracker.record_failure(IP).retry_after == pytest.approx(4.0)
    clock.advance(4)
    assert tracker.record_failure(IP).retry_after == pytest.approx(5.0)


def test_very_high_levels_stay_capped() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock, threshold=1, max_block_sec=900)

    for _ in range(40):
        status = tracker.record_failure(IP)
        assert status.retry_after <= 900
        clock.advance(status.retry_after)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.0.0.5", "10.0.0.5"),
        ("::ffff:10.0.0.5", "10.0.0.5"),
        ("fe80::1%eth0", "fe80::1"),
        ("FE80:0:0:0:0:0:0:1", "fe80::1"),
        ("::1", "::1"),
    ],
)
def test_normalize_address(raw: str, expected: str) -> None:
    assert normalize_address(raw) == expected


@pytest.mark.parametrize("raw", ["", "not-an-ip", "10.0.0.256", "10.0.0.5:4000", "10.0.0.5/24"])
def test_normalize_address_rejects_garbage_without_echoing_it(raw: str) -> None:
    with pytest.raises(ValueError, match="not a valid IP address") as caught:
        normalize_address(raw)

    assert raw not in str(caught.value) or raw == ""


def test_equivalent_spellings_share_one_streak() -> None:
    tracker = LockoutTracker(FakeClock())

    tracker.record_failure("10.0.0.5")
    tracker.record_failure("::ffff:10.0.0.5")
    tracker.record_failure("::FFFF:0a00:0005")
    tracker.record_failure("10.0.0.5")

    assert len(tracker) == 1
    assert tracker.record_failure("::ffff:10.0.0.5").blocked
    assert tracker.check("10.0.0.5").blocked


def test_invalid_address_is_rejected_by_every_entry_point() -> None:
    tracker = LockoutTracker(FakeClock())

    with pytest.raises(ValueError, match="not a valid IP"):
        tracker.check("nope")
    with pytest.raises(ValueError, match="not a valid IP"):
        tracker.record_failure("nope")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"threshold": 0},
        {"base_block_sec": 0},
        {"base_block_sec": 10, "max_block_sec": 5},
        {"reset_after_sec": 0},
        {"max_entries": 0},
    ],
)
def test_constructor_rejects_bad_settings(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"must|satisfy"):
        LockoutTracker(FakeClock(), **kwargs)


def test_table_is_bounded_and_forgets_quiet_addresses_first() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock, max_entries=3)
    for index in range(3):
        tracker.record_failure(f"10.0.0.{index}")
        clock.advance(1)
    clock.advance(RESET_AFTER_SEC)  # all three are now quiet

    tracker.record_failure("10.0.0.9")

    assert len(tracker) == 1


def test_full_table_evicts_oldest_unblocked_and_keeps_blocked_entries() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock, max_entries=3)
    _fail(tracker, "10.0.0.1", FAILURE_THRESHOLD)  # blocked
    clock.advance(1)
    tracker.record_failure("10.0.0.2")  # oldest unblocked
    clock.advance(1)
    tracker.record_failure("10.0.0.3")
    clock.advance(1)

    tracker.record_failure("10.0.0.4")

    assert len(tracker) == 3
    assert tracker.check("10.0.0.1").blocked  # the blocked one survived
    # 10.0.0.2 was evicted, so it starts from zero again.
    assert not _fail(tracker, "10.0.0.2", FAILURE_THRESHOLD - 1).blocked


def test_full_table_of_blocked_entries_evicts_the_one_ending_soonest() -> None:
    clock = FakeClock()
    tracker = LockoutTracker(clock, max_entries=2)
    _fail(tracker, "10.0.0.1", FAILURE_THRESHOLD)  # ends at t=60
    clock.advance(5)
    _fail(tracker, "10.0.0.2", FAILURE_THRESHOLD)  # ends at t=65

    tracker.record_failure("10.0.0.3")

    assert len(tracker) == 2
    assert not tracker.check("10.0.0.1").blocked
    assert tracker.check("10.0.0.2").blocked
