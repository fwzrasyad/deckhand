import 'dart:io';

import 'package:crypto/crypto.dart';

/// An `HttpClient` that accepts exactly one certificate: the pinned one.
///
/// Hostname and CA validation are intentionally bypassed in favour of pinning
/// (SRD 4.5). During typed-code pairing the client records the fingerprint it
/// sees instead of checking one, which is why `acceptAny` exists; the QR path
/// always pins.
final class PinnedHttpClient {
  /// Creates a client.
  const PinnedHttpClient();

  /// Returns the lowercase hex SHA-256 of a DER-encoded certificate.
  static String fingerprintOf(List<int> derCertificate) =>
      sha256.convert(derCertificate).toString();

  /// Returns an [HttpClient] that only accepts [pinnedFingerprint].
  ///
  /// When [acceptAny] is true the fingerprint of every presented certificate is
  /// recorded through [onSeenFingerprint] and accepted. Use that only for the
  /// single pairing connection made from a typed code (SRD 4.4 step 1).
  HttpClient createClient({
    required String pinnedFingerprint,
    bool acceptAny = false,
    void Function(String fingerprint)? onSeenFingerprint,
  }) {
    final client = HttpClient()
      ..badCertificateCallback = (certificate, host, port) {
        final seen = fingerprintOf(certificate.der);
        onSeenFingerprint?.call(seen);
        return acceptAny || seen == pinnedFingerprint;
      };
    return client;
  }
}
