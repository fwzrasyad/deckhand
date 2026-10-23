import 'package:deckhand/core/errors/failure.dart';
import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/run.dart';
import 'package:deckhand/domain/repositories/action_repository.dart';

/// Starts an action and hands the resulting run back to the caller.
///
/// Rejects an empty action id locally so a malformed card cannot reach the
/// daemon. All parameter validation is the daemon's job (SEC-003); this layer
/// only does cheap sanity checks.
final class RunAction {
  /// Creates the use case.
  const RunAction(this.actions);

  /// Source of the action catalogue and runs.
  final ActionRepository actions;

  /// Runs [actionId] with [params].
  Future<Result<Run>> call(
    String actionId, {
    Map<String, String> params = const {},
  }) {
    if (actionId.isEmpty) {
      return Future.value(
        const Err(ValidationFailure('No action selected.')),
      );
    }
    return actions.runAction(actionId, params: params);
  }
}
