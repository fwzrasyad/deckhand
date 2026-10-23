import 'package:deckhand/domain/entities/telemetry_frame.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the newest telemetry sample.
///
/// Only the latest frame is kept: charts need history, and the chart widget
/// buffers it, not this controller (SRD 10.7).
final class TelemetryController extends Notifier<TelemetryFrame?> {
  @override
  TelemetryFrame? build() => null;

  /// Replaces the sample when a newer sequence number arrives.
  void update(TelemetryFrame frame) {
    final current = state;
    if (current != null && frame.seq <= current.seq) {
      return;
    }
    state = frame;
  }

  /// Drops the sample when the subscription stops.
  void clear() => state = null;
}

/// Telemetry state for the stats screen.
final telemetryControllerProvider =
    NotifierProvider<TelemetryController, TelemetryFrame?>(
      TelemetryController.new,
    );
