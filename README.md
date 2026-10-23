# Deckhand

> Turn your smartphone into a control surface for your development PC.

[![daemon CI](https://github.com/YOUR_ORG/deckhand/actions/workflows/daemon-ci.yml/badge.svg)](https://github.com/YOUR_ORG/deckhand/actions/workflows/daemon-ci.yml)
[![mobile CI](https://github.com/YOUR_ORG/deckhand/actions/workflows/mobile-ci.yml/badge.svg)](https://github.com/YOUR_ORG/deckhand/actions/workflows/mobile-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Deckhand is a lightweight Python daemon on your PC that exposes owner-defined
actions, streams hardware telemetry, and runs processes with live output
streaming. A Flutter app on your phone shows an action grid, a stats
dashboard, and a live terminal. They communicate over an authenticated,
encrypted WebSocket on the local network or a VPN such as Tailscale.

## Features

- **One-tap actions** – Docker, git, builds, scripts, macros
- **Live telemetry** – CPU, RAM, disk, network, GPU, temperatures at 1 Hz
- **Live terminal** – process output, Ctrl+C, stdin, pty support
- **Secure by construction** – TLS + certificate pinning, paired devices only
- **Zero-config discovery** – mDNS on LAN; manual entry for Tailscale

## Quick Start

```bash
# Install the daemon
pipx install deckhand-daemon

# First run: generates TLS cert and opens a pairing window
deckhand serve

# In another terminal, open a pairing window and show QR + code
deckhand pair
```

Then open the Deckhand app on your phone and scan the QR code or type the
12-character code shown.

## Repository Structure

```
deckhand/
├── daemon/      Python daemon (PC side)
├── mobile/      Flutter app (phone side)
├── protocol/    Wire protocol schemas and fixtures (source of truth)
├── docs/        Architecture, user guide, ADRs
└── tools/       Developer utilities
```

See [docs/architecture.md](docs/architecture.md) for the full design.

## Protocol Compatibility

| App version | Daemon version | Protocol version |
|-------------|---------------|-----------------|
| 0.1.x       | 0.1.x         | 1               |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/dev/setup.md](docs/dev/setup.md).

## Security

See [SECURITY.md](SECURITY.md) and [docs/security/threat-model.md](docs/security/threat-model.md).

## License

[MIT](LICENSE)
