# Testing

Purpose: Describe the test strategy, tooling, coverage gates, manual checklist,
and performance/soak runs for the daemon and the phone app (SRD Section 12).

Status: outline, to be written in later.

## Principles
Test pyramid, real-server integration tests, scripted end-to-end sessions, and injected time, randomness, and network (Section 12.1).
## Daemon tests
Unit, integration, Windows-specific, and end-to-end tests with the listed tooling (Section 12.2).
## Mobile tests
Unit, widget, golden, and integration tests against `tools/mock_daemon` (Section 12.3).
## Security suites
Injection, protocol abuse, pairing, tokens, network guard, file permissions, redaction, and fuzzing under `tests/security/` (Section 12.4).
## Contract tests
`make protocol-check`: schemas, fixtures, and both codebases' encoders (Section 12.5).
## Coverage and static analysis
Coverage thresholds and the Python/Dart lint and type commands (Section 12.6).
## Manual checklist
Hardware- and OS-dependent checks tracked in this file (Section 12.7).
## Performance and soak
Log flood, session flood, reconnect storm; results recorded in `docs/perf.md` (Section 12.8).
