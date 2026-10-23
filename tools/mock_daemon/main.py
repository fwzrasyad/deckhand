#!/usr/bin/env python3
"""Scripted fake Deckhand daemon (implemented in Phase 1).

Will replay recorded session transcripts (PROTO-008) over a local WebSocket so
mobile screens and integration tests can run without a real daemon: TLS
handshake, pairing, ``AUTH_OK``, snapshot, run streaming, alerts.

Phase 0 ships the entry point only; nothing listens on a socket yet.

Usage: python tools/mock_daemon/main.py
"""

from __future__ import annotations


def main() -> int:
    """Print what the tool will do and exit cleanly."""
    print("mock daemon: not implemented yet (Phase 1 replays session transcripts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
