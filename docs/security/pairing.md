# Pairing

Purpose: Describe how a phone is paired with the daemon: the secret and QR
format, the pairing window and limits, certificate pinning, the transcript-bound
HMAC handshake, device tokens, and failure handling (SRD Sections 4.4-4.6).

Status: outline, to be written in later.

## Secret and QR code

60 random bits as 12 Crockford Base32 characters, input normalization, and the
`deckhand://pair?...` URI (Section 4.4).

## Pairing window

Opened by CLI or tray, 120 s, closes on success or `--cancel`, 5 failed proofs
and a 30 s cooldown (Section 4.4). Implemented by `security/pairing.py`
(`PairingWindow`).

- Opening a window that is already open returns the same window (same secret,
  same expiry). Opening during the cooldown is refused.
- Each `PAIR_CHALLENGE` allows exactly one `PAIR_PROOF`. A second proof on the
  same challenge, or a proof with an unknown challenge, counts as a failed proof.
- The 5 failed proofs are counted across all clients. A request that finds the
  window closed or cooling down, or whose `device_id`/`client_nonce` is
  malformed, counts against the source IP only, not against the window.
- The first success closes the window. Handshakes still in flight are refused
  with `PAIR_WINDOW_CLOSED`, so one window never pairs two devices.
- A challenge belongs to the window that issued it; it is useless after that
  window closes.
- The window has no timers. Expiry is applied against the clock on every call,
  and the owner can call `expire_if_due()` so the audit event is not delayed.

## Certificate pinning

QR path verifies `fp` and aborts on mismatch; typed-code path records `fp_seen`
(Sections 4.4, 4.5).

## Handshake

`PAIR_REQUEST` -> `PAIR_CHALLENGE` -> `PAIR_PROOF` -> `PAIR_OK`, including the
transcript format and constant-time checks (Section 4.4).

## Failure codes

`PAIR_WINDOW_CLOSED`, `PAIR_BAD_PROOF`, `PAIR_LOCKED_OUT`, close code 4401
(Section 4.4).

`PAIR_LOCKED_OUT` is returned both while the 30 s post-lockout cooldown runs and
while the source IP is blocked (below). The 5th failed proof itself is answered
`PAIR_BAD_PROOF`; later requests get `PAIR_LOCKED_OUT`. An IP block is checked
first, so its `retry_after` wins when both apply.

## Per-IP lockout

Failed auth and pairing attempts are rate limited per source IP (Section 4.7,
SEC-010), implemented by `security/lockout.py` (`LockoutTracker`).

- 5 failures block the address for 60 s. After a block ends, the next single
  failure blocks it again for twice as long, up to 15 minutes.
- An address with no failures for 1 hour is forgotten.
- Failures from an address that is already blocked are ignored, so hammering
  through a block neither extends nor escalates it.
- A successful authentication does not reset the streak, and failures
  accumulate with no sliding window: only an hour of quiet clears them. This
  follows Section 4.7 literally.
- IPv4-mapped IPv6 addresses are treated as their IPv4 form, and IPv6 scope ids
  are ignored, so one host cannot split failures across spellings.
- The table is bounded (4096 addresses). When full, quiet addresses are
  forgotten first, then the oldest unblocked one; if every entry is blocked, the
  block ending soonest is dropped.
- IPv6 clients are tracked per exact address, not per prefix. A client that
  rotates through addresses in its own prefix is therefore not slowed by this
  tracker; the source-IP allowlist (SEC-011) is what limits who can reach it.

## Tokens and device store

`devices.json` fields, atomic writes, hashed tokens, no expiry in v1, revoke and
`UNPAIR_SELF` (Section 4.6).
