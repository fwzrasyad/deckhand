import 'package:deckhand/domain/entities/connection_status.dart';
import 'package:flutter/material.dart';

/// A coloured dot that shows the session state (SRD 10.2).
///
/// Used in the deck app bar and in the hosts list. The colour comes from the
/// Material 3 scheme rather than hard-coded values so both themes stay legible.
final class StatusDot extends StatelessWidget {
  /// Creates a dot for [status].
  const StatusDot({required this.status, super.key});

  /// The state to show.
  final ConnectionStatus status;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: status.name,
      child: Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: switch (status) {
            ConnectionStatus.connected => scheme.primary,
            ConnectionStatus.connecting ||
            ConnectionStatus.authenticating ||
            ConnectionStatus.reconnecting => scheme.tertiary,
            ConnectionStatus.disconnected => scheme.outline,
            ConnectionStatus.error => scheme.error,
          },
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}
