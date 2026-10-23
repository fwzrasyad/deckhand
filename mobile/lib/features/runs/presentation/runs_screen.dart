import 'package:deckhand/core/utils/duration_format.dart';
import 'package:deckhand/features/runs/application/runs_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Runs in flight and the terminal attached to one of them (SRD 10.6).
///
/// Phase 1 adds the xterm view, the stdin bar for interactive runs, and log
/// replay from `since_seq` after a reconnect.
final class RunsScreen extends ConsumerWidget {
  /// Creates the screen.
  const RunsScreen({super.key});

  /// Route path.
  static const String path = '/runs';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final runs = ref.watch(runsControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Runs')),
      body: runs.isEmpty
          ? const Center(child: Text('Nothing running.'))
          : ListView.builder(
              itemCount: runs.length,
              itemBuilder: (context, index) {
                final run = runs[index];
                return ListTile(
                  title: Text(run.actionId),
                  subtitle: Text(
                    '${run.state.name} · '
                    '${formatDuration(run.durationUntil(DateTime.now()))}',
                  ),
                  trailing: Icon(
                    run.isTerminal
                        ? Icons.check_circle_outline
                        : Icons.play_circle_outline,
                  ),
                );
              },
            ),
    );
  }
}
