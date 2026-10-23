# 0004 - Pairing secret design

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** SEC-007, SEC-008, SEC-009, SEC-010; Sections 2.3 (D2, D3), 4.4, 4.7, 9.7

## Context

The first draft mentioned HMAC pairing but never specified it (D3), and a short
PIN over plain `ws://` was brute-forceable (D2). Pairing must be safe over a LAN
where a MITM may intercept, and must stay simple enough to type by hand.

## Decision

Pairing is a transcript-bound HMAC-SHA256 challenge/response over TLS, driven by
a 60-bit secret displayed once.

- **Secret:** 60 random bits from `secrets`, shown as 12 Crockford Base32
  characters grouped `XXXX-XXXX-XXXX`. Input is normalized (uppercase, strip
  spaces and hyphens, I and L become 1, O becomes 0).
- **Transport:** the QR encodes
  `deckhand://pair?host=H&port=P&fp=FP&secret=S&name=N`; typed entry also works.
- **Window:** opened by `deckhand pair` or the tray menu, lasts 120 s, and closes
  after the first successful pairing or on `deckhand pair --cancel`.
- **Attempts:** at most 5 failed `PAIR_PROOF` attempts across all clients; the
  5th closes the window and starts a 30 s cooldown. Per source IP, 5 failures
  block for 60 s, doubling up to 15 min, cleared after 1 h without failures.
- **Transcript:** `deckhand-pair-v1|<role>|<fp>|<client_nonce>|<server_nonce>|<device_id>`,
  with role `client` or `server`, where `fp` is the lowercase hex SHA-256 of the
  daemon certificate in DER form and `K` is the normalized secret as ASCII bytes.
- **Exchange:** `PAIR_REQUEST {device_id, device_name, client_nonce}` ->
  `PAIR_CHALLENGE {server_nonce}` -> `PAIR_PROOF {proof}` ->
  `PAIR_OK {device_token, server_proof}`. Both sides verify in constant time.
- **Binding to the certificate:** a QR scanner MUST abort if the presented
  certificate fingerprint differs from `fp`. Typed-code pairing accepts any
  certificate for that one connection and records `fp_seen` as the pin, so a MITM
  makes `fp_seen` differ from the daemon's `fp` and the proof check fails.
- **Result:** the phone stores `device_token`, `device_id`, and the pinned
  fingerprint in secure storage; the daemon stores only the SHA-256 hash of the
  256-bit token. Failures send `PAIR_FAIL {code}` and close 4401
  (`PAIR_WINDOW_CLOSED`, `PAIR_BAD_PROOF`, `PAIR_LOCKED_OUT`).

## Consequences

- Both proofs are bound to the certificate fingerprint and both nonces, so a
  captured proof cannot be replayed against another certificate or session.
- 60 bits plus a 120 s window and a 5-attempt lockout make guessing infeasible.
- Typed-code pairing has a weaker first contact than QR pairing: a MITM fails at
  step 6 (`server_proof`) rather than step 1. Losing the secret means re-running
  `deckhand pair`; there is no other recovery.

## Alternatives considered

- **Short numeric PIN without a window or lockout.** Rejected: brute-forceable (D2).
- **HMAC pairing left unspecified.** Rejected: D3 requires a full
  transcript-bound handshake.
- **Longer secret.** Not evaluated in the SRD. Rationale not recorded in SRD.
- **QR-only pinning, no typed-code path.** Rejected: manual entry is required
  (D12) and FR-M-502 requires typed code support that records the fingerprint.