import 'dart:async';

import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/alert_rule.dart';

/// Reads alert rules and streams the alerts currently firing.
///
/// Rules are stored on the daemon; the phone may edit them only when
/// `security.remote_alert_edit` is enabled (SRD 8.2).
abstract interface class AlertRepository {
  /// Alerts raised and cleared while the session is open.
  Stream<ActiveAlert> watchActiveAlerts();

  /// Returns the rule set from the most recent snapshot.
  Future<List<AlertRule>> loadRules();

  /// Saves [rules] with optimistic concurrency on [baseRev].
  Future<Result<List<AlertRule>>> saveRules(
    List<AlertRule> rules, {
    required int baseRev,
  });
}
