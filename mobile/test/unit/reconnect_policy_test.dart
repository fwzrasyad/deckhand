import 'dart:math';

import 'package:deckhand/data/network/reconnect_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ReconnectPolicy', () {
    test('first retry waits about one second', () {
      final policy = ReconnectPolicy(random: Random(7));
      expect(
        policy.delayFor(1).inMilliseconds,
        inInclusiveRange(800, 1200),
      );
    });

    test('later retries grow and stay capped near thirty seconds', () {
      final policy = ReconnectPolicy(random: Random(7));
      expect(policy.delayFor(2).inMilliseconds, inInclusiveRange(1600, 2400));
      expect(
        policy.delayFor(99).inMilliseconds,
        inInclusiveRange(24000, 36000),
      );
    });

    test('zero or negative attempts still use the first step', () {
      final policy = ReconnectPolicy(random: Random(7));
      expect(
        policy.delayFor(0).inMilliseconds,
        inInclusiveRange(800, 1200),
      );
    });
  });
}
