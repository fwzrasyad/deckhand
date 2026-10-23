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
and a 30 s cooldown (Section 4.4).

## Certificate pinning

QR path verifies `fp` and aborts on mismatch; typed-code path records `fp_seen`
(Sections 4.4, 4.5).

## Handshake

`PAIR_REQUEST` -> `PAIR_CHALLENGE` -> `PAIR_PROOF` -> `PAIR_OK`, including the
transcript format and constant-time checks (Section 4.4).

## Failure codes

`PAIR_WINDOW_CLOSED`, `PAIR_BAD_PROOF`, `PAIR_LOCKED_OUT`, close code 4401
(Section 4.4).

## Tokens and device store

`devices.json` fields, atomic writes, hashed tokens, no expiry in v1, revoke and
`UNPAIR_SELF` (Section 4.6).
