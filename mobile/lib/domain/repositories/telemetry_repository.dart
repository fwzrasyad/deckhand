import 'dart:async';

import 'package:deckhand/domain/entities/telemetry_frame.dart';

/// Subscribes to telemetry and exposes the latest sample.
///
/// The subscription is tied to screen visibility so the daemon stops sampling
/// when nobody is watching (SRD 9.5, Phase 2).
abstract interface class TelemetryRepository {
  /// Latest frames, newest last. Lossy by design: only the newest matters.
  Stream<TelemetryFrame> get frames;

  /// Asks the daemon to start sending frames every [interval].
  ///
  /// The daemon clamps the interval to 500-5000 ms (SRD 7.5).
  Future<void> subscribe({Duration interval});

  /// Asks the daemon to stop sending frames.
  Future<void> unsubscribe();
}
