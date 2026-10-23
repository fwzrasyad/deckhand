# Deckhand — Progress Tracker

> Updated by the coding agent after each phase. Keep this file accurate.

## Phase 0 — Foundations 🔄 In Progress

### Checklist

- [x] Monorepo skeleton: all directories from SRD Section 5.1
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
- [x] `tools/` skeleton: mock_daemon, loadtest, scripts

### Acceptance Criteria (from SRD Phase 0)

- [ ] `make check` passes (pending: requires Python and Flutter runtime)
- [ ] CI green on all three OS for the daemon
- [ ] A deliberate forbidden import is caught by import-linter (proved by a test)
- [ ] `make protocol-check` validates fixtures

### Known Gaps / Decisions

- None yet. Add ADR references here if design decisions were made.

---

## Phase 1 — Secure Vertical Slice (MVP) ⬜ Not Started

## Phase 2 — Telemetry and Stats ⬜ Not Started

## Phase 3 — Discovery, Tray, Layout, Multi-device ⬜ Not Started

## Phase 4 — Terminal Control ⬜ Not Started

## Phase 5 — Status and Alerts ⬜ Not Started

## Phase 6 — Hardening, Packaging, Polish ⬜ Not Started
