import 'package:deckhand/domain/entities/connection_status.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Mirrors the connection state machine into the UI (SRD 10.2).
///
/// Phase 1 keeps this in sync with `ConnectionRepository.watchStatus()`.
final class ConnectionController extends Notifier<ConnectionStatus> {
  @override
  ConnectionStatus build() => ConnectionStatus.disconnected;

  /// The state last reported by the repository.
  ConnectionStatus get status => state;

  /// Records a new state emitted by the repository.
  set status(ConnectionStatus value) => state = value;

  /// True while a session is usable.
  bool get isConnected => state == ConnectionStatus.connected;
}

/// Connection state for the connection banner and screen.
final connectionControllerProvider =
    NotifierProvider<ConnectionController, ConnectionStatus>(
      ConnectionController.new,
    );
