/// The kinds of live widget a layout cell can show (SRD 7.6).
enum DeckWidgetKind {
  /// CPU usage and temperature.
  cpu,

  /// Memory usage.
  ram,

  /// GPU usage and temperature.
  gpu,

  /// Disk throughput and volume usage.
  disk,

  /// Network throughput.
  net,

  /// Battery charge.
  battery,
}

/// What a layout cell renders.
enum DeckCellKind {
  /// A button that runs an action.
  action,

  /// A live telemetry tile.
  widget,
}

/// One cell in a [LayoutPage].
final class DeckCell {
  /// Creates a cell at [column], [row].
  const DeckCell({
    required this.column,
    required this.row,
    required this.kind,
    this.actionId,
    this.widgetKind,
    this.columnSpan = 1,
    this.rowSpan = 1,
  });

  /// Zero-based column index.
  final int column;

  /// Zero-based row index.
  final int row;

  /// Whether this cell runs an action or shows a widget.
  final DeckCellKind kind;

  /// The action this cell runs, when [kind] is [DeckCellKind.action].
  final String? actionId;

  /// The widget this cell shows, when [kind] is [DeckCellKind.widget].
  final DeckWidgetKind? widgetKind;

  /// How many columns the cell covers.
  final int columnSpan;

  /// How many rows the cell covers.
  final int rowSpan;
}

/// One page of the deck (SRD 8.4).
final class LayoutPage {
  /// Creates a page.
  const LayoutPage({
    required this.id,
    required this.title,
    required this.columns,
    required this.rows,
    this.cells = const [],
  });

  /// Page identifier, unique within the layout.
  final String id;

  /// Tab title.
  final String title;

  /// Grid width, at most 6.
  final int columns;

  /// Grid height, at most 8.
  final int rows;

  /// Cells placed on the grid.
  final List<DeckCell> cells;
}

/// The whole deck layout owned by the daemon and editable from the phone.
final class DeckLayout {
  /// Creates a layout at revision [rev].
  const DeckLayout({required this.rev, required this.pages});

  /// Optimistic-concurrency revision; `LAYOUT_SET` must quote the current one.
  final int rev;

  /// Pages in display order, at most 12.
  final List<LayoutPage> pages;

  /// True when there is nothing to show yet.
  bool get isEmpty => pages.isEmpty;
}
