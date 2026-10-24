"""Tests for ordered service lifecycle management."""

from __future__ import annotations

import asyncio

import pytest

from deckhand.core.errors import LifecycleError, ShutdownError, StartupError
from deckhand.core.lifecycle import LifecycleManager


class RecordingService:
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        fail_start: bool = False,
        fail_stop: bool = False,
        hang_start: bool = False,
        hang_stop: bool = False,
    ) -> None:
        self.name = name
        self.events = events
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.hang_start = hang_start
        self.hang_stop = hang_stop

    async def start(self) -> None:
        self.events.append(f"start:{self.name}")
        if self.hang_start:
            await asyncio.sleep(30)
        if self.fail_start:
            raise RuntimeError(f"{self.name} failed to start")

    async def stop(self) -> None:
        self.events.append(f"stop:{self.name}")
        if self.hang_stop:
            await asyncio.sleep(30)
        if self.fail_stop:
            raise RuntimeError(f"{self.name} failed to stop")


async def test_services_start_in_order_and_stop_in_reverse() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("a", RecordingService("a", events))
    manager.register("b", RecordingService("b", events))
    manager.register("c", RecordingService("c", events))

    await manager.start()
    assert events == ["start:a", "start:b", "start:c"]
    assert manager.started == ("a", "b", "c")

    await manager.stop()

    assert events == [
        "start:a",
        "start:b",
        "start:c",
        "stop:c",
        "stop:b",
        "stop:a",
    ]
    assert not manager.started


async def test_stop_without_start_is_a_noop() -> None:
    manager = LifecycleManager()
    await manager.stop()
    assert manager.started == ()


async def test_start_failure_rolls_back_started_services() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("a", RecordingService("a", events))
    manager.register("b", RecordingService("b", events, fail_start=True))
    manager.register("c", RecordingService("c", events))

    with pytest.raises(StartupError) as info:
        await manager.start()

    assert "b" in str(info.value)
    assert info.value.details == {"service": "b"}
    assert events == ["start:a", "start:b", "stop:a"]
    assert not manager.started


async def test_start_timeout_rolls_back_and_reports_timeout() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=0.01)
    manager.register("a", RecordingService("a", events))
    manager.register("slow", RecordingService("slow", events, hang_start=True))

    with pytest.raises(StartupError, match="timed out"):
        await manager.start()

    assert events == ["start:a", "start:slow", "stop:a"]
    assert manager.started == ()


async def test_rollback_stop_failure_does_not_mask_startup_error() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("bad-stop", RecordingService("bad-stop", events, fail_stop=True))
    manager.register("bad-start", RecordingService("bad-start", events, fail_start=True))

    with pytest.raises(StartupError, match="bad-start"):
        await manager.start()

    assert events == ["start:bad-stop", "start:bad-start", "stop:bad-stop"]


async def test_rollback_stop_timeout_is_swallowed() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=0.01)
    manager.register("slow-stop", RecordingService("slow-stop", events, hang_stop=True))
    manager.register("bad-start", RecordingService("bad-start", events, fail_start=True))

    with pytest.raises(StartupError, match="bad-start"):
        await manager.start()

    assert events == ["start:slow-stop", "start:bad-start", "stop:slow-stop"]


async def test_stop_continues_after_a_failure_and_aggregates() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("a", RecordingService("a", events))
    manager.register("b", RecordingService("b", events, fail_stop=True))
    manager.register("c", RecordingService("c", events))

    await manager.start()

    with pytest.raises(ShutdownError) as info:
        await manager.stop()

    assert "b" in str(info.value)
    assert info.value.details == {"services": "b"}
    assert events == [
        "start:a",
        "start:b",
        "start:c",
        "stop:c",
        "stop:b",
        "stop:a",
    ]
    assert manager.started == ()


async def test_stop_timeout_is_reported() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=0.01)
    manager.register("slow", RecordingService("slow", events, hang_stop=True))

    await manager.start()

    with pytest.raises(ShutdownError, match="failed to stop"):
        await manager.stop()


async def test_start_twice_is_rejected() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("a", RecordingService("a", events))

    await manager.start()

    with pytest.raises(LifecycleError, match="already running"):
        await manager.start()


async def test_can_restart_after_stopping() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    manager.register("a", RecordingService("a", events))

    await manager.start()
    await manager.stop()
    await manager.start()

    assert manager.started == ("a",)
    assert events == ["start:a", "stop:a", "start:a"]


async def test_registering_while_running_is_rejected() -> None:
    events: list[str] = []
    manager = LifecycleManager(timeout=1)
    await manager.start()

    with pytest.raises(LifecycleError, match="while running"):
        manager.register("late", RecordingService("late", events))


def test_invalid_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        LifecycleManager(timeout=0)


def test_duplicate_registration_is_rejected() -> None:
    manager = LifecycleManager()
    events: list[str] = []
    manager.register("a", RecordingService("a", events))

    with pytest.raises(ValueError, match="already registered"):
        manager.register("a", RecordingService("a", events))


def test_empty_service_name_is_rejected() -> None:
    manager = LifecycleManager()
    events: list[str] = []

    with pytest.raises(ValueError, match="must not be empty"):
        manager.register("", RecordingService("empty", events))


def test_services_can_omit_lifecycle_calls_until_started() -> None:
    manager = LifecycleManager()

    assert manager.started == ()
