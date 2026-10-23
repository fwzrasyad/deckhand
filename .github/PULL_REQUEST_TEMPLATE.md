## Description

<!-- Briefly describe what this PR does and why. -->

## Related Issues / Requirements

<!-- Reference issue numbers and SRD requirement IDs covered by this change. -->
<!-- Example: Closes #42. Implements FR-D-101, FR-D-102. Addresses SEC-003. -->

Closes #
Requirements: <!-- FR-*, SEC-*, NFR-*, PROTO-* -->

## Type of Change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (bumps protocol version or changes public API)
- [ ] Docs / tests / CI only
- [ ] Refactor

## Checklist

- [ ] `make check` passes locally (lint, type check, tests, import rules)
- [ ] Tests accompany all logic changes
- [ ] Docstrings updated for changed modules (responsibility + allowed imports)
- [ ] `docs/` updated if behavior or configuration changed
- [ ] `CHANGELOG.md` entry added (Conventional Commit format)
- [ ] `PROGRESS.md` updated if a phase milestone is reached
- [ ] No `# type: ignore` or `// ignore:` added without an explanatory comment
- [ ] No SEC requirement weakened

## Protocol Changes (if any)

- [ ] Protocol change is non-breaking (new optional field or new message type)
- [ ] Protocol change is breaking — `protocol/VERSION` bumped and ADR added
- [ ] Fixtures updated to match schema changes
- [ ] `make protocol-check` passes

## Security Impact

<!-- Does this change touch security-sensitive code? Describe the impact. -->
- [ ] No security-sensitive code changed
- [ ] Security-sensitive code changed — described above

## Testing Notes

<!-- Describe how you tested this change, especially for OS-specific or
hardware-dependent behavior. -->
