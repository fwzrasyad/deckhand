import 'package:deckhand/domain/entities/alert_rule.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the alerts currently firing.
///
/// `ALERT_RAISED` adds an alert, `ALERT_CLEARED` removes it (SRD 7.5). The list
/// is newest first so the banner shows the most recent problem.
final class AlertsController extends Notifier<List<ActiveAlert>> {
  @override
  List<ActiveAlert> build() => const [];

  /// Adds or replaces [alert].
  void raise(ActiveAlert alert) => state = [
    alert,
    ...state.where((existing) => existing.alertId != alert.alertId),
  ];

  /// Removes the alert with [alertId], if it is still firing.
  void clear(String alertId) =>
      state = state.where((alert) => alert.alertId != alertId).toList();
}

/// Alert state for the alerts screen and the critical banner.
final alertsControllerProvider =
    NotifierProvider<AlertsController, List<ActiveAlert>>(
      AlertsController.new,
    );
