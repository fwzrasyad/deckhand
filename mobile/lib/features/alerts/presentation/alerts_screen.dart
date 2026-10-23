import 'package:deckhand/domain/entities/alert_rule.dart';
import 'package:deckhand/features/alerts/application/alerts_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Alerts currently firing, with their severity (SRD 10.8).
///
/// Critical alerts also raise a banner over the deck and fire the alert haptic
/// (SRD 9.6).
final class AlertsScreen extends ConsumerWidget {
  /// Creates the screen.
  const AlertsScreen({super.key});

  /// Route path.
  static const String path = '/alerts';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alerts = ref.watch(alertsControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Alerts')),
      body: alerts.isEmpty
          ? const Center(child: Text('No alerts. All quiet.'))
          : ListView.builder(
              itemCount: alerts.length,
              itemBuilder: (context, index) {
                final alert = alerts[index];
                return ListTile(
                  leading: Icon(
                    switch (alert.severity) {
                      AlertSeverity.critical => Icons.error,
                      AlertSeverity.warning => Icons.warning_amber,
                      AlertSeverity.info => Icons.info_outline,
                    },
                  ),
                  title: Text(alert.metric),
                  subtitle: Text(
                    '${alert.value.toStringAsFixed(1)} '
                    '(limit ${alert.threshold.toStringAsFixed(1)})',
                  ),
                );
              },
            ),
    );
  }
}
