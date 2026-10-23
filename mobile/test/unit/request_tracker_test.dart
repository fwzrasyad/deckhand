import 'package:deckhand/data/network/request_tracker.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('RequestTracker', () {
    test('completes the future tracked for a reply id', () async {
      final tracker = RequestTracker();
      final id = tracker.nextRequestId();
      final response = tracker.track(id);
      expect(tracker.pendingCount, 1);

      tracker.complete(id, const {'ok': true});
      await expectLater(response, completion(const {'ok': true}));
      expect(tracker.pendingCount, 0);
    });

    test('ignores a reply for an unknown id', () {
      final tracker = RequestTracker()..complete('never-tracked', const {});
      expect(tracker.pendingCount, 0);
    });

    test('fails every pending request when the socket closes', () async {
      final tracker = RequestTracker();
      final first = expectLater(
        tracker.track('a'),
        throwsA(isA<Exception>()),
      );
      final second = expectLater(
        tracker.track('b'),
        throwsA(isA<Exception>()),
      );

      tracker.failAll(Exception('socket closed'));
      await Future.wait([first, second]);
      expect(tracker.pendingCount, 0);
    });
  });
}
