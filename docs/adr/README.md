# Architecture Decision Records

Decisions taken while building Deckhand. Each record follows
[`0000-template.md`](0000-template.md): status, date, context, decision,
consequences, alternatives considered.

The SRD (Section 0.1, rule 4) requires underspecified points to be resolved by
the simplest and safest option and recorded here. Breaking changes to
`protocol/` schemas also require a record in this directory.

## Index

| ADR | Title | Status |
| :-- | :-- | :-- |
| [0001](0001-monorepo.md) | Monorepo | Accepted |
| [0002](0002-action-allowlist-no-raw-commands.md) | Action allowlist, no raw commands | Accepted |
| [0003](0003-tls-with-cert-pinning.md) | TLS with certificate pinning | Accepted |
| [0004](0004-pairing-secret-design.md) | Pairing secret design | Accepted |

## Not yet written

The SRD (Section 5.1) also reserves 0005-0007:

| ADR | Planned title | Status |
| :-- | :-- | :-- |
| 0005 | Event loop and threading model | Not written |
| 0006 | Sensor provider abstraction | Not written |
| 0007 | Protocol source of truth | Not written |

## Conventions

- File name: `NNNN-short-kebab-title.md`, numbered in order of creation.
- Status is one of `Proposed`, `Accepted`, `Superseded by NNNN`, `Deprecated`.
- Never edit an accepted decision's meaning; supersede it with a new ADR and
  update both statuses and this index.
- Where the SRD gives no rationale, write "Rationale not recorded in SRD"
  rather than inventing one.
