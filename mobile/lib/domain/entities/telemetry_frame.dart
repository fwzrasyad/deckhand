/// One telemetry sample (`TELEMETRY_UPDATE`, SRD 7.6).
///
/// Units are fixed by the protocol: percent as 0-100 doubles, sizes in bytes,
/// rates in bytes per second, temperatures in Celsius. A metric the host does
/// not support is `null`, never zero.
final class TelemetryFrame {
  /// Creates a frame.
  const TelemetryFrame({
    required this.seq,
    required this.cpuPercent,
    this.cpuTempCelsius,
    this.memoryPercent,
    this.memoryUsedBytes,
    this.memoryTotalBytes,
    this.gpuPercent,
    this.gpuTempCelsius,
    this.diskReadBytesPerSecond,
    this.diskWriteBytesPerSecond,
    this.netRxBytesPerSecond,
    this.netTxBytesPerSecond,
    this.batteryPercent,
    this.isPluggedIn,
  });

  /// Monotonic sequence number; newer frames replace older ones.
  final int seq;

  /// Total CPU usage, 0-100.
  final double cpuPercent;

  /// CPU temperature in Celsius, or `null` when the host cannot report it.
  final double? cpuTempCelsius;

  /// Memory usage, 0-100.
  final double? memoryPercent;

  /// Memory in use, in bytes.
  final int? memoryUsedBytes;

  /// Installed memory, in bytes.
  final int? memoryTotalBytes;

  /// GPU usage, 0-100. The first GPU only.
  final double? gpuPercent;

  /// GPU temperature in Celsius.
  final double? gpuTempCelsius;

  /// Disk read rate, bytes per second.
  final int? diskReadBytesPerSecond;

  /// Disk write rate, bytes per second.
  final int? diskWriteBytesPerSecond;

  /// Network receive rate, bytes per second.
  final int? netRxBytesPerSecond;

  /// Network transmit rate, bytes per second.
  final int? netTxBytesPerSecond;

  /// Battery charge, 0-100, or `null` on a desktop.
  final int? batteryPercent;

  /// Whether the host is on mains power.
  final bool? isPluggedIn;

  /// True when every metric is `null`, so the UI can show a single empty state.
  bool get isEmpty =>
      cpuTempCelsius == null &&
      memoryPercent == null &&
      gpuPercent == null &&
      diskReadBytesPerSecond == null &&
      netRxBytesPerSecond == null &&
      batteryPercent == null;
}
