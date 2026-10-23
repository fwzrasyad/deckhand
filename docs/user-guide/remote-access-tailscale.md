# Remote access over Tailscale

Purpose: Explain how to reach the daemon from outside the LAN over a VPN such as
Tailscale, and why manual host entry is required there (SRD Sections 1.4, 4.5,
9.7; FR-D-703).

Status: outline, to be written in Phase 6.

## When to use it

Scenario S5: away from home, connect to the PC's Tailscale `100.x` address
(Sections 1.4, 9.7).

## Connect by address

Enter the `100.x` address as a manual host in the phone app; manual entry always
works (FR-D-703).

## Discovery does not cross the VPN

mDNS multicast does not cross Tailscale or guest Wi-Fi with client isolation
(FR-D-703).

## TLS still applies

TLS with the pinned certificate is used over Tailscale as defense in depth
(Section 4.5).

## Daemon-side address guard

The source-IP guard accepts private, Tailscale, and loopback addresses and
rejects public-range addresses (Section 12.4, SEC-011).
