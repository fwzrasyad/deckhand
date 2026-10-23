# Troubleshooting

Purpose: Help a user diagnose common daemon and connection problems using
`deckhand doctor`, logs, firewall rules, and the documented fallbacks (SRD
Sections 9.7-9.9, 9.12, 13.2).

Status: outline, to be written in Phase 6.

## Start with `deckhand doctor`
The CLI reports configuration and network problems and prints firewall guidance (Sections 9.9, 13.2).
## Firewall blocks the port
Windows private-network prompt, Linux `ufw` rule for TCP 47800, macOS prompt on first run (Section 13.2).
## The phone cannot discover the host
mDNS is only a convenience; enter the address manually. Multicast does not cross Tailscale or guest Wi-Fi with client isolation (Section 9.7).
## Pairing fails
Expired window, wrong code, and lockout behaviour (Section 4.4).
## Certificate or pinning problems
Rotating the TLS certificate revokes all pairings because pinned fingerprints stop matching (SEC-022).
## Tray does not appear
Linux without AppIndicator runs headless; all features remain reachable through the CLI (FR-D-803).
## Autostart does not work
Check the per-OS autostart mechanism (Section 13.2).
## Logs
Application log and the separate rotating audit log (Sections 4.8, 9.12).
