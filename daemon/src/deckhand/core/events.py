"""A small in-process publish/subscribe event bus.

Layer 0 (foundations).

Handlers are called in registration order and may be synchronous or async.
Subscribing to a base class receives every event instance of its subclasses,
which lets services register one listener for a family of events.

The bus never lets one failing handler prevent delivery to the others: the
exception is logged and the remaining handlers still run. ``publish`` returns
the number of handlers that were invoked.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar, cast

EventT = TypeVar("EventT")

Handler = Callable[[Any], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class Subscription:
    """A registered handler; pass it back to :meth:`EventBus.unsubscribe`."""

    id: int
    event_type: type[Any]
    handler: Handler


class EventBus:
    """Synchronous registration with asynchronous, ordered delivery."""

    def __init__(self) -> None:
        self._subscriptions: list[Subscription] = []
        self._next_id = 0

    @property
    def subscription_count(self) -> int:
        """Number of currently registered handlers."""
        return len(self._subscriptions)

    def subscribe(
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Awaitable[None] | None],
    ) -> Subscription:
        """Register ``handler`` for events that are instances of ``event_type``."""
        subscription = Subscription(
            id=self._next_id,
            event_type=event_type,
            handler=cast(Handler, handler),
        )
        self._next_id += 1
        self._subscriptions.append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> bool:
        """Remove a subscription; return ``False`` if it was already gone."""
        for index, candidate in enumerate(self._subscriptions):
            if candidate.id == subscription.id:
                del self._subscriptions[index]
                return True
        return False

    def clear(self) -> None:
        """Remove every subscription. Ids are not reused."""
        self._subscriptions.clear()

    async def publish(self, event: object) -> int:
        """Deliver ``event`` to every matching handler and return their count."""
        snapshot = tuple(self._subscriptions)
        delivered = 0
        for subscription in snapshot:
            if not isinstance(event, subscription.event_type):
                continue
            delivered += 1
            try:
                result = subscription.handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logging.getLogger(__name__).exception(
                    "event handler %r failed for %s",
                    subscription.handler,
                    type(event).__name__,
                )
        return delivered
