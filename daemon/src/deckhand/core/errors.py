"""Error base classes shared by every daemon layer.

Layer 0 (foundations). This module deliberately contains only the exception
hierarchy: concrete subsystems add their own subclasses (for example
``deckhand.protocol.errors`` maps failures to wire error codes) so callers can
always catch a single root type.
"""

from __future__ import annotations

from collections.abc import Mapping


class DeckhandError(Exception):
    """Root of every exception raised deliberately by Deckhand.

    ``str(error)`` is the human-readable message. ``details`` carries optional
    structured context for logs and tests; it must never contain secrets
    (SRD 0.1, rule 6).
    """

    def __init__(
        self,
        message: str = "",
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = dict(details or {})

    def __str__(self) -> str:
        return self.message


class ConfigurationError(DeckhandError):
    """Configuration is missing, malformed, or failed validation."""


class LifecycleError(DeckhandError):
    """A service could not be started or stopped in an orderly fashion."""


class StartupError(LifecycleError):
    """A service failed to start, or start exceeded the deadline."""


class ShutdownError(LifecycleError):
    """One or more services failed to stop, or stop exceeded the deadline."""


class RateLimitError(DeckhandError):
    """A token-bucket limiter refused a request."""
