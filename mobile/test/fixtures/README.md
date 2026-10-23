# Test fixtures

Shared test data: envelope frames, snapshots, telemetry samples, and pairing
exchanges captured from the daemon.

Nothing is checked in yet. The canonical protocol fixtures are generated and
validated in `/protocol/fixtures` (with `tools/validate_protocol.py`), because
the daemon, the app, and the mock daemon must all agree on the same bytes. Phase
1 adds a small loader here that reads those files from the repository root, so
there is exactly one copy of every fixture.
