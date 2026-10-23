# 0002 - Action allowlist, no raw commands

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** SEC-001, SEC-002, SEC-003, SEC-004, SEC-020; Sections 2.3 (D1), 4.3, 8.2, 9.3

## Context

The first draft let the client send raw `command` strings, which is remote code
execution on the host (D1 in Section 2.3). The daemon is authoritative: the phone
is a remote control for a fixed set of owner-defined actions, not a shell.

The SRD resolves this with an allowlist. Actions exist only in the local
`actions.yaml`; the client sends only `action_id` plus params. The `run` block
(argv, cwd, env, shell) is never sent to the phone — only `ActionMeta` is exposed.

## Decision

Clients MUST NOT send command strings. Only `action_id` and `params` cross the
wire, and every action must already exist in the local `actions.yaml`.

- Actions are defined only in `actions.yaml`; no protocol message may create,
  modify, or delete an action (SEC-002).
- Processes start from an argv list without a shell (SEC-004).
- Params are validated against the action's declared schema; unknown params,
  over-length values, NUL bytes, and control characters are rejected (SEC-003).
- Strings reject a leading `-` unless the param sets `allow_leading_dash: true`,
  which blocks argument injection such as `--upload-pack=...`.
- Placeholders are never allowed in `argv[0]`, `script.path`, or `interpreter`;
  substitution is textual within a single element, after validation, never split
  on whitespace and never passed to a shell.
- The `shell` run type is disabled unless `security.allow_shell = true`, and
  params reach it only as `DECKHAND_PARAM_<NAME>` environment variables, never
  interpolated into command text.
- `confirm: true` is a UX safeguard, not a security control; the allowlist is the
  security control (SEC-020).

## Consequences

- The phone cannot express an arbitrary command, so a compromised client is
  limited to actions the owner already declared.
- Owners must edit `actions.yaml` on the host to add capability; there is no
  remote action management (an explicit non-goal).
- Param schemas become a security boundary and need tests: the injection suite
  asserts values such as `; rm -rf /`, `$(id)`, backticks, `&& calc`, embedded
  newlines, NUL, `--flag`, and `../..` reach the child verbatim as one argv
  element, or are rejected without starting a process.
- `shell` actions carry residual risk even with env-only params; they stay off by
  default.

## Alternatives considered

- **Client-supplied command strings with server-side sanitisation.** Rejected:
  identified as the RCE flaw of the first draft (D1).
- **Remote action editing from the phone.** Rejected as a non-goal (SEC-002).
- **Treating `confirm: true` as the safety mechanism.** Rejected: SEC-020 states
  it is a UX safeguard only.
- **Allowing leading dashes by default.** Rejected: leading-dash values are
  blocked unless a param explicitly opts in, to prevent argument injection.
