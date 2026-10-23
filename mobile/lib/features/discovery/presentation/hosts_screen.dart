import 'package:deckhand/features/discovery/application/hosts_controller.dart';
import 'package:deckhand/features/pairing/presentation/pairing_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Saved and discovered hosts (SRD 10.1).
///
/// Discovery is a hint, not a trust decision: the list shows what was found,
/// and connecting still verifies the pinned certificate (SEC-019). Manual entry
/// is offered because mDNS fails on many networks.
final class HostsScreen extends ConsumerWidget {
  /// Creates the screen.
  const HostsScreen({super.key});

  /// Route path.
  static const String path = '/hosts';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hosts = ref.watch(hostsControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Hosts')),
      body: hosts.isEmpty
          ? const Center(child: Text('No hosts yet. Scan the code on your PC.'))
          : ListView.builder(
              itemCount: hosts.length,
              itemBuilder: (context, index) {
                final host = hosts[index];
                return ListTile(
                  title: Text(host.name),
                  subtitle: Text('${host.address}:${host.port}'),
                );
              },
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.go(PairingScreen.path),
        label: const Text('Pair'),
        icon: const Icon(Icons.qr_code_scanner),
      ),
    );
  }
}
