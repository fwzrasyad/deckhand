import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Settings that live on the phone rather than on the daemon.
final class SettingsState {
  /// Creates a state. Both toggles default to on.
  const SettingsState({this.hapticsEnabled = true, this.keepScreenOn = true});

  /// Whether action feedback may vibrate the phone (SRD 9.6).
  final bool hapticsEnabled;

  /// Whether the deck keeps the screen awake while connected (SRD 9.6).
  final bool keepScreenOn;

  /// Returns a copy with the given fields replaced.
  SettingsState copyWith({bool? hapticsEnabled, bool? keepScreenOn}) =>
      SettingsState(
        hapticsEnabled: hapticsEnabled ?? this.hapticsEnabled,
        keepScreenOn: keepScreenOn ?? this.keepScreenOn,
      );
}

/// Reads and writes the phone-side settings.
///
/// Phase 1 persists these through `PrefsStore`; the defaults matter because a
/// fresh install must feel deliberate.
final class SettingsController extends Notifier<SettingsState> {
  @override
  SettingsState build() => const SettingsState();

  /// Switches haptic feedback on or off.
  void setHaptics({required bool enabled}) =>
      state = state.copyWith(hapticsEnabled: enabled);

  /// Switches the keep-awake behaviour on or off.
  void setKeepScreenOn({required bool enabled}) =>
      state = state.copyWith(keepScreenOn: enabled);
}

/// Settings state for the settings screen.
final settingsControllerProvider =
    NotifierProvider<SettingsController, SettingsState>(
      SettingsController.new,
    );
