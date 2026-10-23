# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 0: full monorepo skeleton
  - Repository structure from SRD Section 5.1
  - Makefile with all targets from Section 5.4
  - GitHub Actions CI workflows (daemon, mobile, protocol, security, release)
  - pyproject.toml with ruff, mypy, pytest, import-linter configuration
  - pubspec.yaml with all dependencies from SRD Section 6.2
  - Protocol schemas: envelope, HELLO, AUTH, AUTH_OK, AUTH_FAIL, ERROR
  - Protocol fixtures (valid and invalid examples)
  - ADR drafts 0001–0007
  - PROGRESS.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
  - pre-commit hooks, editorconfig, gitattributes, gitignore, gitleaks config
