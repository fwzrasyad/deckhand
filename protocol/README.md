# Protocol — Source of Truth

This directory is the **single source of truth** for the Deckhand wire
protocol. Both the daemon (`daemon/`) and the mobile app (`mobile/`) derive
their encoders, decoders, and tests from the artifacts here.

## Structure

```
protocol/
├── VERSION                     Integer protocol version (currently 1)
├── schemas/
│   ├── envelope.schema.json    The outer message envelope
│   ├── messages/               Per-type payload schemas
│   └── shared/                 Payload shapes reused by several messages
└── fixtures/
    ├── valid/                  Valid example messages
    ├── invalid/                Invalid examples (for negative tests)
    └── sessions/               Full recorded session transcripts (.jsonl)
```

A fixture's file name selects the schema under test: `<SCHEMA>.json` in
`valid/`, `<SCHEMA>_<rule broken>.json` in `invalid/`. Shared shapes are
referenced from message schemas with relative `$ref`s.

## Messages (v1)

| Type | Dir | Payload |
| :-- | :-- | :-- |
| `HELLO` | S->C | server_id, server_name, daemon_version, protocol_versions[], os, arch, tls_fp, pairing_open, auth_required |
| `AUTH` | C->S | device_id, token, protocol_version, client{app_version, platform} |
| `AUTH_OK` | S->C | session_id, device_name, protocol_version, server_time_ms, limits{} |
| `AUTH_FAIL` | S->C | code, retry_after_sec? |
| `PAIR_REQUEST` | C->S | device_id, device_name, client_nonce |
| `PAIR_CHALLENGE` | S->C | server_nonce |
| `PAIR_PROOF` | C->S | proof |
| `PAIR_OK` | S->C | device_token, server_proof |
| `PAIR_FAIL` | S->C | code |
| `UNPAIR_SELF` | C->S | (empty) |
| `PING`, `PONG` | both | nonce |
| `SERVER_SHUTDOWN` | S->C | reason, reconnect_after_sec |
| `ERROR` | S->C | code, message, details? |
| `SNAPSHOT_GET` | C->S | (empty) |
| `SNAPSHOT` | S->C | capabilities, actions[], layout, statuses[], active_runs[], alert_rules{rev, rules[]}, active_alerts[] |
| `ACTION_RUN` | C->S | action_id, params, confirmed? |
| `ACTION_ACCEPTED` | S->C | run_id |
| `RUN_STATE` | S->C | RunState |
| `PROCESS_LOG` | S->C | run_id, lines[], truncated? |
| `RUN_SIGNAL` | C->S | run_id, signal |
| `RUNS_LIST` | C->S | limit? |
| `RUNS` | S->C | runs[] |

Shared shapes in `schemas/shared/`: `ActionMeta`, `ParamSpec`, `RunState`,
`Layout`, `Capabilities`, `AlertRule`, `LogLine`, `StatusItem`.

## Rules

1. **Never edit schemas without updating fixtures** — `make protocol-check`
   will fail if they diverge.
2. **Non-breaking changes** (new optional fields, new message types) do not
   bump `VERSION`.
3. **Breaking changes** (field removed/renamed, meaning changed) MUST bump
   `VERSION` and add an ADR in `docs/adr/`.
4. **Both codebases validate** their encoders/decoders against these fixtures
   in CI (`make protocol-check`).

## Single Responsibility

This package owns the protocol contract only — no implementation code lives
here. Implementations are in `daemon/src/deckhand/protocol/` and
`mobile/lib/data/protocol/`.
