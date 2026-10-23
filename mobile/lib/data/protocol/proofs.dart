/// The pairing proofs defined in SRD 4.4.
///
/// `transcript(role)` is
/// `deckhand-pair-v1|<role>|<fp>|<client_nonce>|<server_nonce>|<device_id>`
/// and the proof is `HMAC-SHA256(K, transcript)`, base64url without padding,
/// where `K` is the normalized pairing secret as ASCII bytes.
library;

import 'dart:convert';

import 'package:crypto/crypto.dart';

const String _pairingPrefix = 'deckhand-pair-v1';

/// Role name used in the client transcript.
const String clientRole = 'client';

/// Role name used in the server transcript.
const String serverRole = 'server';

/// Normalizes a pairing code typed by the user.
///
/// Uppercase, spaces and hyphens removed, `I` and `L` become `1`, `O` becomes
/// `0` (SRD 4.4).
String normalizePairingSecret(String input) => input
    .toUpperCase()
    .replaceAll(RegExp(r'[\s-]'), '')
    .replaceAll('I', '1')
    .replaceAll('L', '1')
    .replaceAll('O', '0');

/// Builds the transcript that a proof covers.
String pairingTranscript({
  required String role,
  required String fingerprint,
  required String clientNonce,
  required String serverNonce,
  required String deviceId,
}) => [
  _pairingPrefix,
  role,
  fingerprint,
  clientNonce,
  serverNonce,
  deviceId,
].join('|');

/// Computes a pairing proof.
///
/// [secret] must already be normalized with [normalizePairingSecret].
String computePairingProof({
  required String secret,
  required String role,
  required String fingerprint,
  required String clientNonce,
  required String serverNonce,
  required String deviceId,
}) {
  final transcript = pairingTranscript(
    role: role,
    fingerprint: fingerprint,
    clientNonce: clientNonce,
    serverNonce: serverNonce,
    deviceId: deviceId,
  );
  final hmac = Hmac(sha256, ascii.encode(secret));
  final digest = hmac.convert(utf8.encode(transcript));
  return base64UrlEncode(digest.bytes).replaceAll('=', '');
}
