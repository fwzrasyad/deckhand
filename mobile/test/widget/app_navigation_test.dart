import 'package:flutter_test/flutter_test.dart';

import '../helpers/pump_app.dart';

void main() {
  testWidgets('starts on the welcome screen', (tester) async {
    await pumpApp(tester);
    expect(find.text('Control your PC from your phone.'), findsOneWidget);
    expect(find.text('Get started'), findsOneWidget);
  });

  testWidgets('get started opens the hosts screen', (tester) async {
    await pumpApp(tester);
    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();

    expect(find.text('Hosts'), findsOneWidget);
    expect(
      find.text('No hosts yet. Scan the code on your PC.'),
      findsOneWidget,
    );
  });

  testWidgets('pairing screen opens from the hosts screen', (tester) async {
    await pumpApp(tester);
    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pair'));
    await tester.pumpAndSettle();

    expect(find.text('Pair a phone'), findsOneWidget);
    expect(find.text('Scan QR code'), findsOneWidget);
  });
}
