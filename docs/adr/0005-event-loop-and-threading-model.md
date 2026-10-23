# 0005 - Event loop and threading model

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** D8; Sections 3.2, 3.5; FR-D-401, FR-D-501, FR-D-502; NFR-003

## Context

The first draft contradicted itself on threading: it did not say whether the
daemon was single-threaded or multi-threaded (D8). The daemon must serve protocol
traffic and sessions, schedule probes, supervise processes, run a tray UI, and
perform blocking sensor, GPU, certificate, and config work. NFR-003 requires one
run emitting 10,000 lines/s not to stall the event loop for more than 100 ms,
with the phone staying at 60 fps while 1,000 lines/s stream.

## Decision

The daemon runs ONE asyncio event loop in a dedicated thread, the core thread.

- **Core thread:** all protocol handling, sessions, probe scheduling, and process
  supervision run on the loop.
- **Blocking work:** psutil sampling, GPU queries, certificate generation, and
  config file writes go through `asyncio.to_thread` or a bounded
  `ThreadPoolExecutor` with at most 4 workers. Every call has a timeout.
- **Tray:** runs on the main thread, which macOS requires (safe elsewhere). Tray
  to core uses `loop.call_soon_threadsafe` and a thread-safe command queue. Core
  to tray uses a thread-safe state object. There is no other cross-thread sharing.
- **Headless:** with `--no-tray`, the core loop runs on the main thread.
- **Subprocess output:** read with asyncio streams. Windows pty reads use an
  executor thread. Nothing blocks the loop.
- **Sensor sampling:** `sample()` runs in the executor with an 800 ms timeout
  (FR-D-401). Providers sample concurrently, and sampling ticks are drift-free on
  `loop.time()` (FR-D-502).

## Consequences

- Blocking calls cannot stall protocol handling, and each one is bounded by a
  timeout.
- Core state is owned by a single thread, so domain code needs no locks.
- A blocking call made directly on the core thread stalls every session; this is
  forbidden and must be caught in review and tests.
- The tray is the only other thread, and it communicates only through the
  command queue and state object.
- Held in place by the NFR-003 throughput test (10,000 lines/s, under 100 ms
  stall) and the `loadtest/` session-flood and log-flood generators.

## Alternatives considered

- **Multi-threaded core.** Rejected: D8 resolves the contradiction to one loop.
- **Blocking calls on the loop without a timeout.** Rejected: Section 3.2
  requires `to_thread`/executor with a timeout for every such call.
- **Tray on the core thread.** Rejected: macOS requires the tray on the main
  thread (Section 3.2).
- **No executor, all work on the loop.** Rationale not recorded in SRD.
