# 0003 - TLS with certificate pinning

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** SEC-005, SEC-006, SEC-022; Sections 2.3 (D2), 3.1, 4.5, 4.4 step 7, 9.7 (T8), 11 (R6), 12 (PinMismatch)

## Context

A 4-digit PIN over plain `ws://` is brute-forceable (D2). Traffic crosses a LAN
or Tailscale link where a rogue device, an mDNS spoofer, or a MITM may be
present. The SRD resolves this with TLS plus certificate pinning rather than a
public CA: the daemon is self-hosted on a home machine with no domain name, so
there is nothing for a CA to vouch for.

## Decision

All non-loopback listeners use TLS, and the client pins the daemon certificate.

- TLS 1.2 minimum, TLS 1.3 preferred (SEC-005). Plain `ws://` is allowed only on
  a loopback bind with `--insecure-dev`; the daemon refuses to start otherwise.
- The daemon generates a self-signed ECDSA P-256 certificate on first run, CN
  `deckhand-<hostname>`, 5-year validity, SAN with the hostname and `localhost`;
  the private key stays in the state dir with mode 0600 / restricted ACL
  (SEC-006, SEC-014).
- The client pins the SHA-256 of the DER certificate. `fp` is lowercase hex of
  that digest and is carried in the pairing QR code.
- The Dart client uses `HttpClient.badCertificateCallback` and accepts only a
  certificate whose SHA-256(DER) equals the pinned fingerprint. Hostname and CA
  validation are intentionally bypassed in favour of pinning. During typed-code
  pairing only, the callback records the fingerprint it saw instead of rejecting.
- mDNS is a hint only; trust comes from the pinned fingerprint (T8).
- `deckhand tls rotate` regenerates the certificate and revokes all pairings,
  because pinned fingerprints stop matching (SEC-022).
- A `PinMismatch` shows a blocking warning with the old fingerprint and offers
  Forget and Re-pair; it never auto-trusts.
- Tailscale connections still use TLS (defence in depth).

## Consequences

- No public CA, no domain, no certificate renewal service: the daemon is
  self-sufficient on a home LAN.
- Rotation is a breaking event for every paired device; it is bundled with
  revocation so the failure mode is explicit.
- Pinning code is the fragile point across platforms (R6), so it is isolated in
  `pinned_http_client.dart` with its own tests.
- There is no fallback to CA validation: a user who reinstalls the daemon must
  re-pair.

## Alternatives considered

- **Plain `ws://` with a shared PIN.** Rejected: brute-forceable (D2).
- **Public CA certificate (Let's Encrypt or similar).** Not evaluated in the
  SRD. Rationale not recorded in SRD.
- **Self-signed certificate with CA validation left enabled.** Rejected
  implicitly: the SRD states hostname and CA validation are intentionally
  bypassed in favour of pinning.
- **Trust-on-first-use without a pinned fingerprint.** Rejected: mDNS and
  discovery are treated as hints only; trust is the pinned fingerprint.

