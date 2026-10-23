# Protocol fixtures

Wire frames used by both codebases' tests. Every file is one complete envelope
(see `../schemas/envelope.schema.json`).

## Naming

| Directory | Expectation |
| :-- | :-- |
| `valid/` | Must validate against the envelope and, when the type has a payload schema, against its payload schema. |
| `invalid/` | Must be rejected. Each file breaks **exactly one** rule and is named `<SCHEMA>_<rule broken>.json`. |

The schema is chosen from the file name: the stem starts with the schema name
(`envelope`, `HELLO`, `AUTH`, `AUTH_OK`, `AUTH_FAIL`, `ERROR`), so
`AUTH_FAIL_code_not_in_enum.json` is checked as an `AUTH_FAIL` payload.

`valid/envelope.json` uses `PING`, a real protocol type that has no payload
schema in this phase, so it exercises only the envelope rules.

## Checking

```bash
python tools/scripts/validate_protocol.py protocol/schemas protocol/fixtures
```

The check also fails when a schema has no valid fixture. `make protocol-check`
runs the same command.

`invalid/` may later be reused verbatim as negative tests by the daemon and the
app; recorded session transcripts (`sessions/`, `.jsonl`) arrive in Phase 1.
