# Pair a phone

Purpose: Walk a user through pairing the Deckhand phone app with a running
daemon by QR code or typed code, and explain what is stored and what to do when
pairing fails (SRD Sections 4.4, 9.8, 10.7).

Status: outline, to be written in Phase 6.

## Before pairing
Daemon running, phone on the same LAN or VPN, and the pairing window opened with `deckhand pair` or the tray menu (Sections 4.4, 9.8).
## Scan the QR code
The QR encodes host, port, fingerprint, secret, and name; the app verifies the certificate fingerprint and aborts on mismatch (Section 4.4).
## Type the code
The 12-character code and its normalization rules; typed entry accepts any certificate for that one connection and pins the fingerprint it sees (Section 4.4).
## What the phone stores
`device_token`, `device_id`, and the pinned fingerprint in secure storage (Section 4.4).
## Failures
Expired window, wrong code, lockout, and the possible-interception error (Section 4.4).
## Revoke or unpair
`deckhand devices revoke`, the tray, or `UNPAIR_SELF` from the phone (Section 4.6).
## Discovery is only a hint
Manual host entry always works; mDNS does not cross Tailscale or guest Wi-Fi with client isolation (Section 9.7).
