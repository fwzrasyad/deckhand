import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/deck_layout.dart';

/// Reads and writes the deck layout.
///
/// The daemon owns `layout.json`; the phone edits it with optimistic
/// concurrency on [DeckLayout.rev] (SRD 8.4). A stale revision returns a
/// `ValidationFailure` carrying the current layout in the message details.
abstract interface class LayoutRepository {
  /// Returns the layout from the most recent snapshot.
  Future<DeckLayout> load();

  /// Saves [layout] and returns the committed revision.
  Future<Result<DeckLayout>> save(DeckLayout layout);
}
