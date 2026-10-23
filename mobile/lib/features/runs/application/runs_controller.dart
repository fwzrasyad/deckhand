import 'package:deckhand/domain/entities/run.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the runs the daemon has reported during this session.
///
/// Phase 1 fills this from `RunRepository.watchRuns()` and appends log lines to
/// the matching terminal buffer.
final class RunsController extends Notifier<List<Run>> {
  @override
  List<Run> build() => const [];

  /// The runs reported during this session.
  List<Run> get runs => state;

  /// Replaces the list after a snapshot or a batch of `RUN_STATE` messages.
  set runs(List<Run> value) => state = value;

  /// Inserts or updates one run, newest first.
  void upsert(Run run) =>
      state = [run, ...state.where((existing) => existing.runId != run.runId)];
}

/// Runs state for the runs list and terminal screens.
final runsControllerProvider = NotifierProvider<RunsController, List<Run>>(
  RunsController.new,
);
