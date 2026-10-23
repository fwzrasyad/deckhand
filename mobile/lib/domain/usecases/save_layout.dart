import 'package:deckhand/core/errors/failure.dart';
import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/deck_layout.dart';
import 'package:deckhand/domain/repositories/layout_repository.dart';

/// Validates a layout on the phone before sending it to the daemon.
///
/// The daemon revalidates and is authoritative (`LAYOUT_INVALID`), but catching
/// the obvious mistakes here keeps a bad drag from round-tripping. The limits
/// are the ones in SRD 7.6: 12 pages, 6 columns, 8 rows, no overlapping cells.
final class SaveLayout {
  /// Creates the use case.
  const SaveLayout(this.layouts);

  /// Maximum number of pages in a deck.
  static const int maxPages = 12;

  /// Maximum grid width.
  static const int maxColumns = 6;

  /// Maximum grid height.
  static const int maxRows = 8;

  /// Layout persistence.
  final LayoutRepository layouts;

  /// Checks [layout] and saves it when it is valid.
  Future<Result<DeckLayout>> call(DeckLayout layout) {
    final problem = problemWith(layout);
    if (problem != null) {
      return Future.value(Err(ValidationFailure(problem)));
    }
    return layouts.save(layout);
  }

  /// Returns a user-facing problem, or `null` when [layout] is valid.
  static String? problemWith(DeckLayout layout) {
    if (layout.pages.length > maxPages) {
      return 'A deck can have at most $maxPages pages.';
    }
    for (final page in layout.pages) {
      if (page.columns < 1 || page.columns > maxColumns) {
        return 'Page "${page.title}" must be 1-$maxColumns columns wide.';
      }
      if (page.rows < 1 || page.rows > maxRows) {
        return 'Page "${page.title}" must be 1-$maxRows rows tall.';
      }
      final problem = _problemWithCells(page);
      if (problem != null) {
        return problem;
      }
    }
    return null;
  }

  static String? _problemWithCells(LayoutPage page) {
    final occupied = <String>{};
    for (final cell in page.cells) {
      final right = cell.column + cell.columnSpan;
      final bottom = cell.row + cell.rowSpan;
      if (cell.column < 0 || cell.row < 0) {
        return 'A cell on "${page.title}" is outside the grid.';
      }
      if (right > page.columns || bottom > page.rows) {
        return 'A cell on "${page.title}" is outside the grid.';
      }
      for (var column = cell.column; column < right; column++) {
        for (var row = cell.row; row < bottom; row++) {
          if (!occupied.add('$column:$row')) {
            return 'Two cells on "${page.title}" overlap.';
          }
        }
      }
    }
    return null;
  }
}
