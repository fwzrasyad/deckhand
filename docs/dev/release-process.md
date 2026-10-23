# Release process

Purpose: Describe how Deckhand artifacts are versioned, built, signed, and
published, and which documentation a release requires (SRD Section 13).

Status: outline, to be written in Phase 6.

## Versioning

SemVer for artifacts, a separate integer protocol version, and the README
compatibility table (Section 13.3).

## Changelog

Generated from Conventional Commits with `git-cliff` (Section 13.3).

## Release workflow

`release.yml` runs on a `vX.Y.Z` tag (Section 13.1).

## Packaging

PyInstaller bundles on three OSes, wheel and sdist, Android APK and AAB
(Sections 13.1, 13.2).

## Signing

Signing steps run only when secrets are present (Section 13.1).

## Publishing

Generate `SHA256SUMS` and create the GitHub Release with the changelog
(Section 13.1).

## Documentation gate

Required docs by v1.0: README, CONTRIBUTING, SECURITY, threat model, user guide,
protocol reference, and ADRs (Section 13.3).
