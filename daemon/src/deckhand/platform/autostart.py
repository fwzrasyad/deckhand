"""Autostart backends: Run key, systemd user unit, LaunchAgent.

Layer 0 (foundations). Stub only. The daemon does not register itself for login
yet; this module exists so the CLI's ``autostart enable|disable`` commands and
the eventual backends have a home (SRD 5.2).

Every entry point raises :class:`NotImplementedError` rather than silently doing
nothing: a caller that forgets to check for support must fail loudly.
"""

from __future__ import annotations

_NOT_IMPLEMENTED = (
    "autostart management is not implemented yet; it is scheduled for a later "
    "phase of the daemon (SRD 5.2 lists `autostart enable|disable`)"
)


def enable() -> None:
    """Register the daemon to start at user login."""
    raise NotImplementedError(_NOT_IMPLEMENTED)


def disable() -> None:
    """Remove the daemon's autostart registration."""
    raise NotImplementedError(_NOT_IMPLEMENTED)


def is_enabled() -> bool:
    """Whether the daemon is currently registered to start at login."""
    raise NotImplementedError(_NOT_IMPLEMENTED)
