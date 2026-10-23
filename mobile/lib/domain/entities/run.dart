/// Lifecycle of one execution of an action (`RunState` in the protocol).
enum RunState {
  /// The process is being spawned.
  starting,

  /// The process is running.
  running,

  /// A termination signal was sent and the process has not exited yet.
  stopping,

  /// The process exited. A non-zero exit code is still [exited].
  exited,

  /// The process could not be started.
  failedToStart,

  /// The run exceeded its timeout and was stopped.
  timedOut,

  /// The run was cancelled by the user.
  cancelled,
}

/// One execution of an action, as tracked by the daemon.
final class Run {
  /// Creates a run.
  const Run({
    required this.runId,
    required this.actionId,
    required this.state,
    required this.startedAt,
    this.endedAt,
    this.exitCode,
  });

  /// Identifier assigned by the daemon when the run is registered.
  final String runId;

  /// The action this run executes.
  final String actionId;

  /// Current lifecycle state.
  final RunState state;

  /// When the run started.
  final DateTime startedAt;

  /// When the run reached a terminal state, if it has.
  final DateTime? endedAt;

  /// Process exit code, once known.
  final int? exitCode;

  /// True when no further `RUN_STATE` updates are expected.
  bool get isTerminal => switch (state) {
    RunState.starting || RunState.running || RunState.stopping => false,
    RunState.exited ||
    RunState.failedToStart ||
    RunState.timedOut ||
    RunState.cancelled => true,
  };

  /// True when the process exited with code 0.
  bool get isSuccess => state == RunState.exited && exitCode == 0;

  /// Wall-clock duration of the run so far.
  Duration durationUntil(DateTime now) =>
      (endedAt ?? now).difference(startedAt);
}
