"""Start and stop services in dependency order.

Layer 0 (foundations).

Services are started in registration order and stopped in reverse order. Every
start and stop call is bounded by a timeout. If a start fails, services that
already started during this call are stopped again (best effort) before the
error is re-raised; if a stop fails, the remaining services are still stopped
and the failures are reported together.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Protocol

from deckhand.core.errors import LifecycleError, ShutdownError, StartupError


class Service(Protocol):
    """A component with an ordered start/stop lifecycle."""

    async def start(self) -> None:
        """Acquire resources and begin work."""
        ...  # pragma: no cover - protocol declaration

    async def stop(self) -> None:
        """Stop work and release resources."""
        ...  # pragma: no cover - protocol declaration


@dataclass(frozen=True, slots=True)
class Registration:
    """A service together with the name used in diagnostics."""

    name: str
    service: Service


class LifecycleManager:
    """Track registrations and run them in order."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._timeout = timeout
        self._registrations: list[Registration] = []
        self._started: list[Registration] = []
        self._running = False

    @property
    def started(self) -> tuple[str, ...]:
        """Names of services that are currently started, in start order."""
        return tuple(registration.name for registration in self._started)

    def register(self, name: str, service: Service) -> None:
        """Add a service. Registration order is start order."""
        if not name:
            raise ValueError("service name must not be empty")
        if self._running:
            raise LifecycleError("cannot register a service while running")
        if any(existing.name == name for existing in self._registrations):
            raise ValueError(f"service {name!r} is already registered")
        self._registrations.append(Registration(name=name, service=service))

    async def start(self) -> None:
        """Start every registered service, rolling back on failure."""
        if self._running:
            raise LifecycleError("lifecycle is already running")

        for registration in self._registrations:
            try:
                await self._with_timeout(registration.service.start())
            except TimeoutError as exc:
                await self._rollback()
                raise StartupError(
                    f"service {registration.name!r} timed out starting after {self._timeout:g}s",
                    details={"service": registration.name},
                ) from exc
            except Exception as exc:
                await self._rollback()
                raise StartupError(
                    f"service {registration.name!r} failed to start: {exc}",
                    details={"service": registration.name},
                ) from exc
            self._started.append(registration)

        self._running = True

    async def stop(self) -> None:
        """Stop started services in reverse order, reporting every failure."""
        registrations = list(reversed(self._started))
        self._started.clear()
        self._running = False

        errors: list[tuple[str, BaseException]] = []
        for registration in registrations:
            try:
                await self._with_timeout(registration.service.stop())
            except TimeoutError as exc:
                self._log_failure(registration.name, "stop", exc)
                errors.append(
                    (
                        registration.name,
                        TimeoutError(
                            f"timed out stopping after {self._timeout:g}s",
                        ),
                    )
                )
            except Exception as exc:
                self._log_failure(registration.name, "stop", exc)
                errors.append((registration.name, exc))

        if errors:
            names = ", ".join(name for name, _ in errors)
            raise ShutdownError(
                f"{len(errors)} service(s) failed to stop: {names}",
                details={"services": names},
            ) from errors[0][1]

    async def _with_timeout(self, awaitable: Awaitable[None]) -> None:
        await asyncio.wait_for(awaitable, timeout=self._timeout)

    async def _rollback(self) -> None:
        """Stop whatever started during the failed start call, best effort."""
        registrations = list(reversed(self._started))
        self._started.clear()
        for registration in registrations:
            try:
                await self._with_timeout(registration.service.stop())
            except Exception as exc:
                self._log_failure(registration.name, "rollback stop", exc)

    @staticmethod
    def _log_failure(name: str, phase: str, error: BaseException) -> None:
        logging.getLogger(__name__).error("service %r failed during %s: %s", name, phase, error)
