/// The connection state machine the UI renders (SRD 10.2).
enum ConnectionStatus {
  /// No socket, and auto-reconnect is off.
  disconnected,

  /// A socket is being opened.
  connecting,

  /// The TLS session is up and `AUTH` has been sent.
  authenticating,

  /// `AUTH_OK` and the snapshot have been received.
  connected,

  /// The socket dropped and a backoff retry is pending.
  reconnecting,

  /// The last attempt failed; the UI shows the error and offers a retry.
  error,
}
