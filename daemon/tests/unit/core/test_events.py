"""Tests for the in-process event bus."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import pytest

from deckhand.core.events import EventBus, Subscription


@dataclass(frozen=True)
class BaseEvent:
    value: int


@dataclass(frozen=True)
class ChildEvent(BaseEvent):
    pass


@dataclass(frozen=True)
class OtherEvent:
    value: int


async def test_publish_delivers_to_matching_handlers() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)

    subscription = bus.subscribe(BaseEvent, handler)
    delivered = await bus.publish(BaseEvent(1))

    assert delivered == 1
    assert received == [BaseEvent(1)]
    assert bus.subscription_count == 1
    assert subscription.id == 0
    assert isinstance(subscription, Subscription)


async def test_base_class_subscription_receives_subclasses() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []
    bus.subscribe(BaseEvent, received.append)

    await bus.publish(ChildEvent(2))
    await bus.publish(OtherEvent(3))

    assert received == [ChildEvent(2)]


async def test_async_handlers_are_awaited_in_registration_order() -> None:
    bus = EventBus()
    events: list[str] = []

    async def first(event: BaseEvent) -> None:
        await asyncio.sleep(0)
        events.append(f"first:{event.value}")

    def second(event: BaseEvent) -> None:
        events.append(f"second:{event.value}")

    bus.subscribe(BaseEvent, first)
    bus.subscribe(BaseEvent, second)

    delivered = await bus.publish(BaseEvent(7))

    assert delivered == 2
    assert events == ["first:7", "second:7"]


async def test_failing_handler_does_not_block_others(
    caplog: pytest.LogCaptureFixture,
) -> None:
    bus = EventBus()
    received: list[BaseEvent] = []

    def broken(event: BaseEvent) -> None:
        raise RuntimeError("handler exploded")

    bus.subscribe(BaseEvent, broken)
    bus.subscribe(BaseEvent, received.append)

    with caplog.at_level(logging.ERROR, logger="deckhand.core.events"):
        delivered = await bus.publish(BaseEvent(1))

    assert delivered == 2
    assert received == [BaseEvent(1)]
    assert "handler exploded" in caplog.text


async def test_async_handler_failure_is_isolated() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []

    async def broken(event: BaseEvent) -> None:
        raise ValueError("async failure")

    bus.subscribe(BaseEvent, broken)
    bus.subscribe(BaseEvent, received.append)

    assert await bus.publish(BaseEvent(2)) == 2
    assert received == [BaseEvent(2)]


async def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []
    subscription = bus.subscribe(BaseEvent, received.append)

    assert bus.unsubscribe(subscription) is True
    assert bus.unsubscribe(subscription) is False
    assert bus.subscription_count == 0
    assert await bus.publish(BaseEvent(1)) == 0
    assert received == []


async def test_clear_removes_every_subscription() -> None:
    bus = EventBus()
    bus.subscribe(BaseEvent, lambda _: None)
    bus.subscribe(OtherEvent, lambda _: None)

    bus.clear()

    assert bus.subscription_count == 0
    assert await bus.publish(BaseEvent(1)) == 0


async def test_publish_uses_a_snapshot() -> None:
    bus = EventBus()
    received: list[str] = []

    def first(event: BaseEvent) -> None:
        received.append("first")
        bus.unsubscribe(second_subscription)

    def second(event: BaseEvent) -> None:
        received.append("second")

    bus.subscribe(BaseEvent, first)
    second_subscription = bus.subscribe(BaseEvent, second)

    await bus.publish(BaseEvent(0))

    assert received == ["first", "second"]
    assert bus.subscription_count == 1
