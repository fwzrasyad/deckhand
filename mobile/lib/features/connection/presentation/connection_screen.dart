import 'package:deckhand/domain/entities/connection_status.dart';
import 'package:deckhand/features/connection/application/connection_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Shows where the session stands and why (SRD 10.2).
///
/// The banner form of this screen sits above the deck while a session is being
/// established or is retrying; the full screen is reachable from settings.
final class ConnectionScreen extends ConsumerWidget {
  /// Creates the screen.
  const ConnectionScreen({super.key});

  /// Route path.
  static const String path = '/connection';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(connectionControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Connection')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(_iconFor(status), size: 48),
            const SizedBox(height: 16),
            Text(_describe(status), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  static IconData _iconFor(ConnectionStatus status) => switch (status) {
    ConnectionStatus.connected => Icons.link,
    ConnectionStatus.connecting ||
    ConnectionStatus.authenticating ||
    ConnectionStatus.reconnecting => Icons.sync,
    ConnectionStatus.disconnected || ConnectionStatus.error => Icons.link_off,
  };

  static String _describe(ConnectionStatus status) => switch (status) {
    ConnectionStatus.disconnected => 'Not connected.',
    ConnectionStatus.connecting => 'Connecting to your PC…',
    ConnectionStatus.authenticating => 'Verifying this phone…',
    ConnectionStatus.connected => 'Connected.',
    ConnectionStatus.reconnecting => 'Connection lost. Retrying…',
    ConnectionStatus.error => 'Could not connect.',
  };
}
