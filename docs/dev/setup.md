# Development setup

Purpose: Get a contributor from a fresh clone to a running daemon, a running mock
daemon, and a green `make check`, using the repository's Makefile and tooling
(SRD Sections 5.4, 6, 12.6).

Status: outline, to be written in later.

## Prerequisites

Python 3.11+ and the Flutter SDK; versions pinned in the lockfiles
(Sections 6.1, 6.2).

## Bootstrap

`make setup`: create the venv, run `pub get`, and install hooks (Section 5.4).

## Make targets

`make check`, `lint`, `fmt`, `typecheck`, `daemon-test`, `mobile-test`,
`protocol-check`, `import-check`, `run-daemon`, `mock-daemon`,
`package-daemon`, and `audit` (Section 5.4).

## Pre-commit and CI parity

Run the same linters and formatters locally as CI: ruff, mypy, import-linter,
bandit for Python; format and analyze for Dart (Section 12.6).

## Run the daemon

`make run-daemon` and `make mock-daemon` for mobile work without a real daemon
(Sections 5.4, 7.10).

## Repository rules

Layering and import contracts, and the requirement that every package states its
responsibility and allowed imports (Sections 3.3, 5.5).
