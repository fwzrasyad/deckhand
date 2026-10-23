import 'package:deckhand/features/alerts/presentation/alerts_screen.dart';
import 'package:deckhand/features/connection/presentation/connection_screen.dart';
import 'package:deckhand/features/deck/presentation/deck_screen.dart';
import 'package:deckhand/features/discovery/presentation/hosts_screen.dart';
import 'package:deckhand/features/onboarding/presentation/onboarding_screen.dart';
import 'package:deckhand/features/pairing/presentation/pairing_screen.dart';
import 'package:deckhand/features/runs/presentation/runs_screen.dart';
import 'package:deckhand/features/settings/presentation/settings_screen.dart';
import 'package:deckhand/features/telemetry/presentation/telemetry_screen.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

/// Route table for the app (SRD 10.1).
///
/// Addresses are path constants on each screen, so tests and deep links never
/// hard-code strings. A new router is built per app instance, which gives
/// widget tests a clean location.
abstract final class AppRouter {
  /// Builds the route table.
  static GoRouter create() => GoRouter(
    initialLocation: OnboardingScreen.path,
    routes: [
      GoRoute(
        path: OnboardingScreen.path,
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: HostsScreen.path,
        builder: (context, state) => const HostsScreen(),
      ),
      GoRoute(
        path: PairingScreen.path,
        builder: (context, state) => const PairingScreen(),
      ),
      GoRoute(
        path: ConnectionScreen.path,
        builder: (context, state) => const ConnectionScreen(),
      ),
      GoRoute(
        path: DeckScreen.path,
        builder: (context, state) => const DeckScreen(),
      ),
      GoRoute(
        path: RunsScreen.path,
        builder: (context, state) => const RunsScreen(),
      ),
      GoRoute(
        path: TelemetryScreen.path,
        builder: (context, state) => const TelemetryScreen(),
      ),
      GoRoute(
        path: AlertsScreen.path,
        builder: (context, state) => const AlertsScreen(),
      ),
      GoRoute(
        path: SettingsScreen.path,
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
    errorBuilder: (context, state) => _RouteErrorScreen(
      message: state.error?.toString() ?? 'Unknown route: ${state.uri}',
    ),
  );
}

final class _RouteErrorScreen extends StatelessWidget {
  const _RouteErrorScreen({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Center(child: Text(message));
}
