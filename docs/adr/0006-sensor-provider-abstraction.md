# 0006 - Sensor provider abstraction

- **Status:** Accepted
- **Date:** 2026-10-23
- **SRD references:** D4; Sections 3.5, 9.4, 9.5; FR-D-401 to FR-D-405, FR-D-501 to FR-D-503

## Context

Sensor coverage differs by OS and hardware: psutil temperatures are Linux-only
and GPUtil is NVIDIA-only (D4). A single sampler cannot assume that CPU
temperature or GPU metrics exist, and a failing sensor must not break telemetry
for the rest of the frame.

## Decision

Telemetry is collected through pluggable `SensorProvider` implementations behind
one interface.

- **Interface:** `name`, `detect() -> capabilities`, `sample() -> partial frame`
  (FR-D-401). `sample()` runs in the executor with an 800 ms timeout.
- **Providers (FR-D-402):**
  - `PsutilProvider`: CPU usage, per-core, frequency; memory and swap; disk IO
    and volumes; network rates; battery. All platforms. Base provider.
  - `LinuxHwmonProvider`: CPU temperature. Linux. Uses
    `psutil.sensors_temperatures()`, picking `coretemp`, `k10temp`, `zenpower`,
    or `cpu_thermal`.
  - `NvidiaProvider`: GPU usage, VRAM, temperature. Windows, Linux. Uses `nvidia-ml-py`; absent driver or library means unsupported.
  - `AmdSysfsProvider`: GPU usage, VRAM, temperature. Linux (amdgpu); reads sysfs `gpu_busy_percent` and hwmon.
  - `LibreHwMonitorProvider`: CPU temperature, AMD/Intel GPU. Windows; opt-in via `telemetry.libre_hardware_monitor_url`.
  - macOS temperatures and GPU are reported as unsupported in v1.
- **Unsupported metrics:** `null` in the frame and `false` in `capabilities`;
  the phone hides them (FR-D-403).
- **Failure:** a failing provider is logged once, marked degraded, and retried
  with exponential backoff up to 60 s. It never breaks the frame (FR-D-404).
- **Rates:** computed from counter deltas over monotonic time.
  `cpu_percent(interval=None)` is primed at startup so no call blocks (FR-D-405).
- **Sampler:** runs only while a session is subscribed or an alert rule is
  enabled (FR-D-501). Tick interval is the smallest requested by any subscriber,
  clamped 500-5000 ms, default 1000 ms; scheduling is drift-free on
  `loop.time()`; providers sample concurrently (FR-D-502). Each frame has a
  monotonic `seq`, stays under 4 KiB, and is sent to each session at its own
  requested rate (FR-D-503).

## Consequences

- Supporting new hardware means adding a provider, not changing the sampler.
- Capabilities drive the phone UI, so missing metrics degrade gracefully.
- Provider work is concurrent and time-bounded; one slow provider cannot hold up
  the frame beyond its timeout.
- Held in place by provider tests covering detection, unsupported metrics, and
  degraded retry behaviour, plus sampler concurrency tests.

## Alternatives considered

- **psutil only.** Rejected: D4 records that psutil temperatures are Linux-only.
- **GPUtil for GPU metrics.** Rejected: D4 records that it is NVIDIA-only.
- **One monolithic sampler per platform.** Rationale not recorded in SRD.
- **Native macOS temperature/GPU provider in v1.** Rationale not recorded in SRD;
  the SRD only states that these metrics are unsupported in v1.
