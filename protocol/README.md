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

## Nonces, proofs, and tokens (v1)

Every nonce and proof on the wire is **unpadded base64url** (the URL-safe
alphabet `A-Z a-z 0-9 - _`, no `=` padding) with an exact length:

- A pairing nonce is exactly **22 characters** (`PAIR_REQUEST.client_nonce`,
  `PAIR_CHALLENGE.server_nonce`).
- `PING.nonce` and `PONG.nonce` are opaque keepalive strings of **at most 64
  characters**, unrelated to pairing.
- A 32-byte HMAC-SHA256 proof is exactly **43 characters**
  (`PAIR_PROOF.proof`, `PAIR_OK.server_proof`).

`PAIR_OK.device_token` is **64 lowercase hex characters**, the same form as
`AUTH.token`. Receivers reject anything else with `PROTO_MALFORMED`.

## Capabilities (frozen for protocol v1)

`SNAPSHOT.payload.capabilities` is a `Capabilities` object. These field names
are frozen for protocol v1: the Flutter app hard-codes them, so renaming any
field requires an explicit protocol decision (and a `VERSION` bump under rule
3). Booleans mean "supported on this host"; lists use the values the daemon
can actually serve.

- `os`: string, one of `windows`, `linux`, `macos`.
- `telemetry` (object):
  - `cpu_temp`: boolean - CPU temperature is available.
  - `gpu`: boolean - GPU metrics are available.
  - `gpu_vendors`: list of strings - detected GPU vendors (for example
    `nvidia`); empty when no GPU metrics are supported.
  - `battery`: boolean - battery metrics are available.
  - `disk`: boolean - disk throughput and volume metrics are available.
  - `net`: boolean - network throughput metrics are available.
- `features` (object):
  - `pty`: boolean - PTY runs are supported on this host.
  - `signals`: list of strings - deliverable signals, each `INTERRUPT`,
    `TERMINATE`, or `KILL`.
  - `probes`: list of strings - status probes implemented on this host (for
    example `process_alive`, `docker_container`).
  - `notifier`: string - configured notifier type (for example `none`,
    `ntfy`).

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
