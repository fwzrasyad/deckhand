# Test fixtures

Shared, non-generated test data for the daemon suite.

- Recorded sensor fixtures (hwmon, sysfs, LibreHardwareMonitor JSON) used by
  `tests/unit/telemetry/providers/` land here in Phase 2.
- Protocol transcripts live in the repository-level `protocol/fixtures/`
  directory, not here, because the mobile suite validates against them too
  (PROTO-006, PROTO-007).
- Nothing in this directory may contain tokens, pairing secrets, private keys,
  or real device identifiers.
