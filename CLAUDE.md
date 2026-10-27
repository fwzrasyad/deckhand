# Deckhand: instructions for the coding agent

Monorepo: Python daemon (daemon/), Flutter app (mobile/), shared wire contract (protocol/).
The spec is docs/SRD.md. It is long: NEVER read it whole. Use grep to find IDs/sections
and read only the ones the current step names. Follow SRD 0.1 (agent rules) always.

## Working rules
- One step per session. Do only the step asked, commit (Conventional Commits), then stop.
- Before coding: list files you will create/change and the requirement IDs they cover.
- Tests ship with the code. Run `make check` from a normal (non-admin) shell and fix everything.
  Never loosen lint/type/import-linter rules, add ignores, or skip/delete tests to pass.
- Never weaken a SEC requirement. If one blocks you, stop and report.
- If the SRD is ambiguous on a security or crypto detail, ask. Do not guess.
- Never log, print or commit tokens, pairing secrets or keys. Never read .env files.
- Stubs/placeholders only where the step says so. No empty folders. No Phase 2+ features.
- Do not edit PROGRESS.md or CHANGELOG.md until the final Phase 1 review step.
- Keep command output short (pipe long output through tail -n 30). Do not read lockfiles,
  generated files or build output. Targeted edits, not full rewrites.
- Python 3.12 via uv. mypy --strict, ruff, no module-level mutable state, no bare `type: ignore`.
- Layering is enforced by import-linter (daemon) and tools/scripts/check_imports.py (mobile).
- Report at the end in under 15 lines: files created, make check result, coverage, decisions to review.

## Phase 1 status (update the marks when a step is committed)
[x] 1a core  [x] 1b platform/config  [x] 1c logging+redaction  [x] 2a schemas  [x] 2b protocol models
[x] 3a pairing crypto + tokens + test vectors   (SRD SEC-006..008, 4.4, 4.6)
[x] 3b pairing state machine + lockout          (4.4 window, 4.7, SEC-009/010)
[ ] 3c device store + audit log                 (4.6, 4.8, SEC-014/015/017)
[ ] 4  TLS cert generation + source-IP guard    (4.5, SEC-005/006/011)
[ ] 5a actions models, loader, registry         (8.3, 9.1)
[ ] 5b param validation + argv templating       (SEC-001..004, 8.3 rules, 12.4 injection)
[ ] 6  process runners (pipe mode) + run manager (9.2 FR-D-201..206, 7.8)
[ ] 7  transport: outbox, session, router, handlers, server (7.x, 4.7, SEC-009)
[ ] 8  CLI, control channel, bootstrap, doctor  (9.9-9.11, 5.2)
[ ] 9  daemon integration + security suites     (12.2, 12.4)
[ ] 10 mobile: build.yaml, DTOs, codec, proofs  (test against protocol/fixtures and test_vectors)
[ ] 11 mobile: pinned client, connection state machine, reconnect (4.5, 10.2, 7.9)
[ ] 12 mobile: storage, repositories, pairing screens (10.7)
[ ] 13 mobile: deck, params sheet, basic run log (10.3, 10.4 pipe mode only)
[ ] 14 Phase 1 self-review vs the 8 acceptance criteria (SRD 14) and SEC list; update PROGRESS.md/CHANGELOG.md

## Frozen decisions
- Pairing nonces/proofs are UNPADDED base64url: 16-byte nonce = 22 chars, 32-byte HMAC proof = 43 chars.
- PAIR_OK.device_token and AUTH.token: 64 lowercase hex chars. PING/PONG nonce: any string, max 64.
- Capabilities: os; telemetry{cpu_temp,gpu,gpu_vendors,battery,disk,net}; features{pty,signals,probes,notifier}.
- Schemas use absolute https://deckhand.local/... refs; unknown payload fields are ignored (PROTO-002).