import 'dart:async';

/// Correlates request ids with the replies that answer them (SRD 7.9).
///
/// A request that gets no reply within its timeout completes with a
/// [TimeoutException] instead of leaking a pending future.
final class RequestTracker {
  /// Creates an empty tracker.
  RequestTracker();

  final Map<String, Completer<Map<String, Object?>>> _pending = {};
  int _nextId = 0;

  /// Number of requests still waiting for a reply.
  int get pendingCount => _pending.length;

  /// Allocates an id for the next request.
  String nextRequestId() => 'c-${_nextId++}';

  /// Registers [id] and returns a future completed by [complete].
  Future<Map<String, Object?>> track(String id, {Duration? timeout}) {
    final completer = Completer<Map<String, Object?>>();
    _pending[id] = completer;
    if (timeout != null) {
      Timer(timeout, () => fail(id, TimeoutException('No reply to $id')));
    }
    return completer.future;
  }

  /// Completes the request [replyTo].
  ///
  /// Unknown ids are ignored: a late reply for a timed-out request is harmless
  /// (PROTO-002).
  void complete(String replyTo, Map<String, Object?> payload) {
    _pending.remove(replyTo)?.complete(payload);
  }

  /// Fails the request [id] with [error].
  void fail(String id, Object error) {
    final completer = _pending.remove(id);
    if (completer != null && !completer.isCompleted) {
      completer.completeError(error);
    }
  }

  /// Fails every pending request, for example when the socket closes.
  void failAll(Object error) {
    for (final completer in _pending.values) {
      if (!completer.isCompleted) {
        completer.completeError(error);
      }
    }
    _pending.clear();
  }
}
