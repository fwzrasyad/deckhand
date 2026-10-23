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
│   └── messages/               Per-type payload schemas
│       ├── HELLO.schema.json
│       ├── AUTH.schema.json
│       ├── AUTH_OK.schema.json
│       ├── AUTH_FAIL.schema.json
│       └── ERROR.schema.json
└── fixtures/
    ├── valid/                  Valid example messages
    ├── invalid/                Invalid examples (for negative tests)
    └── sessions/               Full recorded session transcripts (.jsonl)
```

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
