"""Tests for ULID-style identifier generation."""

from __future__ import annotations

import pytest

from deckhand.core.clock import FakeClock
from deckhand.core.ids import (
    CROCKFORD_ALPHABET,
    ULID_LENGTH,
    IdGenerator,
    format_ulid,
    is_valid,
    new_ulid,
    timestamp_ms,
)

EPOCH = 1_700_000_000.0
ZEROS = b"\x00" * 10
MAX_RANDOM_BYTES = b"\xff" * 10


def test_format_ulid_has_expected_shape() -> None:
    value = format_ulid(1_700_000_000_000, ZEROS)

    assert len(value) == ULID_LENGTH
    assert set(value) <= set(CROCKFORD_ALPHABET)
    assert is_valid(value)
    assert timestamp_ms(value) == 1_700_000_000_000


def test_format_ulid_roundtrips_max_timestamp() -> None:
    value = format_ulid((1 << 48) - 1, MAX_RANDOM_BYTES)

    assert is_valid(value)
    assert timestamp_ms(value) == (1 << 48) - 1
    assert value == "7" + "Z" * 25


def test_format_ulid_rejects_bad_timestamp() -> None:
    with pytest.raises(ValueError, match="48 bits"):
        format_ulid(-1, ZEROS)
    with pytest.raises(ValueError, match="48 bits"):
        format_ulid(1 << 48, ZEROS)


def test_format_ulid_rejects_wrong_randomness_length() -> None:
    with pytest.raises(ValueError, match="10 bytes"):
        format_ulid(1, b"\x00")


def test_generator_is_deterministic_for_fixed_inputs() -> None:
    clock = FakeClock(epoch=EPOCH)

    first = IdGenerator(clock, lambda _: ZEROS).new()
    second = IdGenerator(clock, lambda _: ZEROS).new()

    assert first == second
    assert timestamp_ms(first) == int(EPOCH * 1000)


def test_generator_increments_randomness_within_same_millisecond() -> None:
    clock = FakeClock(epoch=EPOCH)
    generator = IdGenerator(clock, lambda _: ZEROS)

    ids = [generator.new() for _ in range(3)]

    assert ids == sorted(ids)
    assert len(set(ids)) == 3
    assert all(timestamp_ms(value) == int(EPOCH * 1000) for value in ids)


def test_generator_orders_across_milliseconds() -> None:
    clock = FakeClock(epoch=EPOCH)
    generator = IdGenerator(clock, lambda _: MAX_RANDOM_BYTES)

    first = generator.new()
    clock.advance(0.001)
    second = generator.new()

    assert first < second
    assert timestamp_ms(second) - timestamp_ms(first) == 1


def test_generator_survives_a_backwards_wall_clock() -> None:
    clock = FakeClock(epoch=EPOCH)
    generator = IdGenerator(clock, lambda _: ZEROS)

    first = generator.new()
    clock.set_epoch(EPOCH - 10)
    second = generator.new()

    assert first < second
    assert timestamp_ms(second) == timestamp_ms(first)


def test_generator_rejects_short_randomness() -> None:
    generator = IdGenerator(FakeClock(), lambda _: b"\x00")

    with pytest.raises(ValueError, match="10 bytes"):
        generator.new()


def test_generator_raises_when_randomness_is_exhausted() -> None:
    clock = FakeClock(epoch=EPOCH)
    generator = IdGenerator(clock, lambda _: MAX_RANDOM_BYTES)

    generator.new()

    with pytest.raises(OverflowError, match="exhausted"):
        generator.new()


def test_new_ulid_uses_the_clock() -> None:
    clock = FakeClock(epoch=EPOCH)

    value = new_ulid(clock, lambda _: ZEROS)

    assert is_valid(value)
    assert timestamp_ms(value) == int(EPOCH * 1000)


def test_new_ulid_rejects_short_randomness() -> None:
    with pytest.raises(ValueError, match="10 bytes"):
        new_ulid(FakeClock(), lambda _: b"\x00")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-a-ulid",
        "0" * 25,
        "0" * 27,
        "0" * 25 + "I",
        "0" * 25 + "u",
        "8" * 26,  # timestamp overflows 48 bits, but characters are valid
    ],
)
def test_is_valid_rejects_malformed_values(value: str) -> None:
    assert not is_valid(value)


def test_is_valid_accepts_lowercase() -> None:
    assert is_valid(format_ulid(1, ZEROS).lower())


def test_timestamp_ms_rejects_malformed_value() -> None:
    with pytest.raises(ValueError, match="not a valid ULID"):
        timestamp_ms("nope")
