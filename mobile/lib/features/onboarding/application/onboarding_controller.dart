import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the first-run state of the app.
///
/// Phase 0 only tracks whether the welcome flow was completed. Phase 1 loads
/// the flag from preferences and seeds the router redirect from it (SRD 10.1).
final class OnboardingController extends Notifier<bool> {
  @override
  bool build() => false;

  /// Marks the welcome flow as finished.
  void complete() => state = true;
}

/// Onboarding state for the onboarding screen.
final onboardingControllerProvider =
    NotifierProvider<OnboardingController, bool>(OnboardingController.new);
