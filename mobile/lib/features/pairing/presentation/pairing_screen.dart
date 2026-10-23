import 'package:deckhand/features/pairing/application/pairing_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Pairs this phone with a daemon (SRD 10.3).
///
/// Two paths: scan the QR code shown by the daemon (the fingerprint comes from
/// the code, so the secret never travels in the open), or type the short code
/// and trust-on-first-use the certificate for that one connection (SRD 4.4).
final class PairingScreen extends ConsumerWidget {
  /// Creates the screen.
  const PairingScreen({super.key});

  /// Route path.
  static const String path = '/pair';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stage = ref.watch(pairingControllerProvider);
    final controller = ref.read(pairingControllerProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('Pair a phone')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_describe(stage), textAlign: TextAlign.center),
            const Spacer(),
            FilledButton.icon(
              onPressed: () => controller.stage = PairingStage.scanningQr,
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Scan QR code'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () => controller.stage = PairingStage.enteringCode,
              child: const Text('Enter code manually'),
            ),
          ],
        ),
      ),
    );
  }

  static String _describe(PairingStage stage) => switch (stage) {
    PairingStage.idle => 'Point the camera at the code on your PC.',
    PairingStage.scanningQr => 'Looking for a pairing code…',
    PairingStage.enteringCode => 'Type the code shown by the daemon.',
    PairingStage.verifyingProofs => 'Checking the pairing secret…',
    PairingStage.paired => 'Paired. Your PC is ready.',
    PairingStage.failed => 'Pairing failed. Check the code and try again.',
  };
}
