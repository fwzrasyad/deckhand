import 'package:deckhand/features/telemetry/application/telemetry_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Live stats for the host (SRD 10.7).
///
/// Phase 1 draws the charts with `fl_chart` and ties the subscription to screen
/// visibility with `TelemetryRepository.subscribe`/`unsubscribe`.
final class TelemetryScreen extends ConsumerWidget {
  /// Creates the screen.
  const TelemetryScreen({super.key});

  /// Route path.
  static const String path = '/stats';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final frame = ref.watch(telemetryControllerProvider);
    if (frame == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Stats')),
        body: const Center(child: Text('Waiting for telemetry…')),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Stats')),
      body: ListView(
        children: [
          ListTile(
            title: const Text('CPU'),
            trailing: Text('${frame.cpuPercent.toStringAsFixed(0)}%'),
          ),
          ListTile(
            title: const Text('Memory'),
            trailing: Text(
              frame.memoryPercent == null
                  ? '—'
                  : '${frame.memoryPercent!.toStringAsFixed(0)}%',
            ),
          ),
        ],
      ),
    );
  }
}
