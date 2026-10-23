# Threat model

Purpose: State what Deckhand protects, where trust boundaries lie, and which
threats and security requirements shape the daemon and phone app (SRD
Section 4).

Status: outline, to be written in Phase 6.

## Assets and trust boundaries

Actions, device tokens, TLS private key, process output; network untrusted until
pairing or token auth (Section 4.1).

## Threat model

Threats T1-T5 and their mitigations (Section 4.2).

## Security requirements

SEC-001 to SEC-022 and the rules they impose (Section 4.3).

## Limits and abuse controls

Failed auth and pairing lockouts, connection limits, frame limits, token
buckets, run limits (Section 4.7).

## Audit log

JSON-lines events, rotation, and what is never recorded (Section 4.8).

## Secure-defaults checklist

Items verified in Phase 6 (Section 4.9).
