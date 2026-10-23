import 'package:deckhand/domain/entities/deck_layout.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the deck layout currently rendered.
///
/// `null` means no snapshot has arrived yet. The layout is owned by the daemon
/// and cached here for rendering and drag feedback (SRD 8.4).
final class DeckController extends Notifier<DeckLayout?> {
  @override
  DeckLayout? build() => null;

  /// The layout currently rendered, or `null` before a snapshot.
  DeckLayout? get layout => state;

  /// Replaces the layout after a snapshot or a successful save.
  set layout(DeckLayout value) => state = value;

  /// Drops the layout, for example when the session ends.
  void clear() => state = null;
}

/// Deck state for the deck screen.
final deckControllerProvider = NotifierProvider<DeckController, DeckLayout?>(
  DeckController.new,
);
