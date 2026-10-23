# Deckhand - Software Requirements Document

Version 1.0 | Status: implementation-ready | Replaces the earlier SystemDeck draft | Audience: AI coding agents (OpenCode, Cursor, CLI) and human maintainers

> Deckhand is a working name. Keep it in one constants file per codebase (`daemon/src/deckhand/version.py`, `mobile/lib/core/constants/app_constants.dart`) so a rename touches only those files, the mDNS service type, and the `deckhand://` URI scheme.

## 0. How to Use This Document

### 0.1 Agent operating rules

1. Read this whole document once, then build phase by phase (Section 14). Do not start a later phase until the current phase's acceptance criteria pass.
2. MUST, SHOULD, MAY follow RFC 2119. Requirement IDs (FR-, SEC-, NFR-, PROTO-) are referenced in test names or docstrings so coverage is traceable.
3. Every change ships with code, tests, and docs. Logic in the `security`, `actions`, `process`, and `protocol` modules MUST have unit tests written alongside it.
4. Do not invent features. If something is underspecified, pick the simplest and safest option, record it as an ADR in `docs/adr/`, and continue.
5. Never weaken a SEC requirement to make something work. If a SEC requirement blocks progress, stop and report it.
6. Never log tokens, pairing secrets, private keys, or params marked `secret`.
7. Keep `PROGRESS.md` current: done, in progress, decisions taken, known gaps.
8. Run `make check` (lint, type check, tests, import rules, protocol contract tests) before declaring any task done.
9. Standards: Python 3.11+, full type hints, `mypy --strict`, `ruff`. Dart with strict analysis (`strict-casts`, `strict-inference`, `strict-raw-types`) and `dart format`. No `# type: ignore` or `// ignore:` without a comment explaining why.
10. Small modules with one responsibility each. Prefer dependency injection over globals. No module-level mutable state.

### 0.2 Definition of Done (every phase)

- All phase acceptance criteria pass.
- `make check` green on Linux; daemon CI jobs green on Windows and macOS.
- New behavior covered by tests; coverage targets in Section 12 met.
- Behavior documented in `docs/`; example configs updated.
- No TODO without an issue reference.
- `PROGRESS.md` and `CHANGELOG.md` updated.

## 1. Product Overview

### 1.1 Summary

Deckhand turns a smartphone into a control surface for a development PC. A lightweight Python daemon on the PC exposes a small set of owner-defined actions, streams hardware telemetry, runs processes and streams their output. A Flutter app on the phone shows an action grid, a stats dashboard, and a live terminal. They talk over an authenticated, encrypted WebSocket on the local network or a VPN such as Tailscale.

Two deliverables share one protocol: the **daemon** (`daemon/`) and the **mobile app** (`mobile/`).

### 1.2 Goals

- G1: One-tap execution of pre-defined actions (Docker, git, builds, scripts) without leaving the IDE.
- G2: Live telemetry (CPU, RAM, disk, network, GPU, temperatures where the OS allows, battery) at 1 Hz.
- G3: Live process output and control (interrupt, terminate, kill, stdin) from the phone.
- G4: Safe by construction: a paired phone can only trigger actions the PC owner defined on the PC.
- G5: Zero-config discovery on LAN, with manual entry for Tailscale and restricted networks.
- G6: A modular, well-tested, documented codebase that outside contributors can navigate.

### 1.3 Non-goals (v1)

Cloud relay or accounts; internet exposure; remote file browser; remote desktop, mouse, or keyboard injection; creating or editing action definitions from the phone; multi-user roles; Windows service mode (runs as a normal user process); background execution on the phone; plugin marketplace.

### 1.4 Primary scenarios

- S1: Tap Docker Up. Output streams, the card flashes green, a light haptic tick fires.
- S2: A build runs for five minutes. The phone shows live logs; the user presses Ctrl+C to interrupt it.
- S3: GPU temperature crosses a threshold while the app is open. The phone vibrates and shows an alert banner.
- S4: First setup: run `deckhand pair`, scan the QR code, connected in under a minute.
- S5: Away from home on Tailscale: enter the 100.x address manually and connect.

### 1.5 Glossary

- **Daemon**: the PC-side process. **Client**: the phone app.
- **Action**: an owner-defined, named, parameterized command in `actions.yaml`.
- **Run**: one execution of an action. **Session**: one authenticated WebSocket connection.
- **Device**: a paired phone, identified by `device_id` and a token.
- **Pairing window**: a short period (120 s) in which the daemon accepts a new device.
- **Capability**: a feature or sensor the host actually supports, advertised to the client.
- **Snapshot**: the full current state sent to a client after authentication.
- **Probe**: a check that decides a status card's color (process alive, port open, ...).

## 2. Scope, Platforms, Constraints

### 2.1 Support matrix

- Daemon: Windows 10/11 (Tier 1). Linux with systemd, X11 or Wayland (Tier 1; tray needs AppIndicator, headless fallback otherwise). macOS 13+ (Tier 2: no CPU temperatures, no GPU metrics).
- Mobile: Android 8.0+ / API 26+ (Tier 1). iOS 16+ (Tier 1 in design, built best-effort since it needs a Mac).
- Runtimes: Python 3.11, 3.12, 3.13. Flutter stable channel, Dart 3.x.

### 2.2 Constraints

- LAN or VPN only. No cloud, no accounts, no analytics, no third-party network calls (the optional notifier in Phase 6 is opt-in and user-configured).
- License: MIT.
- Footprint targets in Section 11.

### 2.3 Issues found in the first draft and how this SRD resolves them

| ID | Problem in the draft | Resolution | Section |
| :-- | :-- | :-- | :-- |
| D1 | Client sent raw `command` strings (remote code execution) | Client sends only `action_id` + params; commands live in the local `actions.yaml` | 4, 8.2 |
| D2 | 4-digit PIN over plain ws:// is brute-forceable | TLS, certificate pinning, 60-bit pairing secret, 120 s window, lockout | 4.4-4.7 |
| D3 | HMAC pairing mentioned but never specified | Full transcript-bound handshake | 4.4 |
| D4 | psutil temps are Linux-only; GPUtil is NVIDIA-only | Pluggable sensor providers, capability negotiation, null when unsupported | 9.4 |
| D5 | Haptic alerts assumed to work in background | Foreground-only in v1; daemon-side alert engine; optional push notifier in Phase 6 | 9.6 |
| D6 | Protocol lacked auth, version, errors, exit, signal, stdin, status, heartbeat | Complete protocol with envelope, versioning, error registry | 7 |
| D7 | SIGINT and stdin assumed POSIX pipes | Runner abstraction, Windows CTRL\_BREAK, pty mode | 9.2 |
| D8 | Single-threaded vs multi-threaded contradiction | One asyncio loop thread, executor for blocking work, tray on main thread | 3.2 |
| D9 | Layout storage unspecified | Daemon owns `actions.yaml` (not remotely writable) and `layout.json` (phone-editable) | 3.6, 8 |
| D10 | Insecure MVP with security bolted on later | Security is built in Phase 1 | 14 |
| D11 | Long-press used for both params and reorder | Explicit edit mode for reordering | 10.3 |
| D12 | Discovery assumed to always work | Manual entry required; mDNS is only a hint | 9.7 |

## 3. Architecture

### 3.1 Component diagram

```
+------------------------------ HOST PC -------------------------------+
| deckhand daemon (one process)                                       |
|  tray (main thread) --thread-safe queue--> core thread (asyncio loop)|
|     |- transport  (wss server, sessions, router, handlers)           |
|     |- security   (pairing, tokens, device store, audit)             |
|     |- actions    (registry, param validation, argv templating)      |
|     |- process    (runners, run manager, log ring buffers)           |
|     |- status     (probe scheduler)                                  |
|     |- telemetry  (sampler + providers) --> alerts engine            |
|     |- layout store, discovery (mDNS), control server (loopback)     |
|  CLI: deckhand ... --loopback control channel--> daemon              |
+----------------------------------------------------------------------+
      ^  wss:// TLS, pinned certificate, JSON text frames (LAN/Tailscale)
      v
+------------------------------- PHONE -------------------------------+
| Flutter: presentation -> application (Riverpod) -> domain <- data    |
|          (screens)       (controllers)             (entities) (ws client, storage, mDNS)
+----------------------------------------------------------------------+
```

### 3.2 Daemon runtime and threading model

- Core: ONE asyncio event loop in a dedicated thread (the core thread). All protocol handling, sessions, probe scheduling, and process supervision run on it.
- Blocking or slow work (psutil sampling, GPU queries, certificate generation, config file writes) goes through `asyncio.to_thread` or a bounded `ThreadPoolExecutor` (max 4 workers), each call with a timeout.
- Tray runs on the main thread (required by macOS, safe elsewhere). Tray to core uses `loop.call_soon_threadsafe` and a thread-safe command queue. Core to tray uses a thread-safe state object. No other cross-thread sharing.
- Headless mode (`--no-tray`): the core loop runs on the main thread.
- Subprocess output is read with asyncio streams; Windows pty reads use an executor thread. Nothing blocks the loop.

### 3.3 Daemon layering and import rules

- Layer 0: `core`, `config`, `platform`. No domain imports.
- Layer 1: `protocol` (pure pydantic models; imports `core` only).
- Layer 2 (domain services): `security`, `actions`, `process`, `status`, `telemetry`, `alerts`, `layout`, `discovery`. May import layers 0-1. Allowed cross-service imports only: `actions -> process`, `status -> process`, `alerts -> telemetry`.
- Layer 3: `transport`. Handlers translate protocol messages into service calls through `typing.Protocol` interfaces. Domain services MUST NOT import `transport`.
- Layer 4 (edges): `cli`, `tray`, `control`. `bootstrap.py` is the only composition root where concrete classes are wired.
- Enforced with `import-linter` contracts in `daemon/pyproject.toml`. A violation fails CI.

### 3.4 Mobile layering

Feature-first. Each feature folder has `presentation/` (screens, widgets) and `application/` (Riverpod controllers). `domain/` holds entities and repository interfaces; `data/` implements them. Dependencies point inward: presentation -> application -> domain; data -> domain. `data/` never imports presentation. Features do not import each other's internals; shared code lives in `shared/` or `domain/`. Checked by `tools/scripts/check_imports.py`.

### 3.5 Key flows

- Run: ACTION\_RUN -> router -> auth and rate checks -> ActionService (lookup, validate params, build argv) -> RunManager.start -> runner spawns -> ACTION\_ACCEPTED -> RUN\_STATE broadcast -> PROCESS\_LOG batches -> terminal RUN\_STATE.
- Telemetry: sampler tick -> providers sampled concurrently in the executor -> merged frame -> alert engine evaluates -> frame sent to subscribed sessions.
- Pairing: Section 4.4.

### 3.6 State ownership

| State | Owner | Phone may edit | Storage |
| :-- | :-- | :-- | :-- |
| Action definitions | Daemon | No | config dir `actions.yaml` |
| Layout (pages, grid, order) | Daemon | Yes, `LAYOUT_SET` | state dir `layout.json` |
| Alert rules | Daemon | Yes, `ALERT_RULES_SET` | state dir `alerts.json` |
| Paired devices (hashed tokens) | Daemon | Only self-unpair | state dir `devices.json` |
| TLS certificate and key | Daemon | No | state dir `tls/` |
| Device token + pinned fingerprint | Phone | n/a | `flutter_secure_storage` |
| Saved hosts, UI settings | Phone | n/a | `shared_preferences` |
| Run logs | Daemon, in-memory ring buffers | Read only | memory |

## 4. Security

### 4.1 Assets and trust boundaries

Assets: the ability to execute code on the PC, the device tokens, the TLS private key, and the content of process output. Trust boundary: everything on the network is untrusted until it completes pairing or token auth. Processes running as the same OS user as the daemon are trusted equally to the user (out of scope).

### 4.2 Threat model

| ID | Threat | Mitigation |
| :-- | :-- | :-- |
| T1 | Rogue device on the same Wi-Fi sends commands | TLS, token auth, allowlisted actions only |
| T2 | Brute-forcing pairing | 60-bit secret, 120 s window, 5 attempts, lockout |
| T3 | MITM on the LAN | Pinned certificate fingerprint + transcript-bound HMAC proofs |
| T4 | Lost or stolen phone | Per-device revocation, secure storage, optional biometric app lock |
| T5 | Tampered or malicious client messages | Daemon is authoritative: schema validation, allowlist, limits |
| T6 | Argument or command injection through params | No shell, argv templating, regex/enum/range validation |
| T7 | DoS: floods, huge frames, slowloris, log floods | Size limits, rate limits, connection caps, deadlines, backpressure |
| T8 | mDNS spoofing | mDNS is a hint; trust only the pinned fingerprint |
| T9 | Local malware reading token files | Out of scope beyond file permissions (same-user trust) |
| T10 | Phone rewriting executable config | `actions.yaml` is not remotely writable |
| T11 | Accidental internet exposure (port forward) | Source-IP allowlist of private ranges by default |
| T12 | Privilege escalation | Daemon refuses to run as root/admin by default |

### 4.3 Security requirements

- SEC-001: The daemon MUST NOT accept command strings from clients. Clients send only `action_id` and `params`.
- SEC-002: Actions are defined only in the local `actions.yaml`. No protocol message may create, modify, or delete an action.
- SEC-003: Params MUST be validated against the action's declared schema. Unknown params, over-length values, and NUL bytes are rejected.
- SEC-004: Processes MUST be started from an argv list without a shell. The `shell` action type requires `security.allow_shell = true`, and params reach it only as environment variables, never interpolated into the command text.
- SEC-005: Non-loopback listeners MUST use TLS 1.2+ (TLS 1.3 preferred). Plain `ws://` is allowed only on a loopback bind with `--insecure-dev`; the daemon refuses to start otherwise.
- SEC-006: The daemon generates a self-signed ECDSA P-256 certificate on first run. The client pins the SHA-256 of the DER certificate.
- SEC-007: Pairing follows Section 4.4 exactly.
- SEC-008: Device tokens are 256-bit random values. The daemon stores only the SHA-256 hash and compares with `hmac.compare_digest`.
- SEC-009: Unauthenticated sockets get a 5 s deadline (10 s during pairing) and may send only `AUTH`, `PAIR_REQUEST`, `PAIR_PROOF`. At most 4 unauthenticated sockets at once.
- SEC-010: Failed auth or pairing attempts are rate limited per source IP (Section 4.7).
- SEC-011: Connections from source addresses outside `server.allowed_networks` are closed at accept. Default: RFC 1918, 100.64.0.0/10, fe80::/10, fc00::/7, loopback.
- SEC-012: Inbound frame size, message rate, and run-start rate are limited (Section 4.7).
- SEC-013: The daemon refuses to start as root or Administrator unless `--allow-elevated` is passed, and logs a warning when it is.
- SEC-014: Secret files (private key, device store, control token) are created with mode 0600 (Windows: ACL restricted to the current user) and verified at startup.
- SEC-015: Security events are written to an audit log (Section 4.8).
- SEC-016: A log redaction filter strips tokens, pairing secrets, and params marked `secret`.
- SEC-017: Revoking a device closes its live sessions within 1 s (close code 4401).
- SEC-018: The phone stores the token and pinned fingerprint only in `flutter_secure_storage`. Android: `allowBackup=false`, cleartext traffic disabled. iOS: Keychain, `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`.
- SEC-019: mDNS TXT records contain no secrets.
- SEC-020: `confirm: true` on an action is a UX safeguard (the phone asks first), not a security control. The security control is the allowlist.
- SEC-021: Dependencies are pinned and audited in CI (`pip-audit`, OSV scanner, `gitleaks`).
- SEC-022: `deckhand tls rotate` regenerates the certificate and revokes all pairings, since pinned fingerprints stop matching.

### 4.4 Pairing protocol

**Pairing secret.** 60 random bits from `secrets`, shown as 12 Crockford Base32 characters grouped `XXXX-XXXX-XXXX`. Input is normalized (uppercase, strip spaces and hyphens, I and L become 1, O becomes 0). The QR code encodes `deckhand://pair?host=H&port=P&fp=FP&secret=S&name=N`.

**Window.** Opened by `deckhand pair` or the tray menu. Lasts 120 s. At most 5 failed `PAIR_PROOF` attempts across all clients; the 5th failure closes the window and starts a 30 s cooldown. The window closes after the first successful pairing. The window is also closed by `deckhand pair --cancel`.

**Definitions.** `fp` = lowercase hex SHA-256 of the daemon certificate in DER form. `K` = the normalized secret as ASCII bytes. `transcript(role)` = the UTF-8 string `deckhand-pair-v1|<role>|<fp>|<client_nonce>|<server_nonce>|<device_id>`, where role is `client` or `server`.

**Steps.**

1. Phone connects over TLS. If it scanned a QR code it MUST verify the presented certificate's fingerprint equals `fp` from the QR and abort otherwise. If the user typed the code, it accepts any certificate for this one pairing connection and records the fingerprint it saw (`fp_seen`).
2. Phone sends `PAIR_REQUEST {device_id (random UUIDv4), device_name, client_nonce (16 random bytes, base64url)}`.
3. Daemon replies `PAIR_CHALLENGE {server_nonce (16 random bytes, base64url)}`.
4. Phone sends `PAIR_PROOF {proof = base64url(HMAC-SHA256(K, transcript(client) using fp_seen))}`.
5. Daemon recomputes with its own `fp`; on match (constant time) it creates the device record and replies `PAIR_OK {device_token, server_proof = base64url(HMAC-SHA256(K, transcript(server)))}`.
6. Phone recomputes `server_proof` using `fp_seen`. On mismatch it discards the token, aborts, and shows a possible-interception error. On success it stores token, `device_id`, and `fp_seen` (now pinned) in secure storage.
7. A MITM presenting a different certificate causes `fp_seen` to differ from the daemon's `fp`, so the daemon's recomputation fails and pairing is rejected. The 60-bit secret makes offline guessing of captured proofs infeasible.

On failure the daemon sends `PAIR_FAIL {code}` and closes with 4401. Failure codes: `PAIR_WINDOW_CLOSED`, `PAIR_BAD_PROOF`, `PAIR_LOCKED_OUT`.

### 4.5 TLS

- Certificate: ECDSA P-256, CN `deckhand-<hostname>`, 5-year validity, SAN includes the hostname and `localhost`. Private key stays in the state dir (SEC-014).
- Server: `ssl.SSLContext(PROTOCOL_TLS_SERVER)`, minimum version TLS 1.2, no client certificates.
- Client: Dart `HttpClient` with a `badCertificateCallback` that accepts only a certificate whose SHA-256(DER) equals the pinned fingerprint (or, during typed-code pairing only, records it). Hostname and CA validation are intentionally bypassed in favor of pinning.
- Tailscale: TLS is still used (defense in depth).

### 4.6 Tokens and device store

`devices.json` holds an array of `{device_id, name, token_sha256, created_at, last_seen_at, last_ip, revoked}`. Writes are atomic (write temp, fsync, rename). The phone sends `AUTH {device_id, token}` on every connection. Tokens do not expire in v1; revoke with `deckhand devices revoke <id>`, the tray, or `UNPAIR_SELF` from the phone.

### 4.7 Limits and abuse controls

- Failed auth/pairing: 5 failures per source IP -> blocked 60 s; doubles on each repeat up to 15 min; cleared after 1 h without failures.
- Max total connections 8 (configurable); max unauthenticated 4.
- Inbound frame max 64 KiB; larger -> close 1009. Binary frames -> close 1003. Invalid JSON or unknown envelope -> `ERROR PROTO_MALFORMED`, third strike closes 4400.
- Per-session token bucket: 50 messages/s sustained, burst 100. Exceeding -> `ERROR RATE_LIMITED`; sustained abuse closes 4429.
- `ACTION_RUN`: max 5/s per session. Max concurrent runs 16 total; per action 1 unless `parallel: true`.
- `RUN_STDIN`: max 4 KiB per message, 20 messages/s.
- Outbound queue per session: see backpressure in Section 7.8.

### 4.8 Audit log

JSON lines, rotating (5 files x 5 MB), separate from the app log. Events: `pairing_window_opened/closed`, `pair_success/failure`, `auth_success/failure`, `device_revoked`, `action_run` (action\_id, device\_id, param names, values only for params not marked secret and under 200 chars), `run_signal`, `config_reloaded`, `layout_changed`, `rate_limit_block`, `daemon_start/stop`. Process output is never written to the audit log.

### 4.9 Secure-defaults checklist (verify in Phase 6)

TLS on; shell type off; remote layout edit on, remote action edit impossible; allowed networks private only; elevated run refused; secret files 0600; audit log on; pairing window closed at startup; mDNS advertises `pair=0` unless a window is open.

## 5. Repository Structure

### 5.1 Monorepo layout

```
deckhand/
|-- .github/
|   |-- workflows/          daemon-ci.yml, mobile-ci.yml, protocol-ci.yml, security.yml, release.yml
|   |-- ISSUE_TEMPLATE/     bug_report.yml, feature_request.yml
|   |-- CODEOWNERS, PULL_REQUEST_TEMPLATE.md, dependabot.yml
|-- docs/
|   |-- SRD.md              this document
|   |-- architecture.md     diagrams and module map
|   |-- protocol.md         human-readable protocol reference
|   |-- security/           threat-model.md, pairing.md
|   |-- user-guide/         install-daemon.md, pairing-a-phone.md, writing-actions.md,
|   |                       remote-access-tailscale.md, troubleshooting.md
|   |-- adr/                0000-template.md, 0001-monorepo.md,
|   |                       0002-action-allowlist-no-raw-commands.md,
|   |                       0003-tls-with-cert-pinning.md, 0004-pairing-secret-design.md,
|   |                       0005-event-loop-and-threading-model.md,
|   |                       0006-sensor-provider-abstraction.md, 0007-protocol-source-of-truth.md
|   |-- dev/                setup.md, testing.md, release-process.md
|-- protocol/               SINGLE SOURCE OF TRUTH for the wire contract
|   |-- README.md, VERSION
|   |-- schemas/            envelope.schema.json, messages/<TYPE>.schema.json, shared/*.schema.json
|   |-- fixtures/           valid/, invalid/, sessions/*.jsonl (full recorded transcripts)
|-- daemon/
|   |-- pyproject.toml      deps, ruff, mypy, pytest, import-linter contracts
|   |-- README.md, .python-version
|   |-- examples/           actions.example.yaml, config.example.toml
|   |-- packaging/          pyinstaller.spec, linux/(deckhand.service, deckhand.desktop),
|   |                       macos/(app.deckhand.daemon.plist), windows/(installer notes)
|   |-- src/deckhand/
|   |   |-- __init__.py, __main__.py, version.py, bootstrap.py, logging_setup.py
|   |   |-- cli/            main.py, serve.py, pair.py, devices.py, actions.py, tls.py,
|   |   |                   autostart.py, doctor.py
|   |   |-- config/         settings.py, loader.py, paths.py, defaults.py
|   |   |-- core/           errors.py, ids.py, clock.py, events.py, lifecycle.py,
|   |   |                   ratelimit.py, ringbuffer.py, atomic_io.py
|   |   |-- platform/       base.py, windows.py, linux.py, macos.py, autostart.py
|   |   |-- protocol/       envelope.py, codec.py, errors.py, versions.py,
|   |   |                   messages/(client.py, server.py, shared.py)
|   |   |-- transport/      server.py, session.py, router.py, outbox.py, tls.py, netguard.py,
|   |   |                   handlers/(auth.py, pairing.py, snapshot.py, actions.py, runs.py,
|   |   |                   telemetry.py, layout.py, alerts.py, system.py)
|   |   |-- security/       pairing.py, tokens.py, device_store.py, audit.py, crypto.py,
|   |   |                   lockout.py, redaction.py
|   |   |-- actions/        models.py, loader.py, registry.py, params.py, templating.py,
|   |   |                   service.py, macros.py
|   |   |-- process/        base.py, factory.py, posix.py, windows.py, pty_posix.py,
|   |   |                   pty_windows.py, run.py, manager.py, logbuffer.py, signals.py
|   |   |-- status/         models.py, scheduler.py,
|   |   |                   probes/(base.py, process.py, tcp.py, http.py, docker.py, run_state.py)
|   |   |-- telemetry/      models.py, sampler.py, capabilities.py,
|   |   |                   providers/(base.py, psutil_provider.py, nvidia.py, linux_hwmon.py,
|   |   |                   amd_sysfs.py, libre_hw_monitor.py)
|   |   |-- alerts/         engine.py, rules.py, store.py, notifiers/(base.py, ntfy.py)
|   |   |-- layout/         models.py, store.py, service.py
|   |   |-- discovery/      mdns.py, interfaces.py
|   |   |-- control/        server.py, client.py, commands.py   (loopback admin channel)
|   |   |-- tray/           app.py, state.py, icons.py, pair_window.py, assets/
|   |-- tests/
|   |   |-- conftest.py, fixtures/
|   |   |-- unit/           mirrors src/ layout
|   |   |-- integration/    real server on ephemeral port + real subprocesses
|   |   |-- security/       injection, flood, malformed-frame, lockout suites
|   |   |-- contract/       validates against /protocol schemas and fixtures
|   |   |-- e2e/            daemon + mock phone client, full session scripts
|-- mobile/
|   |-- pubspec.yaml, analysis_options.yaml, l10n.yaml, build.yaml
|   |-- android/, ios/, assets/(icons/, fonts/)
|   |-- lib/
|   |   |-- main.dart, bootstrap.dart
|   |   |-- app/            app.dart, router.dart, theme/(app_theme.dart, tokens.dart)
|   |   |-- core/           constants/, errors/(failure.dart), result.dart, logging/,
|   |   |                   haptics/(haptic_service.dart), platform/, utils/
|   |   |-- domain/         entities/, repositories/(interfaces), usecases/
|   |   |-- data/
|   |   |   |-- protocol/   envelope.dart, codec.dart, dto/(freezed models), proofs.dart
|   |   |   |-- network/    deckhand_client.dart, pinned_http_client.dart,
|   |   |   |               request_tracker.dart, reconnect_policy.dart
|   |   |   |-- discovery/  mdns_scanner.dart
|   |   |   |-- storage/    secure_store.dart, prefs_store.dart
|   |   |   |-- repositories/ (implementations of domain interfaces)
|   |   |-- features/       each has presentation/ and application/
|   |   |   |-- onboarding/, discovery/, pairing/, connection/, deck/, actions/,
|   |   |   |   runs/, telemetry/, alerts/, settings/
|   |   |-- shared/         widgets/, extensions/
|   |   |-- l10n/           app_en.arb
|   |-- test/               unit/, widget/, golden/, fixtures/, helpers/
|   |-- integration_test/
|-- tools/
|   |-- mock_daemon/        scripted fake daemon for mobile development and tests
|   |-- loadtest/           session flood and log flood generators
|   |-- scripts/            bootstrap.sh, check_imports.py, bump_version.py, record_session.py
|-- .editorconfig, .gitattributes, .gitignore, .gitleaks.toml, .pre-commit-config.yaml
|-- CHANGELOG.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE, README.md, SECURITY.md
|-- Makefile, PROGRESS.md
```

### 5.2 Daemon module responsibilities

- `bootstrap`: builds the object graph (the only composition root), starts and stops services in order.
- `cli`: Typer commands: `serve`, `pair`, `devices list|revoke`, `actions validate|list|reload`, `tls show|rotate`, `autostart enable|disable`, `doctor`. CLI talks to a running daemon through `control`.
- `config`: loads and validates `config.toml` with pydantic; resolves platform paths; never touches `actions.yaml`.
- `core`: error base classes, ID generation (ULID-style), injectable clock, in-process event bus, lifecycle manager, token-bucket limiter, ring buffer, atomic file writes.
- `platform`: OS-specific facts behind an interface (config/state/log dirs, autostart, elevation check, process-group helpers).
- `protocol`: pydantic models for every message, envelope encode/decode, error registry, version negotiation. No I/O.
- `transport`: websockets server, TLS context, source-IP guard, session objects, bounded outbox with priorities, router mapping message types to handlers. Handlers are thin and contain no business logic.
- `security`: pairing state machine, token issue/verify, device store, lockout tracker, audit logger, redaction filter, crypto helpers.
- `actions`: parse and validate `actions.yaml`, registry with reload, param validation, argv templating, macro expansion, public metadata projection (`ActionMeta`).
- `process`: runner abstraction (POSIX, Windows, pty variants), run manager (limits, timeouts, escalation), per-run log ring buffer, signal mapping.
- `status`: probe implementations and a scheduler that dedupes probes and emits changes.
- `telemetry`: sampler loop, provider interface and implementations, capability detection, frame assembly.
- `alerts`: rule model, evaluation engine with hysteresis, persistent rule store, optional notifiers.
- `layout`: layout model, validation against the action registry, atomic persistence.
- `discovery`: mDNS registration and interface-change handling.
- `control`: loopback JSON-RPC server (127.0.0.1:47801, token file) and its client used by the CLI and tray.
- `tray`: pystray app, icon states, spawns the pairing window subprocess.

### 5.3 Mobile module responsibilities

- `app`: root widget, router (go\_router), theme and design tokens.
- `core`: Result type, Failure hierarchy, logging, haptics service (wraps `vibration` plus `HapticFeedback` fallback), constants.
- `domain`: entities (Host, Action, ParamSpec, Run, TelemetryFrame, Layout, AlertRule), repository interfaces, small use cases (PairDevice, RunAction, SaveLayout).
- `data/protocol`: DTOs and codec; `proofs.dart` implements the pairing HMAC proofs; unit-tested against `/protocol/fixtures`.
- `data/network`: `DeckhandClient` (connection state machine, request/response correlation, event streams), `PinnedHttpClient`, reconnect policy.
- `data/discovery`: mDNS scanner wrapper. `data/storage`: secure and plain stores.
- `features/*`: screens and Riverpod controllers per Section 10.

### 5.4 Makefile targets

`make setup` (create venv, `pub get`, install hooks), `make check` (everything below), `make lint`, `make fmt`, `make typecheck`, `make daemon-test`, `make mobile-test`, `make protocol-check`, `make import-check`, `make run-daemon`, `make mock-daemon`, `make package-daemon`, `make audit`.

### 5.5 Conventions

- Conventional Commits (`feat(daemon): ...`). Trunk-based development, short-lived branches, squash merge.
- SemVer for app releases. The protocol has its own integer version (Section 7.3).
- Python: `snake_case`, one class per file when the class is large, `__all__` in package `__init__`. Dart: `lower_snake_case` files, `UpperCamelCase` types.
- Every package has a short README or module docstring stating its single responsibility and what it may import.

## 6. Technology Stack

### 6.1 Daemon

Python 3.11+. Versions are pinned in a lockfile (`uv.lock` or `requirements.lock`) at implementation time.

- Runtime: `websockets` (>=13, asyncio API), `pydantic` v2, `PyYAML` (`safe_load` only), `psutil`, `zeroconf` (`AsyncZeroconf`), `cryptography` (certificate generation), `platformdirs`, `typer`, `qrcode` + `Pillow`, `pystray`, `filelock`, `httpx` (optional: HTTP probe and ntfy notifier). Standard library `tomllib` for TOML.
- Optional extras: `[nvidia]` -> `nvidia-ml-py`; `[pty]` -> `ptyprocess` (POSIX) and `pywinpty` (Windows) via environment markers.
- Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `hypothesis`, `jsonschema`, `mypy`, `ruff`, `import-linter`, `bandit`, `pip-audit`, `pre-commit`.

### 6.2 Mobile

Flutter stable, Dart 3.x, null safety, Material 3.

- State: `flutter_riverpod` (providers and `AsyncNotifier`; no code generation for Riverpod). Routing: `go_router`.
- Models: `freezed`, `json_serializable`, `build_runner`.
- Network: `web_socket_channel` (`IOWebSocketChannel` with a custom `HttpClient`). Crypto: `crypto` (SHA-256, HMAC). IDs: `uuid`.
- Storage: `flutter_secure_storage`, `shared_preferences`.
- Discovery and pairing: `nsd`, `mobile_scanner` (QR).
- UI: `fl_chart`, `xterm` (pty terminal view), `reorderable_grid_view` (or a small custom `Draggable` grid if unmaintained), `wakelock_plus`, `local_auth` (optional app lock), `connectivity_plus`, `vibration`, `intl` + `flutter_localizations`, `logger`.
- Dev: `flutter_test`, `integration_test`, `mocktail`, `very_good_analysis`.

### 6.3 Platform configuration (mobile)

- Android: `INTERNET`, `VIBRATE`, `CAMERA`, `ACCESS_NETWORK_STATE`, `CHANGE_WIFI_MULTICAST_STATE`; `usesCleartextTraffic=false`; `allowBackup=false`; minSdk 26.
- iOS: `NSLocalNetworkUsageDescription`; `NSBonjourServices` = `_deckhand._tcp`; `NSCameraUsageDescription`; `NSFaceIDUsageDescription` (if app lock is on).

## 7. Wire Protocol Specification

### 7.1 Transport

- `wss://<host>:47800/v1/ws` (port configurable). WebSocket subprotocol `deckhand.v1`.
- Text frames only; one UTF-8 JSON message per frame. Binary frames are rejected (close 1003).
- PROTO-001: The daemon listens on one port. The loopback control channel (47801) is a separate, non-WebSocket interface.

### 7.2 Envelope

Every message has this shape:

```json
{"v":1,"type":"ACTION_RUN","id":"c-8f2a","ts":1760000000123,"payload":{"action_id":"docker-up","params":{}}}
```

- `v`: integer protocol version. `type`: SCREAMING\_SNAKE\_CASE message type.
- `id`: sender-generated string (max 64 chars), unique within the session. `reply_to`: optional, the `id` of the request being answered.
- `ts`: sender wall clock in milliseconds since the epoch. Informational only; never used for security.
- `payload`: JSON object, possibly empty.
- PROTO-002: Receivers ignore unknown top-level fields and unknown payload fields. Receivers answer an unknown request type with `ERROR PROTO_UNKNOWN_TYPE`; a client logs and ignores an unknown server event.

### 7.3 Versioning

- PROTO-003: Adding optional fields or new message types is non-breaking within a version.
- PROTO-004: Removing or renaming a field, or changing its meaning, is breaking and bumps `v`.
- `HELLO.protocol_versions` lists what the daemon supports; `AUTH.protocol_version` picks one; `AUTH_OK.protocol_version` confirms it. No overlap -> `AUTH_FAIL PROTO_VERSION_UNSUPPORTED`.
- `protocol/VERSION` holds the current version; CI fails if schemas change without a recorded decision in `docs/adr/` for breaking changes.

### 7.4 Connection lifecycle

1. TCP + TLS handshake. Source-IP guard runs at accept (SEC-011).
2. Daemon sends `HELLO` immediately.
3. Client sends `AUTH` (known device) or `PAIR_REQUEST` (new device). Deadline 5 s (10 s pairing).
4. On success the daemon sends `AUTH_OK`, then a full `SNAPSHOT`.
5. Client optionally sends `TELEMETRY_SUBSCRIBE` and `RUN_ATTACH`.
6. Either side closes; the daemon sends `SERVER_SHUTDOWN` first when stopping.

### 7.5 Message catalog

**Connection and auth**

| Dir | Type | Payload | Notes |
| :-- | :-- | :-- | :-- |
| S->C | HELLO | server\_id, server\_name, daemon\_version, protocol\_versions\[\], os, arch, tls\_fp, pairing\_open, auth\_required | First message |
| C->S | AUTH | device\_id, token, protocol\_version, client{app\_version, platform} | 5 s deadline |
| S->C | AUTH\_OK | session\_id, device\_name, protocol\_version, server\_time\_ms, limits{} | Followed by SNAPSHOT |
| S->C | AUTH\_FAIL | code, retry\_after\_sec? | Then close 4401 |
| C->S | PAIR\_REQUEST | device\_id, device\_name, client\_nonce | Window must be open |
| S->C | PAIR\_CHALLENGE | server\_nonce |  |
| C->S | PAIR\_PROOF | proof | Section 4.4 |
| S->C | PAIR\_OK | device\_token, server\_proof |  |
| S->C | PAIR\_FAIL | code | Then close 4401 |
| C->S | UNPAIR\_SELF | (empty) | Removes this device |
| both | PING, PONG | nonce | Optional, for RTT display |
| S->C | SERVER\_SHUTDOWN | reason, reconnect\_after\_sec | Before close 4503 |
| S->C | ERROR | code, message, details? | `reply_to` set when answering |

**State sync**

| Dir | Type | Payload | Notes |
| :-- | :-- | :-- | :-- |
| C->S | SNAPSHOT\_GET | (empty) | Manual refresh |
| S->C | SNAPSHOT | capabilities, actions\[ActionMeta\], layout, statuses\[\], active\_runs\[RunState\], alert\_rules{rev, rules\[\]}, active\_alerts\[\] | After AUTH\_OK and on request |
| S->C | CONFIG\_CHANGED | scope (actions, layout, alerts), rev | Client re-requests SNAPSHOT |

**Actions and runs**

| Dir | Type | Payload | Notes |
| :-- | :-- | :-- | :-- |
| C->S | ACTION\_RUN | action\_id, params, confirmed? |  |
| S->C | ACTION\_ACCEPTED | run\_id | Sent when the run is registered, not when it finishes |
| S->C | RUN\_STATE | RunState | Broadcast to all sessions |
| C->S | RUN\_ATTACH | run\_id, since\_seq? | Server replays buffered logs, then streams live |
| C->S | RUN\_DETACH | run\_id |  |
| S->C | PROCESS\_LOG | run\_id, lines\[{seq, stream, ts, text}\], truncated? | Pipe mode |
| S->C | PROCESS\_LOG\_GAP | run\_id, from\_seq, to\_seq | Lines dropped under backpressure |
| S->C | PTY\_DATA | run\_id, seq, data | Pty mode, raw terminal text |
| C->S | RUN\_SIGNAL | run\_id, signal (INTERRUPT, TERMINATE, KILL) |  |
| C->S | RUN\_STDIN | run\_id, data, append\_newline | Interactive runs only |
| C->S | RUN\_RESIZE | run\_id, rows, cols | Pty runs only |
| C->S | RUNS\_LIST | limit? |  |
| S->C | RUNS | runs\[RunState\] |  |

The draft's `PROCESS_EXIT` is folded into `RUN_STATE` terminal states. The session that started a run is auto-attached; others call `RUN_ATTACH`. All sessions always receive `RUN_STATE`.

**Telemetry, status, layout, alerts**

| Dir | Type | Payload | Notes |
| :-- | :-- | :-- | :-- |
| C->S | TELEMETRY\_SUBSCRIBE | interval\_ms (clamped 500-5000), metrics? |  |
| C->S | TELEMETRY\_UNSUBSCRIBE | (empty) |  |
| S->C | TELEMETRY\_UPDATE | seq, data{} | Lossy, latest wins |
| S->C | STATUS\_UPDATE | items\[{action\_id, state, detail?, since\_ms}\] | Only on change |
| C->S | LAYOUT\_SET | base\_rev, layout |  |
| S->C | LAYOUT\_OK | rev | Or `ERROR LAYOUT_CONFLICT` with `details.current` |
| C->S | ALERT\_RULES\_SET | base\_rev, rules\[\] |  |
| S->C | ALERT\_RULES\_OK | rev |  |
| S->C | ALERT\_RAISED | alert\_id, rule\_id, metric, value, threshold, severity, since\_ms |  |
| S->C | ALERT\_CLEARED | alert\_id, rule\_id, value |  |

### 7.6 Shared payload shapes

**ActionMeta** (what the phone may know about an action): `id, label, icon, category, description, mode (pipe|pty), interactive, confirm, parallel, has_status, params[ParamSpec]`. The `run` block (argv, cwd, env, shell) is NEVER sent.

**ParamSpec**: `name, label, type (string|int|number|bool|enum), required, default?, choices?[], min?, max?, max_length?, pattern?, secret?, placeholder?`. The phone may pre-validate; the daemon is authoritative.

**RunState**: `run_id, action_id, state, started_at_ms, ended_at_ms?, exit_code?, signal?, reason?, step?{index,total}`. States: `STARTING, RUNNING, STOPPING, EXITED, FAILED_TO_START, TIMED_OUT, CANCELLED`. Terminal: all except STARTING, RUNNING, STOPPING. `EXITED` carries any exit code (0 is success).

**Layout**: `{rev, pages:[{id, title, cols, rows, cells:[{col, row, col_span?, row_span?, kind (action|widget), action_id?, widget? (cpu|ram|gpu|disk|net|battery)}]}]}`. Max 12 pages, 6 cols, 8 rows, 256 KiB serialized.

**AlertRule**: `{id, metric, op (>, >=, <, <=), threshold, for_sec, clear_margin, cooldown_sec, severity (info|warning|critical), enabled}`.

**Capabilities**: `{os, telemetry:{cpu_temp, gpu, gpu_vendors[], battery, disk, net}, features:{pty, signals[], probes[], notifier}}`. The phone hides UI for anything not supported.

**Telemetry frame** (`TELEMETRY_UPDATE.payload`). Units are fixed: percent as 0-100 floats, sizes in bytes, rates in bytes per second, temperatures in Celsius, times in ms. Unsupported metrics are `null`.

```json
{"seq":812,"data":{"cpu":{"usage_percent":34.2,"per_core_percent":[30.1,41.0],"temp_celsius":58.0,"freq_mhz":3600},"memory":{"usage_percent":68.5,"used_bytes":11702000000,"total_bytes":17179869184,"available_bytes":5400000000,"swap_percent":3.1},"disk":{"read_bytes_per_sec":1200000,"write_bytes_per_sec":340000,"volumes":[{"mount":"C:","usage_percent":71.2}]},"net":{"rx_bytes_per_sec":52000,"tx_bytes_per_sec":8000},"gpu":[{"index":0,"name":"GPU 0","usage_percent":12.0,"vram_used_bytes":2100000000,"vram_total_bytes":8589934592,"temp_celsius":49.0}],"battery":{"percent":92,"is_plugged":true,"secs_left":null}}}
```

**Process log** (`PROCESS_LOG.payload`):

```json
{"run_id":"01J9Z3","lines":[{"seq":41,"stream":"stdout","ts":1760000001500,"text":"Container db-postgres Started"}]}
```

**Error** (`ERROR.payload`):

```json
{"code":"PARAM_INVALID","message":"Invalid parameters","details":{"errors":[{"name":"branch","reason":"does not match pattern"}]}}
```

### 7.7 Error and close codes

- Error codes: `PROTO_MALFORMED, PROTO_UNKNOWN_TYPE, PROTO_VERSION_UNSUPPORTED, AUTH_REQUIRED, AUTH_INVALID_TOKEN, AUTH_REVOKED, AUTH_LOCKED_OUT, PAIR_WINDOW_CLOSED, PAIR_BAD_PROOF, PAIR_LOCKED_OUT, RATE_LIMITED, ACTION_NOT_FOUND, PARAM_INVALID, ACTION_BUSY, RUN_LIMIT_REACHED, RUN_NOT_FOUND, RUN_NOT_ACTIVE, RUN_NOT_INTERACTIVE, SIGNAL_UNSUPPORTED, LAYOUT_CONFLICT, LAYOUT_INVALID, ALERT_RULES_INVALID, UNSUPPORTED_ON_HOST, SHUTTING_DOWN, INTERNAL_ERROR`.
- WebSocket close codes: 1000 normal, 1001 going away, 1003 binary not supported, 1009 message too big, 1011 internal error, 4400 protocol error, 4401 authentication failed or revoked, 4408 authentication timeout, 4429 rate limited, 4503 daemon shutting down.
- PROTO-005: Error messages MUST NOT leak internal paths, argv, environment, or stack traces. Details go to the daemon log only.

### 7.8 Ordering, delivery, and backpressure

- WebSocket gives in-order delivery per connection. There are no application-level acks except request/reply.
- Per-run `seq` is monotonic and starts at 1; a client detects gaps by `seq` and `PROCESS_LOG_GAP`.
- Each session has a bounded outbox (1000 frames or 1 MiB, whichever first) with three priorities:
  - P0 (never dropped): ERROR, AUTH\_*, PAIR\_*, RUN\_STATE, ALERT\_\*, STATUS\_UPDATE (coalesced per action), CONFIG\_CHANGED, SERVER\_SHUTDOWN.
  - P1 (dropped oldest-first on overflow, replaced by a single PROCESS\_LOG\_GAP): PROCESS\_LOG, PTY\_DATA.
  - P2 (latest wins, older queued frame replaced): TELEMETRY\_UPDATE.
- If a session cannot drain P0 within 10 s it is closed with 1011.
- Log batching: flush when 50 ms elapsed, 100 lines, or 16 KiB, whichever first. A single line over 8 KiB is truncated with a marker and `truncated: true`.

### 7.9 Keepalive, timeouts, reconnect

- Server sends WebSocket ping every 15 s with a 10 s timeout. The client sets `pingInterval` to 15 s.
- Client request timeout: 10 s for request/reply messages.
- Client reconnect: exponential backoff 1, 2, 4, 8, 16, 30 s (cap 30 s), +/-20 % jitter. Immediate retry on app resume or network change. A user-initiated disconnect disables auto-reconnect.
- After reconnect the client receives a fresh SNAPSHOT and re-sends `RUN_ATTACH` with `since_seq` for any run it was viewing.

### 7.10 Contract testing

- PROTO-006: `/protocol/schemas` holds JSON Schema for the envelope and every message. `/protocol/fixtures` holds valid and invalid examples plus recorded full-session transcripts.
- PROTO-007: The daemon test suite and the mobile test suite both validate their encoders and decoders against the same fixtures. A change to a schema without updated fixtures fails `make protocol-check`.
- PROTO-008: `tools/mock_daemon` replays session transcripts so mobile screens can be developed and tested without a real daemon.

## 8. Configuration and Data Formats

### 8.1 Locations

Resolved with `platformdirs`; overridable with the `DECKHAND_HOME` environment variable (used by tests).

- Config dir (user-edited): `config.toml`, `actions.yaml`. Windows `%APPDATA%\Deckhand`, Linux `~/.config/deckhand`, macOS `~/Library/Application Support/Deckhand`.
- State dir (daemon-written): `layout.json`, `alerts.json`, `devices.json`, `tls/cert.pem`, `tls/key.pem`, `control.token`, `deckhand.lock`. Windows `%LOCALAPPDATA%\Deckhand`, Linux `~/.local/state/deckhand`, macOS `~/Library/Application Support/Deckhand/state`.
- Log dir: `deckhand.log`, `audit.log`.
- All daemon-written JSON files are written atomically (temp file, fsync, rename) and carry a top-level `rev` integer where clients can edit them.

### 8.2 `config.toml`

Every key is optional; the defaults below apply. Unknown keys are a validation error.

```toml
[server]
bind = "0.0.0.0"
port = 47800
allowed_networks = ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "fe80::/10", "fc00::/7"]
max_connections = 8
max_unauthenticated = 4

[security]
allow_shell = false          # enables run.type = shell
remote_layout_edit = true    # LAYOUT_SET
remote_alert_edit = true     # ALERT_RULES_SET

[runs]
max_concurrent = 16
default_timeout_sec = 0      # 0 = no timeout
kill_grace_sec = 5
kill_on_exit = true
log_buffer_lines = 5000
retain_finished = 20
retain_minutes = 30

[telemetry]
default_interval_ms = 1000
libre_hardware_monitor_url = ""   # e.g. http://127.0.0.1:8085/data.json (Windows, opt-in)

[mdns]
enabled = true

[actions]
watch = true                 # poll actions.yaml mtime every 2 s

[logging]
level = "INFO"
json_file = true

[notifier]
type = "none"                # none | ntfy (Phase 6)
url = ""
```

### 8.3 `actions.yaml`

This file is the security boundary. It is edited only on the PC, loaded with `yaml.safe_load`, and validated by pydantic.

```yaml
version: 1
actions:
  - id: docker-up
    label: Docker Up
    icon: docker
    category: Docker
    run:
      type: exec
      argv: [docker, compose, up, -d]
      cwd: ~/projects/api
    status:
      probe: docker_container
      target: api-db-1

  - id: docker-down
    label: Docker Down
    icon: stop
    category: Docker
    confirm: true
    run:
      type: exec
      argv: [docker, compose, down]
      cwd: ~/projects/api

  - id: git-checkout
    label: Checkout
    icon: git-branch
    category: Git
    run:
      type: exec
      argv: [git, checkout, '{{branch}}']
      cwd: ~/projects/api
    params:
      - name: branch
        label: Branch
        type: string
        required: true
        max_length: 64
        pattern: '^[A-Za-z0-9._/-]+$'

  - id: build
    label: Build
    icon: hammer
    category: Build
    mode: pty
    timeout_sec: 1800
    run:
      type: exec
      argv: [npm, run, build]
      cwd: ~/projects/web

  - id: python-repl
    label: Python REPL
    icon: terminal
    mode: pty
    interactive: true
    run:
      type: exec
      argv: [python3]

  - id: morning
    label: Morning Setup
    icon: sun
    run:
      type: macro
      on_error: stop
      steps:
        - action: docker-up
        - action: git-checkout
          params: {branch: main}
```

**Action fields.** `id` (required, unique, `^[a-z0-9][a-z0-9_-]{0,47}$`), `label` (required, max 32), `icon` (built-in key or `material:<name>`, default `bolt`), `category` (max 24), `description` (max 200), `run` (required), `params` (list), `confirm` (default false), `parallel` (default false), `interactive` (default false; pty is always interactive), `mode` (`pipe` or `pty`, default `pipe`), `timeout_sec` (default from config; 0 = none), `status` (optional probe).

**Run types.**

- `exec`: `argv` (non-empty list of strings), optional `cwd`, optional `env` map. Executable resolved with `shutil.which` at run time.
- `script`: `path`, optional `args`, optional `interpreter`, optional `sha256`. Without `interpreter`, by extension: `.sh` -> `sh`, `.bat` and `.cmd` -> `cmd /c`, `.ps1` -> `powershell -NoProfile -File`, anything else is executed directly. If `sha256` is set and the file hash differs, the run fails with reason `script_hash_mismatch`.
- `shell`: `command` string. Disabled unless `security.allow_shell = true`. Runs via `sh -c` or `cmd /c`. Params are NEVER interpolated; they are exposed as environment variables `DECKHAND_PARAM_<UPPERCASE_NAME>`.
- `macro`: `steps` (1-20, each `{action, params?}`), `on_error` (`stop` default, or `continue`). Steps may reference only non-macro actions (no nesting, so no cycles). Step params may be literals or `{{name}}` passthrough of the macro's own params.

**Param fields.** `name` (`^[a-z][a-z0-9_]{0,31}$`), `label`, `type` (`string|int|number|bool|enum`), `required`, `default`, `choices` (required for enum), `min`/`max` (int, number), `max_length` (string, default 128, max 1024), `pattern` (full-match regex), `secret` (bool), `allow_leading_dash` (string, default false), `placeholder`.

**Validation rules (load time).**

- Unique ids; macro steps and probe targets resolve; every `{{name}}` refers to a declared param.
- A placeholder is never allowed in `argv[0]`, `script.path`, or `interpreter`.
- Placeholders are allowed in other argv elements, `args`, `cwd`, and `env` values. Substitution is textual inside a single element and happens AFTER param validation; values are never split on whitespace and never passed to a shell (SEC-004).
- Optional params without a `default` are rejected if their placeholder is used.
- `~` and `$VAR` are expanded only in `cwd` and `script.path`, by the loader, never in param values.

**Run-time param validation (SEC-003).** Required present; no unknown names; correct type; strings: no NUL or control characters, within `max_length`, full match of `pattern`, and no leading `-` unless `allow_leading_dash` (this blocks argument injection such as a branch named `--upload-pack=...`); ints and numbers within `min`/`max`; enum within `choices`; bool is true or false. Failures return `PARAM_INVALID` with per-param reasons.

**Reload.** `deckhand actions reload`, the tray menu, or mtime polling (if `actions.watch`). A file that fails validation leaves the previous registry active; the error is logged and shown in the tray. A successful reload bumps `actions_rev`, prunes layout cells pointing at deleted actions, and sends `CONFIG_CHANGED` to sessions.

**Status probes.** `probe` is one of: `process` (`target` = executable name, case-insensitive), `tcp_port` (`target` = port; loopback only), `http` (`target` = URL; loopback only; GET; up if status is 2xx/3xx or equals `expect_status`), `docker_container` (`target` = container name; uses `docker inspect`; up if running), `run_state` (default when no probe: blue while running, otherwise none). `interval_sec` default 5, minimum 2.

### 8.4 `layout.json`

```json
{"rev":3,"pages":[{"id":"p1","title":"Main","cols":3,"rows":4,"cells":[{"col":0,"row":0,"kind":"action","action_id":"docker-up"},{"col":2,"row":0,"kind":"widget","widget":"cpu"}]}]}
```

Rules: cells must not overlap or exceed the grid; `action_id` must exist; a given action may appear at most once per page. On first run the daemon generates a default layout: all actions in definition order on 3x4 pages. `LAYOUT_SET` uses optimistic concurrency on `rev`; a stale `base_rev` returns `LAYOUT_CONFLICT` with the current layout.

### 8.5 `alerts.json`

`{rev, rules[AlertRule]}`. Metric paths are dotted paths into the telemetry frame; array elements by index (`cpu.temp_celsius`, `gpu.0.temp_celsius`, `memory.usage_percent`). Rules whose metric is currently `null` are skipped. Seeded defaults: CPU temperature above 85 for 5 s (clear margin 5, cooldown 60, warning); memory above 95 % for 10 s (warning); GPU 0 temperature above 85 for 5 s (warning).

## 9. Daemon Functional Requirements

### 9.1 Action service

- FR-D-101: Expose `ActionMeta` for each action to authenticated sessions (never argv, cwd, env, shell commands).
- FR-D-102: `ACTION_RUN` resolves the action, validates params, builds argv, and starts a run; returns `ACTION_ACCEPTED` within 150 ms (p95) or an `ERROR`.
- FR-D-103: An action already running with `parallel: false` returns `ACTION_BUSY`. Global limit returns `RUN_LIMIT_REACHED`.
- FR-D-104: Macro runs expose one `RunState` with `step{index,total}`; log lines are prefixed with the step label.
- FR-D-105: Every started run is audited (Section 4.8).

### 9.2 Process execution

- FR-D-201: A `ProcessRunner` interface with `PosixRunner`, `WindowsRunner`, and pty variants. `factory.py` selects by OS and `mode`.
- FR-D-202: Spawn without a shell (`asyncio.create_subprocess_exec`). POSIX: `start_new_session=True`. Windows: `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`. Stdin is `DEVNULL` unless the action is interactive.
- FR-D-203: Environment is the daemon's environment plus the action's `env`. Missing executable -> `FAILED_TO_START` with reason `executable_not_found`.
- FR-D-204: Run state machine: `STARTING -> RUNNING -> (EXITED | TIMED_OUT | CANCELLED)`, with `STOPPING` while a stop is in progress, and `FAILED_TO_START` from `STARTING`. Every transition emits `RUN_STATE`.
- FR-D-205: Signal mapping (signals are abstract at the protocol level): | Signal | POSIX (pipe) | Windows (pipe) | Pty (either OS) | | :--- | :--- | :--- | :--- | | INTERRUPT | `killpg(SIGINT)` | `CTRL_BREAK_EVENT` to the process group | write byte 0x03 to the pty | | TERMINATE | `killpg(SIGTERM)` | `terminate()` plus psutil children | terminate the pty child tree | | KILL | `killpg(SIGKILL)` | psutil recursive kill | kill the pty child tree |
- FR-D-206: TERMINATE escalates to KILL after `kill_grace_sec` if the process is still alive. INTERRUPT never auto-escalates. Timeout triggers TERMINATE, then KILL, and ends in `TIMED_OUT`.
- FR-D-207: `RUN_STDIN` is accepted only for interactive runs (else `RUN_NOT_INTERACTIVE`) and only while the run is active (else `RUN_NOT_ACTIVE`).
- FR-D-208: Pipe mode: read stdout and stderr concurrently, decode UTF-8 with `errors=replace`, split on `\n`, `\r\n`, and lone `\r` (progress output is coalesced by batching). ANSI sequences pass through unchanged. Pty mode: stream raw decoded text as `PTY_DATA`, support `RUN_RESIZE`. Note in docs: many tools buffer when piped, so pty mode is recommended for build tools.
- FR-D-209: Each run keeps a ring buffer (default 5000 lines, hard cap 8 MiB). `RUN_ATTACH` with `since_seq` replays from the buffer; lines already evicted produce a `PROCESS_LOG_GAP`.
- FR-D-210: Finished runs are retained (default 20 runs or 30 min) for `RUNS_LIST` and late attach.
- FR-D-211: With `kill_on_exit`, shutdown terminates all active runs. On Windows the daemon SHOULD place children in a Job Object with `KILL_ON_JOB_CLOSE` so they die if the daemon crashes.
- FR-D-212: Child CPU or memory limits are out of scope for v1.

### 9.3 Status probes

- FR-D-301: A scheduler runs each distinct probe once per interval regardless of how many sessions exist, with a concurrency cap of 4 and a per-probe timeout (1 s; 3 s for docker).
- FR-D-302: Probes run only while at least one session is authenticated.
- FR-D-303: `STATUS_UPDATE` is sent only on state change, and the full set is included in `SNAPSHOT`.
- FR-D-304: The `docker_container` probe runs `docker inspect` through the same no-shell exec path; if `docker` is not on PATH the state is `UNKNOWN` with detail `docker_not_found`.

### 9.4 Telemetry providers

- FR-D-401: A `SensorProvider` interface: `name`, `detect() -> capabilities`, `sample() -> partial frame`. `sample()` runs in the executor with an 800 ms timeout.
- FR-D-402: Providers: | Provider | Metrics | Platforms | Notes | | :--- | :--- | :--- | :--- | | PsutilProvider | CPU usage, per-core, frequency; memory and swap; disk IO and volumes; network rates; battery | All | Base provider | | LinuxHwmonProvider | CPU temperature | Linux | `psutil.sensors_temperatures()`; picks `coretemp`, `k10temp`, `zenpower`, `cpu_thermal` | | NvidiaProvider | GPU usage, VRAM, temperature | Windows, Linux | `nvidia-ml-py`; absent driver or library -> unsupported | | AmdSysfsProvider | GPU usage, VRAM, temperature | Linux (amdgpu) | Reads sysfs `gpu_busy_percent` and hwmon | | LibreHwMonitorProvider | CPU temperature, AMD/Intel GPU | Windows | Opt-in via `telemetry.libre_hardware_monitor_url` | | (none) | Temperatures, GPU | macOS | Reported as unsupported in v1 |
- FR-D-403: Unsupported metrics are `null` and flagged `false` in `capabilities`; the phone hides them.
- FR-D-404: A failing provider is logged once, marked degraded, and retried with exponential backoff up to 60 s. It never breaks the frame.
- FR-D-405: Rates come from counter deltas over monotonic time. `cpu_percent(interval=None)` is primed at startup so no call blocks.

### 9.5 Telemetry sampler

- FR-D-501: The sampler runs only while at least one session is subscribed OR at least one alert rule is enabled.
- FR-D-502: Tick interval is the smallest requested by any subscriber (clamped 500-5000 ms), default 1000 ms. Scheduling is drift-free (based on `loop.time()`). Providers sample concurrently.
- FR-D-503: Each frame has a monotonic `seq` and stays under 4 KiB. Each session receives frames at its own requested rate.

### 9.6 Alerts

- FR-D-601: A rule fires after its condition is continuously true for `for_sec`. It clears when the value crosses back past the threshold by `clear_margin` (hysteresis). After clearing, it cannot re-fire for `cooldown_sec`.
- FR-D-602: `ALERT_RAISED` and `ALERT_CLEARED` go to all authenticated sessions regardless of telemetry subscription. Active alerts are included in `SNAPSHOT`.
- FR-D-603: Alert state is in memory; rules persist in `alerts.json`.
- FR-D-604 (Phase 6, opt-in): A notifier posts a minimal message (hostname, metric, value) to a user-configured ntfy URL on `ALERT_RAISED`. HTTPS only unless the host is loopback. No other outbound traffic exists.

### 9.7 Discovery

- FR-D-701: Register `_deckhand._tcp.local.` with `AsyncZeroconf`; instance name `<hostname> (Deckhand)`; TXT: `v=1`, `id=<server_id>`, `name=<hostname>`, `fp=<first 16 hex of fingerprint>` (hint only), `pair=0|1`.
- FR-D-702: Advertise only on interfaces whose addresses fall in `allowed_networks`. Re-check interfaces every 30 s and re-register on change.
- FR-D-703: Discovery is a convenience only. Manual host entry MUST always work, and docs explain that multicast does not cross Tailscale or guest Wi-Fi with client isolation.

### 9.8 Tray and pairing UI

- FR-D-801: Tray icon states: idle, connected (N devices), pairing window open, error. Menu: status line, Pair new device, Devices (submenu with Revoke), Reload actions, Open config folder, Open logs, Pause listening, Quit.
- FR-D-802: Pair new device spawns `python -m deckhand.tray.pair_window`, a separate process with a Tk window showing the QR code, the grouped code, and a countdown. If Tk is unavailable it saves a PNG, opens it with the default viewer, and shows the code in a notification.
- FR-D-803: If no tray backend is available (common on minimal Linux), the daemon runs headless and logs a hint; all features remain reachable through the CLI.

### 9.9 CLI

| Command | Purpose |
| :-- | :-- |
| `deckhand serve [--no-tray] [--config PATH] [--insecure-dev] [--allow-elevated]` | Run the daemon |
| `deckhand pair [--cancel]` | Open a pairing window; print QR (terminal), code, addresses, expiry |
| `deckhand devices list`, `revoke <id>`, `rename <id> <name>` | Manage devices |
| `deckhand actions validate [PATH]`, `list`, `reload` | Manage actions |
| `deckhand tls show`, `tls rotate` | Inspect or rotate the certificate |
| `deckhand autostart enable`, `disable`, `status` | Login autostart |
| `deckhand doctor` | Diagnose ports, TLS files, permissions, config validity, providers, mDNS |
| `deckhand --version` | Version info |
| Exit codes: 0 ok, 1 general error, 2 usage, 3 invalid config, 4 daemon not running. |  |

### 9.10 Control channel

- FR-D-901: Loopback-only (127.0.0.1:47801) newline-delimited JSON-RPC 2.0. The first request must include the token from `control.token` (0600). Non-loopback peers are dropped.
- FR-D-902: Methods: `status`, `pair.open`, `pair.close`, `devices.list`, `devices.revoke`, `actions.reload`, `shutdown`.
- FR-D-903: It is separate from the WebSocket server and is never reachable from the network.

### 9.11 Lifecycle

- FR-D-1001: Startup order: config, logging, single-instance lock (`filelock`), elevation and file-permission checks, TLS material, device store and audit log, action registry, layout and alert stores, process manager, status scheduler, telemetry sampler (idle), transport, discovery, control server, tray. Shutdown is the reverse.
- FR-D-1002: Graceful shutdown on SIGINT/SIGTERM (POSIX), console control events (Windows), tray Quit, or `shutdown` RPC: stop accepting, send `SERVER_SHUTDOWN`, close sessions with 4503, apply `kill_on_exit`, unregister mDNS, flush logs. Hard cap 10 s.
- FR-D-1003: Background services (sampler, scheduler, discovery) are supervised and restart with backoff on unexpected exceptions. A transport failure exits non-zero.
- FR-D-1004: A second instance exits with a clear message and exit code 1.

### 9.12 Logging

- FR-D-1101: Standard `logging`. Console is human-readable. The file log is JSON lines, rotating (5 files x 5 MB).
- FR-D-1102: Every record carries `session_id`, `device_id`, `run_id`, and `action_id` where applicable, via `contextvars`.
- FR-D-1103: The redaction filter (SEC-016) is installed on all handlers.

## 10. Mobile Functional Requirements

### 10.1 Screens and navigation

- Onboarding (first launch only): purpose, local-network permission rationale.
- Hosts: saved hosts with live status chips; add by discovery, QR, or manual entry.
- Discovery: mDNS results plus manual entry (address or MagicDNS name, port).
- Pairing: QR scan or typed code; progress; specific errors.
- Main shell with bottom navigation: **Deck**, **Stats**, **Runs**, **Settings**.
- Alerts list (from the app bar bell).
- Run detail / terminal (bottom sheet from Deck, full screen from Runs).
- Routing via `go_router`; the shell keeps tab state.

### 10.2 Connection state machine

`Idle -> Connecting -> VerifyingCertificate -> Authenticating -> Syncing -> Online`. From Online: `Reconnecting(attempt)` on loss. Terminal-ish states needing the user:

- `PinMismatch`: the presented certificate differs from the pinned one. Show a blocking warning with the old fingerprint; offer Forget and Re-pair. Never auto-trust.
- `AuthRevoked`: this device was revoked; go to re-pair.
- `VersionUnsupported`: tell the user which side needs updating.
- `Unreachable`: show last error and retry controls. A connection chip in the app bar always shows the state. While not Online, the Deck remains visible but action cards are disabled.

### 10.3 Deck

- FR-M-101: Paged grid driven by `Layout`. Per page `cols` 1-6 and `rows` 1-8; default 3x4 portrait. Cells hold action cards or telemetry widgets.
- FR-M-102: Action card shows icon, label, status ring (green up, red down, grey unknown, none without a probe), running spinner with elapsed time, and a result badge for 10 s after completion (check or cross with exit code). Minimum touch target 56 dp.
- FR-M-103: Tap: if `confirm`, show a confirmation dialog; if the action has required params without defaults, open the params sheet; otherwise run. Tap on a running card opens its run detail.
- FR-M-104: Long-press opens the params sheet (actions with params) or a menu (Run, Last output, Details). This resolves the draft's long-press conflict.
- FR-M-105: **Edit mode** (app bar toggle) enables drag-to-reorder, page add/remove/rename, per-page grid size, adding telemetry widgets, and an Add action picker for actions not yet placed. Save sends `LAYOUT_SET`; on `LAYOUT_CONFLICT` the app reloads the layout and shows a message.
- FR-M-106: The params sheet is generated from `ParamSpec`: text field with pattern and length validation, numeric field with range, switch, dropdown. Last values are remembered per action locally, except params marked `secret`.

### 10.4 Runs and terminal

- FR-M-201: A draggable bottom sheet (peek, half, full) and a Runs tab list active runs first, then recent ones, as chips with state.
- FR-M-202: Pipe-mode log view: virtualized list, ANSI SGR colors rendered, other escapes stripped, up to 20,000 lines in memory (oldest dropped), auto-scroll that pauses when the user scrolls up with a Jump to latest button, word wrap toggle, copy selection or all, clear view.
- FR-M-203: Control bar: Interrupt (Ctrl+C), Terminate, Kill (always asks to confirm), and a text field with Send for interactive runs. Controls enable and disable by run state and capabilities.
- FR-M-204: Pty runs use the `xterm` widget with a soft-key row (Esc, Tab, Ctrl toggle, arrows, pipe, slash, dash) and send `RUN_RESIZE` when the viewport changes.
- FR-M-205: Finished runs show exit code, duration, and Run again. Disconnected sessions show a banner that the process keeps running on the PC; after reconnect the app re-attaches with `since_seq`.
- FR-M-206 (Phase 6): in-log search.

### 10.5 Stats

- FR-M-301: Tiles for CPU (radial gauge, temperature, 60 s sparkline), memory, each GPU, disk IO, network, battery. Tiles for unsupported metrics are not shown; a Not available on this host note is shown once in the screen footer.
- FR-M-302: The app keeps 120 samples per series and draws 60 s `fl_chart` line charts. Repaints are isolated with `RepaintBoundary`.
- FR-M-303: The app subscribes to telemetry only while a Stats tab or a telemetry widget is visible, and unsubscribes otherwise.
- FR-M-304: Values are formatted humanely (GiB, MB/s, degrees Celsius).

### 10.6 Alerts and haptics

- FR-M-401: `ALERT_RAISED` while the app is in the foreground shows a banner and vibrates; `ALERT_CLEARED` removes the banner. Alerts raised while the app was closed appear in the Alerts list from `SNAPSHOT.active_alerts` on next connect. Background delivery is not supported in v1 (Section 9.6 notifier is the Phase 6 path).
- FR-M-402: Haptic patterns: tap = light; success = two short pulses; failure = one long pulse; warning = three pulses; critical = two strong 500 ms pulses. Implemented with `vibration` (amplitude where available) and `HapticFeedback` as the fallback. Everything respects the Haptics setting and has a visual equivalent.
- FR-M-403: The Alert rules editor lets the user pick a metric from advertised capabilities, an operator, threshold, duration, and severity, then sends `ALERT_RULES_SET`.

### 10.7 Pairing and discovery UX

- FR-M-501: Scan QR: parse `deckhand://pair?...`, verify the certificate fingerprint equals `fp` before sending anything, then run the Section 4.4 steps.
- FR-M-502: Typed code: normalize input, accept grouped or ungrouped, run the steps, and pin the fingerprint seen.
- FR-M-503: Errors map to clear messages: window closed, wrong code (with remaining attempts if provided), locked out, interception suspected (server proof mismatch), unreachable.
- FR-M-504: Discovery list marks already-paired hosts by `server_id` and hosts with an open pairing window by the `pair` TXT flag. Manual entry is always visible.
- FR-M-505: Multiple hosts are supported; switching host closes the current connection first.

### 10.8 Settings

Hosts (rename, forget which also sends `UNPAIR_SELF` when online); Haptics (on/off, intensity); Alerts (rules editor); Display (system, light, dark; keep screen on while Deck is open); Telemetry interval (0.5, 1, 2, 5 s); Security (optional biometric app lock via `local_auth`, shows pinned fingerprint); About (app and protocol versions, licenses, link to docs).

### 10.9 State management

- Riverpod providers (examples): `hostsRepositoryProvider`, `connectionControllerProvider` (state machine above), `clientProvider`, `snapshotProvider`, `actionsProvider`, `layoutControllerProvider`, `runsControllerProvider`, `runLogProvider(runId)`, `telemetryProvider`, `alertsProvider`, `settingsProvider`.
- Models are immutable (`freezed`). Controllers never touch widgets; widgets never touch the socket.
- `DeckhandClient` exposes broadcast `Stream`s per event family plus `Future<T> request(...)` with a 10 s timeout and correlation by `reply_to`.
- Failures are a sealed hierarchy (`NetworkFailure`, `ProtocolFailure(code)`, `AuthFailure`, `ValidationFailure`, `UnsupportedFailure`). The UI maps them to localized messages; raw exceptions are never shown.

### 10.10 Accessibility, i18n, design

- Semantics labels on all controls (cards announce label, status, and running state), minimum 48 dp touch targets, WCAG AA contrast, dynamic type up to 200 %, reduced-motion support, status never conveyed by color alone (icon or text accompanies color).
- All strings in ARB files via `flutter_gen`; English only in v1, structure ready for more.
- Material 3 with dark and light themes from design tokens in `app/theme/tokens.dart` (spacing, radii, status colors, typography).

## 11. Non-Functional Requirements

Reference machine: 4-core CPU, 16 GB RAM, Wi-Fi 5 LAN. Reference phone: mid-range Android from the last four years.

- NFR-001 (latency): tap to `ACTION_ACCEPTED` under 150 ms p95 on LAN; process output to phone screen under 150 ms p95 added latency; telemetry sample to phone under 300 ms.
- NFR-002 (daemon footprint): idle with no sessions and no enabled alerts under 1 % average CPU; one session with 1 Hz telemetry under 3 %; resident memory under 100 MB (target 80 MB).
- NFR-003 (throughput): one run emitting 10,000 lines/s must not stall the event loop for more than 100 ms (batching and drop policy in Section 7.8). The phone stays at 60 fps with 1,000 lines/s streaming (UI updates batched per frame).
- NFR-004 (scale): 4 concurrent sessions, 16 concurrent runs, 100 actions, 12 layout pages.
- NFR-005 (stability): a 24 h soak with one session, 1 Hz telemetry, and periodic runs shows under 10 % memory growth. 1,000 connect/disconnect cycles leak no sockets, tasks, or subscriptions.
- NFR-006 (recovery): after the network returns, the phone is Online again within 3 s p95.
- NFR-007 (mobile lifecycle): when the app is backgrounded the socket stays open for 30 s then closes (no background execution in v1); on resume it reconnects immediately. No wakelock unless the keep-screen-on setting is enabled and the Deck is visible.
- NFR-008 (mobile performance): cold start to Hosts screen under 2 s; release APK under 40 MB.
- NFR-009 (observability): `deckhand doctor` and the `status` RPC report connection counts, active runs, dropped frames, provider health, and last config reload result.
- NFR-010 (maintainability): cyclomatic complexity at most 10 (`ruff C901`); guideline of 400 lines per file and 50 lines per function; docstrings on all public classes and functions; no module-level mutable state.
- NFR-011 (portability): OS-specific code lives only in `platform/`, `process/`, and `telemetry/providers/`. Everything else is OS-neutral and unit-testable on any OS.
- NFR-012 (privacy): no data leaves the local network except the opt-in notifier. No analytics or crash-reporting SDKs.
- NFR-013 (security): all suites in Section 12.4 pass on every PR.

## 12. Testing Strategy

### 12.1 Principles

Test pyramid: many fast unit tests, fewer integration tests against a real server on an ephemeral port, a small set of end-to-end session scripts, and a manual checklist for hardware- and OS-dependent behavior. Time, randomness, and the network are injected (FakeClock, seeded RNG, fake providers, fake runner) so tests are deterministic.

### 12.2 Daemon

- Tooling: `pytest`, `pytest-asyncio`, `pytest-cov`, `hypothesis`, `jsonschema`.
- Unit: param validation and templating; config and `actions.yaml` loading (including every validation rule in 8.3); protocol codec round trips; pairing math with fixed test vectors; lockout and token-bucket limiters; ring buffer; outbox priorities and drop policy; alert hysteresis and cooldown; layout validation; probe logic with fakes; provider parsing with recorded fixtures (hwmon, sysfs, LibreHardwareMonitor JSON).
- Integration: real `websockets` server with TLS on an ephemeral port and a test client performing HELLO, pairing, AUTH, SNAPSHOT, run, signal, stdin, attach/replay, telemetry subscribe, layout edit; real subprocesses using `sys.executable -c ...` scripts that print, sleep, ignore SIGINT, spawn grandchildren, and read stdin.
- Windows-specific: CTRL\_BREAK handling, kill-tree, and ConPTY tests run in the Windows CI job; POSIX-specific tests are skipped there with explicit markers.
- End to end: scripted sessions that replay `/protocol/fixtures/sessions/*.jsonl` against the real daemon and compare the transcript.

### 12.3 Mobile

- Unit: DTOs and codec against shared fixtures; pairing proofs against the same test vectors as the daemon; reconnect policy; connection state machine; param form validation; log buffer and ANSI parser; layout editing logic.
- Widget: Deck, params sheet, terminal controls, stats tiles (including null metrics), pairing screens, error states.
- Golden: key screens in light and dark themes at two text scales.
- Integration (`integration_test`): full flows against `tools/mock_daemon` (pair, run, stream, interrupt, reorder, alert banner).

### 12.4 Security suites (daemon `tests/security/`)

- Injection: param values `; rm -rf /`, `$(id)`, backticks, `&& calc`, embedded newline, NUL, `--flag`, `../..`, very long values, unicode look-alikes. Assert the child receives the value verbatim as one argv element, no shell is involved, and rejected values never start a process.
- Protocol abuse: invalid JSON, deeply nested JSON, oversize frame, binary frame, unknown type, duplicate ids, any message other than AUTH/PAIR before auth, auth timeout, slowloris (one byte per second), connection flood beyond limits.
- Pairing: five wrong proofs close the window; replayed proof rejected; wrong fingerprint rejected on both sides; simulated MITM with a different certificate fails; expired window; second pairing after success is refused until a new window is opened.
- Tokens: revoked token rejected; live session closed within 1 s; comparison uses `hmac.compare_digest` (static check).
- Network guard: public-range source addresses rejected; private, Tailscale, and loopback accepted.
- Files: secret files created with 0600 on POSIX; startup refuses looser permissions.
- Redaction: tokens, secrets, and secret params never appear in logs or the audit log.
- Fuzz: `hypothesis` on the envelope parser and the param validator.

### 12.5 Contract tests

`make protocol-check` validates every fixture against its schema, validates that both daemon and mobile encoders produce schema-valid output, and fails on schema changes without matching fixtures.

### 12.6 Coverage and static analysis

- Daemon line coverage: at least 85 % overall; at least 95 % for `security`, `actions/params.py`, `actions/templating.py`, `protocol`.
- Mobile line coverage: at least 80 % for `data/` and `domain/`; at least 70 % overall.
- Python: `ruff check`, `ruff format --check`, `mypy --strict`, `import-linter`, `bandit`. Dart: `dart format --set-exit-if-changed`, `dart analyze --fatal-infos`.

### 12.7 Manual test checklist (tracked in `docs/dev/testing.md`)

Windows Ctrl+C and kill-tree with a real dev server; tray on Windows, GNOME with AppIndicator, KDE, macOS; mDNS on home Wi-Fi and on guest Wi-Fi (expected failure, manual entry works); Tailscale connection via 100.x address; Android and iOS local-network permission prompts; QR scan in low light; haptic patterns on two devices; phone sleep and resume mid-run.

### 12.8 Performance and soak

`tools/loadtest` provides a log flood (10,000 lines/s), a session flood, and a reconnect storm. Results for NFR-001 to NFR-006 are recorded in `docs/perf.md` for each release.

## 13. CI/CD, Packaging, Release

### 13.1 GitHub Actions

- `daemon-ci.yml`: matrix (ubuntu, windows, macos) x (Python 3.11, 3.12, 3.13). Steps: ruff, ruff format check, mypy, import-linter, pytest with coverage, bandit. The Windows job runs the Windows-marked process tests.
- `mobile-ci.yml`: `flutter pub get`, `build_runner` with a no-diff check, format, analyze, tests with coverage, `flutter build apk --debug`. Optional macOS job builds iOS without signing.
- `protocol-ci.yml`: JSON Schema meta-validation, fixture validation, cross-validation from both codebases.
- `security.yml`: `pip-audit`, OSV scanner, `gitleaks`, dependency review on PRs, weekly schedule.
- `release.yml`: on tag `vX.Y.Z`: build PyInstaller bundles on three OSes, build wheel and sdist, build Android APK and AAB, generate `SHA256SUMS`, create a GitHub Release with the changelog. Signing steps run only when secrets are present.
- Branch protection: all checks required, linear history, one review for non-trivial changes.
- `dependabot.yml`: weekly updates for pip, pub, and GitHub Actions.

### 13.2 Daemon packaging and autostart

- Install paths: `pipx install deckhand-daemon` or `uv tool install`; single-folder PyInstaller bundles for each OS.
- Autostart (`deckhand autostart enable`): Windows `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`; Linux systemd user unit `~/.config/systemd/user/deckhand.service` with an XDG autostart `.desktop` fallback; macOS LaunchAgent `~/Library/LaunchAgents/app.deckhand.daemon.plist`.
- Firewall guidance printed by `deckhand doctor`: Windows Defender Firewall prompt (allow private networks only), `ufw allow from 192.168.0.0/16 to any port 47800 proto tcp` on Linux, macOS prompt on first run.
- Linux tray needs AppIndicator libraries; otherwise the daemon runs headless (FR-D-803).

### 13.3 Versioning and documentation

- SemVer for artifacts; protocol integer version separate. The README carries a compatibility table (app version, daemon version, protocol version).
- Changelog generated from Conventional Commits (`git-cliff`).
- Required docs by v1.0: `README.md` (what it is, screenshots, quick start), `CONTRIBUTING.md`, `SECURITY.md` (private reporting, supported versions), `docs/security/threat-model.md`, `docs/user-guide/*`, `docs/protocol.md`, ADRs.

## 14. Implementation Phases

Security is part of Phase 1, not retrofitted. Each phase ends with the Definition of Done in 0.2.

### Phase 0 - Foundations

- Deliverables: monorepo skeleton from Section 5 (empty packages with docstrings stating responsibility and allowed imports), Makefile, pre-commit, CI workflows, `pyproject.toml` and `pubspec.yaml` with lint and type configs, import-linter contracts, `/protocol` envelope schema plus HELLO, AUTH, AUTH\_OK, ERROR schemas and fixtures, ADR drafts 0001-0007, README, CONTRIBUTING, SECURITY, `PROGRESS.md`.
- Acceptance: `make check` passes; CI green on all three OS for the daemon; a deliberate forbidden import is caught by import-linter (proved by a test); protocol-check validates fixtures.

### Phase 1 - Secure vertical slice (MVP)

- Daemon: config and paths, logging with redaction, TLS generation, source-IP guard, WebSocket server with envelope, codec, and router, HELLO and AUTH, full pairing (window, secret, proofs, lockout), device store, audit log, `actions.yaml` loader with registry, param validation and templating (`exec` and `script`; `shell` gated), pipe-mode runners for POSIX and Windows, run manager (RUN\_STATE, PROCESS\_LOG, timeouts, basic TERMINATE and KILL), SNAPSHOT, CLI (`serve`, `pair`, `devices`, `actions validate`, basic `doctor`), minimal control channel.
- Mobile: app shell and theme, host storage, manual host entry, QR and typed-code pairing, pinned client, connection state machine with reconnect, SNAPSHOT handling, a single-page deck derived from snapshot order, run action, params sheet, basic run log view, secure storage.
- Acceptance: (1) first start creates the certificate and `deckhand pair` prints a QR and code; (2) pairing works by QR and by typed code, and five wrong codes close the window; (3) tapping an action runs it, streams logs, and shows the exit code; (4) the injection suite passes (no shell, leading-dash rejected, verbatim argv); (5) unauthenticated sockets are closed at 5 s, and a revoked device is disconnected within 1 s; (6) contract tests pass on both sides; (7) daemon suite is green on Windows and Linux; (8) coverage targets met for the touched modules.

### Phase 2 - Telemetry and Stats

- Daemon: telemetry models, sampler, providers (psutil, Linux hwmon, NVIDIA, AMD sysfs, optional LibreHardwareMonitor), capabilities in SNAPSHOT, subscribe and unsubscribe, P2 backpressure.
- Mobile: Stats tab with gauges and charts, subscription lifecycle tied to visibility, null-metric handling, formatting.
- Acceptance: frames arrive at the requested rate within 10 %; unsupported metrics are null and hidden in the UI; a failing provider never drops the frame; the sampler stops when there are no subscribers and no alert rules; NFR-002 measured and recorded; fake-provider tests cover degraded and recovering providers.

### Phase 3 - Discovery, tray, layout, multi-device

- Daemon: mDNS registration, tray and pairing window, autostart, layout store and `LAYOUT_SET`, `CONFIG_CHANGED`, actions hot reload, device management (tray and CLI).
- Mobile: mDNS discovery, hosts list, multi-host, edit mode with reorder, pages, grid sizes, widgets, device unpair, reconnect polish.
- Acceptance: discovered hosts appear on the same LAN; manual entry works when mDNS is blocked; a reordered layout survives daemon restart and appears on a second paired phone; editing `actions.yaml` updates the app without restarting; autostart enable and disable verified on each OS via the manual checklist.

### Phase 4 - Terminal control

- Daemon: INTERRUPT, TERMINATE, KILL per OS, stdin, pty mode (`ptyprocess`, `pywinpty`), `RUN_ATTACH` replay, P1 backpressure and gap markers, macros, `RUN_RESIZE`.
- Mobile: terminal sheet, control bar, ANSI rendering, `xterm` view with soft keys, Run again, reattach after reconnect.
- Acceptance: Ctrl+C interrupts a long-running Python script on Linux and Windows; kill leaves no orphan processes (grandchild test); stdin echo test passes; a progress-bar tool renders correctly in pty mode; a 10,000 lines/s flood keeps loop lag under 100 ms and the phone responsive; reconnect resumes logs from `since_seq` without duplicates.

### Phase 5 - Status and Alerts

- Daemon: probes and scheduler, `STATUS_UPDATE`, alert engine and rule store, `ALERT_*`.
- Mobile: status rings, alert banner, haptics, alert rules editor, Alerts list.
- Acceptance: stopping a container flips its card within two probe intervals; hysteresis and cooldown tests pass; the foreground haptic fires on a test alert (manual check); rules edited on the phone persist across daemon restarts.

### Phase 6 - Hardening, packaging, polish

- Deliverables: audit-log completeness, secure-defaults checklist verified by automated tests where possible, `tls rotate`, optional app lock, accessibility pass, in-log search, ntfy notifier, packaging (PyInstaller, wheels, APK/AAB), complete user guide, soak and load tests, threat-model review, v1.0.0 release.
- Acceptance: 24 h soak passes; all NFRs measured and recorded in `docs/perf.md`; a new user completes install and pairing in under 10 minutes following the guide; no open high-severity findings from `pip-audit`, OSV, or `bandit`.

## 15. Risks, Open Questions, Appendices

### 15.1 Risks

| ID | Risk | Mitigation |
| :-- | :-- | :-- |
| R1 | Tray unavailable on some Linux desktops (GNOME without AppIndicator) | Headless fallback, CLI covers everything |
| R2 | ConPTY and `pywinpty` quirks | pty is opt-in per action; pipe mode remains default; Windows CI tests |
| R3 | iOS local-network permission and background limits | Documented, foreground-only, manual entry fallback |
| R4 | LibreHardwareMonitor setup friction on Windows | Opt-in; capability flags hide missing sensors |
| R5 | Firewall blocks the port | `deckhand doctor` prints exact steps |
| R6 | Dart certificate-pinning API changes | Isolated in `pinned_http_client.dart` with its own tests |
| R7 | mDNS unreliable on some networks | Manual entry always available |
| R8 | `xterm` or reorder-grid package maintenance | Both wrapped behind small interfaces so they can be swapped |
| R9 | Scope creep | Non-goals in 1.3; changes go through ADRs |

### 15.2 Open questions (defaults apply unless an ADR changes them)

- OQ1: License MIT vs Apache-2.0. Default MIT.
- OQ2: Final project name. Default Deckhand.
- OQ3: Biometric app lock default. Default off.
- OQ4: Simultaneous connections to several PCs. Default one active connection, many saved hosts.
- OQ5: Token expiry or rotation. Default none in v1.

### Appendix A - Golden session (expected message order)

1. Connect over TLS. Daemon sends `HELLO`.
2. Phone sends `AUTH`. Daemon sends `AUTH_OK`, then `SNAPSHOT`.
3. Phone sends `TELEMETRY_SUBSCRIBE` (interval 1000).
4. Phone sends `ACTION_RUN` (docker-up). Daemon sends `ACTION_ACCEPTED`, `RUN_STATE` (STARTING, RUNNING).
5. Daemon streams `PROCESS_LOG` batches interleaved with `TELEMETRY_UPDATE` frames.
6. Daemon sends `RUN_STATE` (EXITED, exit\_code 0). Phone shows a success flash and a success haptic.
7. Phone sends `LAYOUT_SET`; daemon replies `LAYOUT_OK` and sends `CONFIG_CHANGED` (layout) to other sessions.

### Appendix B - Kickoff prompts for the coding agent

Use one prompt per phase. Replace N.

```
Read docs/SRD.md completely. Then implement Phase N only, following Section 0.1.
Before coding, list the files you will create or change and the requirement IDs
they cover. Write tests with the code. Run make check and fix everything.
Update PROGRESS.md and CHANGELOG.md. Do not start the next phase.
If any requirement is ambiguous, choose the safest simple option and record an ADR.
```

Phase 0 prompt addition:

```
Create the full repository skeleton from Section 5 with module docstrings, the
Makefile, CI workflows, lint and type configs, import-linter contracts, and the
initial protocol schemas and fixtures. No feature code yet.
```

When a phase finishes, ask the agent for a self-review against the phase acceptance criteria and the SEC requirements before moving on.
