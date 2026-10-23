# 0001 - Monorepo

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** Section 5.1 (monorepo layout), Section 5 (Phase 1 deliverables), Section 7 (protocol), Section 12 (CI)

## Context

Deckhand ships two codebases that must agree on one wire contract: a Python daemon
and a Flutter phone app. The SRD makes `protocol/` the SINGLE SOURCE OF TRUTH for
the wire contract and requires contract tests on both sides. `protocol/VERSION`
holds the current version, and CI fails if schemas change without a recorded
decision in `docs/adr/` for breaking changes.

The SRD specifies the whole tree in Section 5.1: `docs/`, `protocol/`, `daemon/`,
`mobile/`, `tools/`, and `.github/`, with `Makefile`, pre-commit, and CI workflows
at the root. Phase 1 deliverables (Section 14) are stated as a monorepo skeleton.

## Decision

Use a single repository containing daemon, mobile app, protocol schemas and
fixtures, docs, tools, and CI configuration, laid out exactly as Section 5.1.

- `protocol/` is the single source of truth for the wire contract; both sides
  test against it.
- Breaking schema changes require an ADR in `docs/adr/`; CI enforces this.
- Each component keeps its own toolchain and lockfile (`daemon/pyproject.toml`,
  `mobile/pubspec.yaml`), and CI runs per-component workflows
  (`daemon-ci.yml`, `mobile-ci.yml`, `protocol-ci.yml`).
- Root-level `Makefile` and pre-commit hooks span all components.

## Consequences

- A protocol change and both sides of its implementation land in one commit, so
  contract tests can be run together.
- CI must build three targets (daemon on Windows/Linux/macOS, mobile, protocol),
  and the root `Makefile` becomes the shared entry point (`make check`).
- Version pinning and dependency audits stay per-component, so a Python bump
  cannot break the Flutter build.
- The repository carries unrelated toolchains; contributors need both Python and
  Flutter to run the full check suite.

## Alternatives considered

- **Separate repositories per component.** Not evaluated in the SRD. Rationale
  not recorded in SRD.
- **Sharing the protocol as a published package instead of a directory.** Not
  evaluated in the SRD. Rationale not recorded in SRD.
