import 'dart:math';

import 'package:deckhand/core/constants/app_constants.dart';

/// Exponential backoff with jitter for reconnects (SRD 7.9).
///
/// Delay is 1, 2, 4, 8, 16, 30 s with ±20 % jitter, capped at 30 s. The jitter
/// avoids a thundering herd when several phones reconnect after the router
/// reboots.
final class ReconnectPolicy {
  /// Creates a policy. Pass a seeded [random] in tests for determinism.
  const ReconnectPolicy({Random? random}) : _random = random;

  final Random? _random;

  /// Delay before the [attempt]-th retry, where attempt 1 is the first retry.
  Duration delayFor(int attempt) {
    const steps = AppConstants.reconnectBackoffSeconds;
    final index = (attempt < 1 ? 1 : attempt).clamp(1, steps.length) - 1;
    final baseMs = steps[index] * 1000;
    final jitter = (_random ?? Random()).nextDouble() * 0.4 - 0.2;
    return Duration(milliseconds: (baseMs * (1 + jitter)).round());
  }

  /// True when the client should keep retrying. The policy never gives up; the
  /// connect button does that.
  bool shouldRetry(int attempt) => attempt > 0;
}
