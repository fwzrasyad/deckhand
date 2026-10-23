/// Product identity and protocol constants.
///
/// The working name lives here so a rename touches only this file, the mDNS
/// service type, and the `deckhand://` URI scheme (SRD Section 1). Keep these in
/// sync with `daemon/src/deckhand/version.py`.
abstract final class AppConstants {
  /// Human-readable product name.
  static const String productName = 'Deckhand';

  /// The `deckhand://` URI scheme used by pairing QR codes.
  static const String uriScheme = 'deckhand';

  /// mDNS service type advertised by the daemon (SRD 9.7).
  static const String mdnsServiceType = '_deckhand._tcp';

  /// WebSocket subprotocol selected for protocol version 1 (SRD 7.1).
  static const String protocolName = 'deckhand.v1';

  /// Protocol version integer this client speaks.
  static const int protocolVersion = 1;

  /// Default daemon port (SRD 7.1).
  static const int defaultPort = 47800;

  /// How long the daemon keeps a pairing window open (SRD 4.4).
  static const Duration pairingWindow = Duration(seconds: 120);

  /// Client request timeout for request/reply messages (SRD 7.9).
  static const Duration requestTimeout = Duration(seconds: 10);

  /// Reconnect backoff steps in seconds, capped at 30 s (SRD 7.9).
  static const List<int> reconnectBackoffSeconds = [1, 2, 4, 8, 16, 30];
}
