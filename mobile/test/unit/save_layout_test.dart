import 'package:deckhand/domain/entities/deck_layout.dart';
import 'package:deckhand/domain/usecases/save_layout.dart';
import 'package:flutter_test/flutter_test.dart';

const _actionCell = DeckCell(
  column: 0,
  row: 0,
  kind: DeckCellKind.action,
  actionId: 'docker-up',
);

const _validPage = LayoutPage(
  id: 'p1',
  title: 'Main',
  columns: 3,
  rows: 3,
  cells: [_actionCell],
);

void main() {
  group('SaveLayout.problemWith', () {
    test('accepts a layout that fits the grid', () {
      expect(
        SaveLayout.problemWith(
          const DeckLayout(rev: 1, pages: [_validPage]),
        ),
        isNull,
      );
    });

    test('rejects more than twelve pages', () {
      final pages = [
        for (var i = 0; i < 13; i++)
          LayoutPage(id: 'p$i', title: 'Page $i', columns: 2, rows: 2),
      ];
      expect(
        SaveLayout.problemWith(DeckLayout(rev: 1, pages: pages)),
        contains('at most 12 pages'),
      );
    });

    test('rejects a page wider than six columns', () {
      expect(
        SaveLayout.problemWith(
          const DeckLayout(
            rev: 1,
            pages: [
              LayoutPage(id: 'p1', title: 'Wide', columns: 7, rows: 2),
            ],
          ),
        ),
        contains('1-6 columns wide'),
      );
    });

    test('rejects a cell that leaves the grid', () {
      expect(
        SaveLayout.problemWith(
          const DeckLayout(
            rev: 1,
            pages: [
              LayoutPage(
                id: 'p1',
                title: 'Main',
                columns: 3,
                rows: 3,
                cells: [
                  DeckCell(
                    column: 2,
                    row: 0,
                    kind: DeckCellKind.action,
                    actionId: 'x',
                    columnSpan: 2,
                  ),
                ],
              ),
            ],
          ),
        ),
        contains('outside the grid'),
      );
    });

    test('rejects overlapping cells', () {
      expect(
        SaveLayout.problemWith(
          const DeckLayout(
            rev: 1,
            pages: [
              LayoutPage(
                id: 'p1',
                title: 'Main',
                columns: 3,
                rows: 3,
                cells: [
                  _actionCell,
                  DeckCell(
                    column: 0,
                    row: 0,
                    kind: DeckCellKind.widget,
                    widgetKind: DeckWidgetKind.cpu,
                  ),
                ],
              ),
            ],
          ),
        ),
        contains('overlap'),
      );
    });
  });
}
