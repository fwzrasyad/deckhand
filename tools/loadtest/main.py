#!/usr/bin/env python3
"""Load generators for the NFR measurements (implemented in Phase 1).

Will drive paired sessions in three modes:

- log flood: 10,000 ``PROCESS_LOG`` lines per second, to measure the terminal
  path end to end;
- session flood: many concurrent sessions, to exercise the router and rate
  limits;
- reconnect storm: repeated connect/authenticate cycles, to exercise backoff.

Results are recorded in ``docs/perf.md`` for NFR-001 to NFR-006 (SRD 10.x).
Phase 0 ships the entry point only; no traffic is generated yet.

Usage: python tools/loadtest/main.py
"""

from __future__ import annotations


def main() -> int:
    """Print what the tool will do and exit cleanly."""
    print("loadtest: not implemented yet (Phase 1 generates log, session and reconnect floods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
