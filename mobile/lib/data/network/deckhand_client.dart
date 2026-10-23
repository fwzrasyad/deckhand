import 'dart:async';

import 'package:deckhand/data/protocol/envelope.dart';

/// A live connection to one daemon.
///
/// The concrete implementation (TLS-pinned WebSocket, `AUTH`, `HELLO` handling,
/// outbox and reconnect) arrives with the Phase 1 vertical slice. Everything
/// above this interface is written against it, so the transport can be faked in
/// tests and in `tools/mock_daemon`-driven development.
abstract interface class DeckhandClient {
  /// Decoded messages from the daemon, in arrival order.
  Stream<Envelope> get messages;

  /// Opens the socket to [uri] and verifies the daemon certificate against
  /// [pinnedFingerprint]. A `null` fingerprint is only allowed while pairing
  /// from a typed code (SRD 4.4 step 1).
  Future<void> connect(Uri uri, {required String? pinnedFingerprint});

  /// Sends one message.
  Future<void> send(Envelope envelope);

  /// Closes the socket and completes any pending request with an error.
  Future<void> close();
}
