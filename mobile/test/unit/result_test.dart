import 'package:deckhand/core/errors/failure.dart';
import 'package:deckhand/core/result.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Result', () {
    test('Ok carries a value and no failure', () {
      const Result<int> result = Ok(7);
      expect(result.isOk, isTrue);
      expect(result.valueOrNull, 7);
      expect(result.failureOrNull, isNull);
    });

    test('Err carries a failure and no value', () {
      const Result<int> result = Err(NetworkFailure('no route'));
      expect(result.isOk, isFalse);
      expect(result.valueOrNull, isNull);
      expect(result.failureOrNull, isA<NetworkFailure>());
    });
  });
}
