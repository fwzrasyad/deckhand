# Architecture

Purpose: Record the architecture of the Python daemon and the Flutter phone app:
the component diagram, the daemon runtime and threading model, layer and import
rules, key flows, state ownership, and the module map (SRD Sections 3 and 5.2-5.3).

Status: outline, to be written in later.

## Component diagram

Diagrams and the daemon/phone split (Section 3.1).

## Daemon runtime and threading model

One asyncio loop on the core thread, executor for blocking work, tray on the
main thread, headless mode (Section 3.2).

## Daemon layering and import rules

Layers 0-4, allowed cross-service imports, composition root, import-linter
enforcement (Section 3.3).

## Mobile layering

Feature-first folders, inward dependencies, shared code (Section 3.4).

## Key flows

Run, telemetry, and pairing flows (Section 3.5).

## State ownership

Which side owns each piece of state and where it is stored (Section 3.6).

## Module map

Daemon and mobile module responsibilities (Sections 5.2, 5.3).
