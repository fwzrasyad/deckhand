# deckhand-daemon

PC-side daemon for Deckhand. It exposes a small set of owner-defined actions,
streams hardware telemetry, and runs processes whose output it streams to a
paired phone over an authenticated, TLS-pinned WebSocket.

Everything the daemon is allowed to execute lives in the local `actions.yaml`
that the PC owner edits. The phone only ever sends an `action_id` plus validated
parameters (SRD SEC-001, SEC-002).

## Layout

| Path | Responsibility |
| :-- | :-- |
| `src/deckhand/bootstrap.py` | The only composition root; wires concrete classes and starts services in order. |
| `src/deckhand/cli/` | Typer commands (`serve`, `pair`, `devices`, `actions`, `tls`, `autostart`, `doctor`). |
| `src/deckhand/config/` | Loads and validates `config.toml`; resolves platform paths. |
| `src/deckhand/core/` | Error base classes, IDs, clock, event bus, lifecycle, rate limiters, ring buffer, atomic writes. |
| `src/deckhand/platform/` | OS-specific facts behind an interface. |
| `src/deckhand/protocol/` | Pydantic models and the envelope codec. No I/O. |
| `src/deckhand/transport/` | WebSocket server, TLS, source-IP guard, sessions, router, handlers. |
| `src/deckhand/security/` | Pairing, tokens, device store, audit log, lockout, redaction. |
| `src/deckhand/actions/` | `actions.yaml` parsing, param validation, argv templating, macros. |
| `src/deckhand/process/` | Runner abstraction, run manager, log buffers, signal mapping. |
| `src/deckhand/status/` | Status probes and their scheduler. |
| `src/deckhand/telemetry/` | Sampler loop and sensor providers. |
| `src/deckhand/alerts/` | Alert rules, evaluation engine, notifiers. |
| `src/deckhand/layout/` | Deck layout model and persistence. |
| `src/deckhand/discovery/` | mDNS registration. |
| `src/deckhand/control/` | Loopback JSON-RPC admin channel used by the CLI and tray. |
| `src/deckhand/tray/` | pystray app and pairing window. |

## Layering

Import rules are enforced by `import-linter` (see `[tool.importlinter]` in
`pyproject.toml`, SRD 3.3):

```
edges (cli, tray, control, bootstrap)
  -> transport
    -> domain services (security, actions, process, status, telemetry, alerts, layout, discovery)
      -> protocol
        -> foundations (core, config, platform)
```

Domain services may not import `transport`. Cross-service imports are limited to
`actions -> process`, `status -> process`, and `alerts -> telemetry`.

## Development

```bash
uv sync                  # create .venv and install runtime + dev dependencies
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run lint-imports
uv run pytest
```

`make check` at the repository root runs all of the above plus the mobile and
protocol checks.

## Configuration

Paths follow the platform conventions resolved by `platformdirs`, and can be
overridden with `DECKHAND_HOME` (used by tests). Example files live in
`examples/`.

## License

MIT.
