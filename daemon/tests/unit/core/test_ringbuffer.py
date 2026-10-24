"""Tests for the bounded ring buffer and its sequence tracking."""

from __future__ import annotations

import pytest

from deckhand.core.ringbuffer import Entry, Replay, RingBuffer


def test_new_buffer_is_empty() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)

    assert len(buffer) == 0
    assert buffer.capacity == 3
    assert buffer.first_seq is None
    assert buffer.last_seq is None
    assert buffer.next_seq == 0
    assert list(buffer) == []


def test_appends_assign_increasing_sequence_numbers() -> None:
    buffer: RingBuffer[str] = RingBuffer(5)

    first = buffer.append("a")
    second = buffer.append("b")

    assert (first, second) == (0, 1)
    assert buffer.next_seq == 2
    assert buffer.first_seq == 0
    assert buffer.last_seq == 1
    assert list(buffer) == [Entry(0, "a"), Entry(1, "b")]


def test_oldest_entries_are_evicted_and_sequences_continue() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)
    for value in ["a", "b", "c", "d", "e"]:
        buffer.append(value)

    assert len(buffer) == 3
    assert buffer.first_seq == 2
    assert buffer.last_seq == 4
    assert buffer.next_seq == 5
    assert buffer.at(1) is None
    assert buffer.at(2) == "c"
    assert buffer.at(4) == "e"
    assert buffer.at(5) is None
    assert [entry.value for entry in buffer] == ["c", "d", "e"]


def test_at_on_empty_buffer_returns_none() -> None:
    buffer: RingBuffer[str] = RingBuffer(2)

    assert buffer.at(0) is None


def test_at_rejects_negative_sequence() -> None:
    buffer: RingBuffer[str] = RingBuffer(2)
    buffer.append("a")

    assert buffer.at(-1) is None


def test_since_returns_retained_entries_without_a_gap() -> None:
    buffer: RingBuffer[str] = RingBuffer(4)
    for value in ["a", "b", "c"]:
        buffer.append(value)

    replay = buffer.since(1)

    assert replay == Replay(
        requested_seq=1,
        oldest_seq=0,
        entries=(Entry(1, "b"), Entry(2, "c")),
        missed=0,
    )
    assert replay.complete is True


def test_since_reports_a_gap_after_eviction() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)
    for value in ["a", "b", "c", "d", "e"]:
        buffer.append(value)

    replay = buffer.since(0)

    assert [entry.seq for entry in replay.entries] == [2, 3, 4]
    assert replay.oldest_seq == 2
    assert replay.missed == 2
    assert replay.complete is False


def test_since_beyond_the_end_returns_nothing() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)
    buffer.append("a")

    replay = buffer.since(10)

    assert replay.entries == ()
    assert replay.missed == 0
    assert replay.complete is True


def test_since_on_empty_buffer_is_complete() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)

    replay = buffer.since(0)

    assert replay.entries == ()
    assert replay.oldest_seq is None
    assert replay.complete is True


def test_since_rejects_negative_sequence() -> None:
    buffer: RingBuffer[str] = RingBuffer(1)

    with pytest.raises(ValueError, match="non-negative"):
        buffer.since(-1)


def test_clear_drops_entries_but_not_the_sequence_counter() -> None:
    buffer: RingBuffer[str] = RingBuffer(3)
    buffer.append("a")
    buffer.append("b")

    buffer.clear()

    assert len(buffer) == 0
    assert buffer.first_seq is None
    assert buffer.next_seq == 2
    assert buffer.append("c") == 2
    assert buffer.since(2).entries == (Entry(2, "c"),)


def test_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RingBuffer(0)


def test_iteration_is_a_snapshot() -> None:
    buffer: RingBuffer[int] = RingBuffer(3)
    buffer.append(1)

    iterator = iter(buffer)
    buffer.append(2)

    assert list(iterator) == [Entry(0, 1)]
