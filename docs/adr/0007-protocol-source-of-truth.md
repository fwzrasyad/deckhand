# 0007 - Protocol source of truth

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** D6; PROTO-003, PROTO-004, PROTO-006, PROTO-007, PROTO-008; Sections 5.1, 5.2, 5.3, 7.3, 7.10

## Context

The daemon and the phone must agree on one wire contract, and the first draft's
protocol lacked authentication, versioning, errors, exit, signal, stdin, status,
and heartbeat messages (D6). Two independent implementations of the same contract
can drift unless one artifact defines it and both sides are tested against it.

## Decision

`/protocol/` is the SINGLE SOURCE OF TRUTH for the wire contract.

- **Contents:** `README.md`, `VERSION`, `schemas/` (`envelope.schema.json`,
  `messages/<TYPE>.schema.json`, `shared/*.schema.json`), and `fixtures/`
  (`valid/`, `invalid/`, `sessions/*.jsonl` full recorded transcripts)
  (PROTO-006).
- **Version:** `protocol/VERSION` holds the current integer version.
- **Daemon:** the `protocol` package holds pure pydantic models for every
  message, envelope encode/decode, the error registry, and version negotiation.
  It performs no I/O (Section 5.2).
- **Mobile:** `data/protocol` holds DTOs and the codec, with `proofs.dart` for
  pairing HMAC proofs, unit-tested against `/protocol/fixtures` (Section 5.3).
- **Contract tests:** both the daemon and mobile suites validate their encoders
  and decoders against the same fixtures. A schema change without updated
  fixtures fails `make protocol-check` (PROTO-007).
- **Versioning:** adding optional fields or new message types is non-breaking
  within a version. Removing or renaming a field, or changing its meaning, is
  breaking and bumps `v` (PROTO-003, PROTO-004). `HELLO.protocol_versions` lists
  support, `AUTH.protocol_version` selects, and `AUTH_OK` confirms; no overlap
  yields `AUTH_FAIL PROTO_VERSION_UNSUPPORTED`.
- **Breaking changes:** CI fails if schemas change without a recorded decision in
  `docs/adr/` (Section 7.3).
- **Mock:** `tools/mock_daemon` replays session transcripts so mobile screens can be developed without a real daemon (PROTO-008).
- **Docs:** `docs/protocol.md` is the human-readable reference (Section 5.1).

## Consequences

- A protocol change is made once in `/protocol/` and both codebases follow.
- The mobile app can be built and tested against recorded transcripts.
- Schema and fixture changes must land together, or CI fails.
- Breaking changes are slower because they require a version bump and an ADR.
- Held in place by `make protocol-check` and `protocol-ci.yml`, which run JSON
  Schema meta-validation, fixture validation, and cross-validation from both
  codebases.

## Alternatives considered

- **Daemon pydantic models as the source, with schemas generated from them.** Not
  evaluated in the SRD. Rationale not recorded in SRD.
- **Separate schemas per codebase.** Rejected: the SRD designates `/protocol/` as
  the single source of truth and requires cross-validation against one fixture set.
- **`docs/protocol.md` as the normative contract.** Rationale not recorded in
  SRD; the SRD calls it a human-readable reference and places the schemas under
  `/protocol/`.
