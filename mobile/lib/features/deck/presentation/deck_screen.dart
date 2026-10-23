import 'package:deckhand/features/deck/application/deck_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// The action grid (SRD 10.5).
///
/// Phase 1 renders `DeckLayout` pages as a draggable grid of action cards and
/// live widgets; this shell shows the empty and loaded states so the route and
/// the controller wiring are already exercised.
final class DeckScreen extends ConsumerWidget {
  /// Creates the screen.
  const DeckScreen({super.key});

  /// Route path.
  static const String path = '/deck';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final layout = ref.watch(deckControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Deck')),
      body: Center(
        child: layout == null
            ? const Text('Waiting for the daemon snapshot…')
            : Text('${layout.pages.length} pages'),
      ),
    );
  }
}
