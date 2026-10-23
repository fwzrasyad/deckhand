# Contributing to Deckhand

Thank you for your interest in contributing! This document explains the
process and conventions for contributing to this project.

## Development Setup

See [docs/dev/setup.md](docs/dev/setup.md) for the full setup guide.

Quick start:
```bash
make setup   # creates venv, runs pub get, installs pre-commit hooks
make check   # lint + type check + tests (must be green before opening a PR)
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(daemon): add mDNS re-registration on interface change
fix(mobile): handle AUTH_REVOKED before SNAPSHOT received
docs(adr): add 0008-...
test(security): injection suite for leading-dash params
```

Scopes: `daemon`, `mobile`, `protocol`, `docs`, `ci`, `tools`.

## Branching

- Trunk-based development with short-lived feature branches.
- Branch names: `feat/short-description`, `fix/issue-123`, `docs/...`.
- Squash-merge into `main`.

## Pull Request Process

1. Run `make check` locally — all checks must be green.
2. Fill in the PR template completely.
3. Reference the requirement IDs (FR-, SEC-, NFR-) covered by your change.
4. Tests must accompany all logic changes (see Section 0.1 of the SRD).
5. One approval required for non-trivial changes.

## Code Style

- Python: `snake_case`, `mypy --strict`, `ruff` (line length 88).
- Dart: `lower_snake_case` files, `UpperCamelCase` types, `dart format`.
- No `# type: ignore` or `// ignore:` without an explaining comment.
- Cyclomatic complexity ≤ 10 per function.
- Module docstrings stating (1) single responsibility, (2) allowed imports.

## Security

Never weaken a SEC requirement. If a security requirement blocks progress,
stop and report it rather than working around it.

## Architecture Decisions

Significant decisions go in `docs/adr/` following the template in
[docs/adr/0000-template.md](docs/adr/0000-template.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
