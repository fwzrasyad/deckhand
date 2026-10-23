import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/action_meta.dart';
import 'package:deckhand/domain/entities/run.dart';

/// Reads the action catalogue and starts runs.
///
/// The catalogue comes from the daemon snapshot and is read-only on the phone;
/// actions can only be created by editing `actions.yaml` on the PC (SEC-002).
abstract interface class ActionRepository {
  /// Returns the actions from the most recent snapshot.
  Future<List<ActionMeta>> loadActions();

  /// Asks the daemon to run [actionId] with [params].
  ///
  /// Fails with `ValidationFailure` after local pre-validation, or with the
  /// daemon's `ERROR` code when the request is rejected server-side.
  Future<Result<Run>> runAction(
    String actionId, {
    Map<String, String> params,
  });
}
