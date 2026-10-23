# Deckhand — Progress Tracker

> Updated by the coding agent after each phase. Keep this file accurate.
>
> Last verified: 2026-10-23, commit `00494c7`.

## Phase 0 — Foundations 🔄 In Progress

### Checklist

- [ ] Monorepo skeleton: all directories from SRD Section 5.1 — missing `mobile/lib/shared/extensions/`
- [x] Root files: README, LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CHANGELOG
- [x] `.editorconfig`, `.gitattributes`, `.gitignore`, `.gitleaks.toml`, `.pre-commit-config.yaml`
- [x] `Makefile` with all targets from Section 5.4
- [x] GitHub Actions: `daemon-ci.yml`, `mobile-ci.yml`, `protocol-ci.yml`, `security.yml`, `release.yml`
- [x] GitHub: `CODEOWNERS`, `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`, issue templates
- [x] `docs/` skeleton: architecture, protocol, security, user-guide, ADR 0001–0007, dev/
- [x] `protocol/` schemas: `envelope.schema.json`, `HELLO`, `AUTH`, `AUTH_OK`, `AUTH_FAIL`, `ERROR`
- [x] `protocol/fixtures/`: valid and invalid examples
- [x] `daemon/pyproject.toml` with ruff, mypy, pytest, import-linter
- [x] `daemon/src/deckhand/` skeleton: all modules with docstrings
- [x] `daemon/tests/` skeleton: conftest, unit mirrors, integration, security, contract, e2e
- [x] `mobile/pubspec.yaml` with all deps from Section 6.2
- [x] `mobile/lib/` skeleton: all Dart files with responsibility comments
- [x] `tools/` skeleton: mock_daemon, loadtest, scripts (bootstrap.sh, bump_version.py, record_session.py are stubs)

### Acceptance Criteria (from SRD Phase 0)

- [x] `make check` passes — verified 2026-10-23: exit 0 (lint, fmt, typecheck, import-check, daemon-test, mobile-test, protocol-check)
- [ ] CI green on all three OS for the daemon — not verified: no GitHub remote, so workflows have never run
- [x] A deliberate forbidden import is caught by import-linter (proved by a test) — verified: `pytest tests/unit/test_import_contracts.py` 2 passed
- [x] `make protocol-check` validates fixtures — verified: 12 fixtures behaved as expected, 0 failures

### Known Gaps / Decisions

- Missing vs SRD 5.1: `mobile/build.yaml`, `mobile/lib/shared/extensions/`.
- `mobile/lib/shared/extensions/` is listed by the SRD but would be empty; the
  project rule forbids empty folders.
- CI is unverified: the repository has no git remote, so the workflows have
  never run on any OS.

---

## Phase 1 — Secure Vertical Slice (MVP) ⬜ Not Started

## Phase 2 — Telemetry and Stats ⬜ Not Started

## Phase 3 — Discovery, Tray, Layout, Multi-device ⬜ Not Started

## Phase 4 — Terminal Control ⬜ Not Started

## Phase 5 — Status and Alerts ⬜ Not Started

## Phase 6 — Hardening, Packaging, Polish ⬜ Not Started
