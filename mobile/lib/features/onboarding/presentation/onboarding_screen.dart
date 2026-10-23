import 'package:deckhand/features/discovery/presentation/hosts_screen.dart';
import 'package:deckhand/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// First-run welcome screen (SRD 10.1).
///
/// Explains that the phone talks to a Deckhand daemon on the same network and
/// points the user at pairing. It is intentionally static: there is nothing to
/// load before a host is chosen.
final class OnboardingScreen extends StatelessWidget {
  /// Creates the screen.
  const OnboardingScreen({super.key});

  /// Route path.
  static const String path = '/welcome';

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.appTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Control your PC from your phone.',
              style: Theme.of(context).textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              'Pair once over your local network, then start actions, watch '
              'runs, and see live stats from anywhere in the house.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: () => context.go(HostsScreen.path),
              child: const Text('Get started'),
            ),
          ],
        ),
      ),
    );
  }
}
