import 'dart:async';

import 'package:deckhand/domain/entities/connection_status.dart';
import 'package:deckhand/domain/entities/host.dart';

/// Owns the socket lifecycle and the connection state machine (SRD 10.2).
///
/// Implementations handle reconnect backoff, immediate retry on app resume or
/// network change, and the freshly requested `SNAPSHOT` after a reconnect
/// (SRD 7.9).
abstract interface class ConnectionRepository {
  /// Current state, for one-shot reads by the UI.
  ConnectionStatus get status;

  /// State changes, starting with the current value.
  Stream<ConnectionStatus> watchStatus();

  /// Opens a session to [host] and authenticates with the stored credentials.
  Future<void> connect(Host host);

  /// Closes the session and disables auto-reconnect until the next [connect].
  Future<void> disconnect();
}
