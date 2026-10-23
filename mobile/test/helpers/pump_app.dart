import 'package:deckhand/app/app.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Pumps a fresh app instance inside a [ProviderScope].
///
/// A new app instance builds its own router, so each test starts on the
/// initial route instead of wherever the previous test navigated to.
Future<void> pumpApp(WidgetTester tester) async {
  await tester.pumpWidget(const ProviderScope(child: DeckhandApp()));
  await tester.pumpAndSettle();
}
