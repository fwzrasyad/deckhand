import 'package:flutter/services.dart';
import 'package:vibration/vibration.dart';

/// Haptics for action feedback and alerts.
///
/// Uses the `vibration` plugin for patterns and falls back to Flutter's
/// `HapticFeedback` when the device or platform has no vibrator. Haptics only
/// fire while the app is in the foreground (SRD 9.6, v1 non-goal: no background
/// execution).
final class HapticService {
  /// Creates the service. [enabled] lets the settings screen mute all feedback.
  const HapticService({this.enabled = true});

  /// Whether haptics are currently allowed by user settings.
  final bool enabled;

  /// Short tick fired when an action is accepted (SRD S1).
  Future<void> tick() =>
      _vibrate(durationMs: 30, fallback: HapticFeedback.lightImpact);

  /// Double pulse used when an action finishes.
  Future<void> success() => _vibrate(
    durationMs: 60,
    fallback: HapticFeedback.mediumImpact,
  );

  /// Pattern used for warning and critical alerts (SRD 9.6).
  Future<void> alert() => _vibrate(
    durationMs: 200,
    fallback: HapticFeedback.heavyImpact,
  );

  /// Returns a copy of this service with haptics switched on or off.
  HapticService copyWith({bool? enabled}) =>
      HapticService(enabled: enabled ?? this.enabled);

  Future<void> _vibrate({
    required int durationMs,
    required Future<void> Function() fallback,
  }) async {
    if (!enabled) {
      return;
    }
    try {
      await Vibration.vibrate(duration: durationMs);
    } on Exception {
      // No vibrator, or the platform denied it: use the light-weight fallback.
      await fallback();
    }
  }
}
