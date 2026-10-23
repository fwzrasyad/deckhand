import 'package:deckhand/features/connection/presentation/connection_screen.dart';
import 'package:deckhand/features/settings/application/settings_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Phone-side preferences and connection details (SRD 10.9).
final class SettingsScreen extends ConsumerWidget {
  /// Creates the screen.
  const SettingsScreen({super.key});

  /// Route path.
  static const String path = '/settings';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsControllerProvider);
    final controller = ref.read(settingsControllerProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Haptic feedback'),
            subtitle: const Text('Vibrate when an action starts or fails.'),
            value: settings.hapticsEnabled,
            onChanged: (enabled) => controller.setHaptics(enabled: enabled),
          ),
          SwitchListTile(
            title: const Text('Keep screen on'),
            subtitle: const Text('While connected to a host.'),
            value: settings.keepScreenOn,
            onChanged: (enabled) =>
                controller.setKeepScreenOn(enabled: enabled),
          ),
          ListTile(
            leading: const Icon(Icons.link),
            title: const Text('Connection'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.go(ConnectionScreen.path),
          ),
        ],
      ),
    );
  }
}
