import 'package:deckhand/core/utils/duration_format.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('formatDuration', () {
    test('shows tenths of a second below one second', () {
      expect(formatDuration(const Duration(milliseconds: 400)), '0.4s');
    });

    test('shows whole seconds below a minute', () {
      expect(formatDuration(const Duration(seconds: 12)), '12s');
    });

    test('shows minutes with padded seconds', () {
      expect(formatDuration(const Duration(minutes: 3, seconds: 5)), '3m 05s');
    });

    test('shows hours with padded minutes', () {
      expect(formatDuration(const Duration(hours: 1, minutes: 2)), '1h 02m');
    });
  });
}
