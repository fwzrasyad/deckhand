# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report security issues privately via GitHub's private vulnerability reporting:
<https://github.com/YOUR_ORG/deckhand/security/advisories/new>

Or email: security@example.com (replace with real address before publication)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We aim to respond within 48 hours and provide a fix within 14 days for
critical issues.

## Security Design

See [docs/security/threat-model.md](docs/security/threat-model.md) for the
full threat model and [docs/security/pairing.md](docs/security/pairing.md)
for the pairing protocol specification.

Key design decisions:
- TLS 1.2+ with certificate pinning (no CA trust)
- Transcript-bound HMAC pairing proofs (60-bit secret)
- Action allowlist — clients send only `action_id`, never shell commands
- Per-device revocation, audit logging, rate limiting
