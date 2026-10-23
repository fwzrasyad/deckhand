# Protocol

Purpose: Human-readable reference for the Deckhand wire protocol. The normative
contract is `/protocol/`: schemas, fixtures, and `VERSION` (SRD Sections 5.1,
7, 7.10).

Status: outline, to be written in later.

## Transport
One WebSocket port with TLS; JSON text frames; the loopback control channel on 47801 is separate (Section 7.1).
## Envelope
Fields, request/response correlation, and unknown-field handling (Section 7.2).
## Versioning
Non-breaking and breaking changes, `HELLO`/`AUTH`/`AUTH_OK` negotiation, `protocol/VERSION` (Section 7.3).
## Connection lifecycle
TLS handshake, `HELLO`, `AUTH` or `PAIR_REQUEST`, deadlines, reconnect (Section 7.4).
## Message catalog
Client and server message types and payloads (Section 7.5).
## Shared payload shapes
Reusable structures referenced by messages (Section 7.6).
## Error and close codes
Error registry and WebSocket close codes (Section 7.7).
## Ordering, delivery, and backpressure
Per-session ordering, queues, gap markers, and drop policy (Section 7.8).
## Keepalive, timeouts, reconnect
Heartbeat, idle timeouts, and resume after reconnect (Section 7.9).
## Contract testing
Schemas and fixtures, `make protocol-check`, cross-validation, mock daemon (Section 7.10).
