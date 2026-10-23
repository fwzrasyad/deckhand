# Protocol DTOs

Typed payload models for every protocol message live here.

## Convention

- Each message type gets one file, named after the type in snake_case:
  `auth_request.dart`, `auth_ok.dart`, `snapshot.dart`, `run_state.dart`, ...
- Models are `freezed` classes with `json_serializable` factories:
  `@freezed class AuthOk with _$AuthOk { ... }`. Generated files
  (`*.freezed.dart`, `*.g.dart`) are produced by `build_runner`.
- DTOs are the only layer that knows JSON key names. Domain entities are mapped
  from DTOs in `data/repositories/`, so a protocol field rename does not ripple
  into the UI.
- Payloads are decoded leniently: unknown fields are ignored (PROTO-002), and a
  missing required field produces a `ProtocolFailure`, never a crash.

## Why they are not written yet

Phase 0 ships the skeleton. The DTOs are generated from the schemas under
`/protocol/schemas` in Phase 1, together with the pairing and run flows that use
them, and validated against `/protocol/fixtures` (PROTO-007).
