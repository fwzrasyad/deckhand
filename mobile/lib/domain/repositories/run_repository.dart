import 'dart:async';

import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/run.dart';
import 'package:deckhand/domain/entities/run_signal.dart';

/// Observes runs and controls the ones in flight.
///
/// Logs are replayed from `since_seq` after a reconnect so the terminal never
/// loses or duplicates lines (SRD 7.9, Phase 4).
abstract interface class RunRepository {
  /// Every run the daemon reports, updated as `RUN_STATE` arrives.
  Stream<List<Run>> watchRuns();

  /// Log lines for [runId], starting at [sinceSeq] when reattaching.
  Stream<String> attachLogs(String runId, {int? sinceSeq});

  /// Sends a signal to a running process.
  Future<Result<void>> sendSignal(String runId, RunSignal signal);

  /// Writes to a run's stdin. Interactive runs only.
  Future<Result<void>> sendStdin(String runId, String data);
}
