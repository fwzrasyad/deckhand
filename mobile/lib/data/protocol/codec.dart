import 'dart:convert';

import 'package:deckhand/core/errors/failure.dart';
import 'package:deckhand/core/result.dart';
import 'package:deckhand/data/protocol/envelope.dart';

/// Encodes and decodes envelope frames.
///
/// One UTF-8 JSON message per text frame (SRD 7.1). Unknown top-level fields
/// and payload fields are ignored (PROTO-002), so this decoder only requires
/// the fields the envelope schema requires.
final class EnvelopeCodec {
  /// Creates a codec.
  const EnvelopeCodec();

  /// Serialises [envelope] to a JSON text frame.
  String encode(Envelope envelope) => jsonEncode({
    'v': envelope.version,
    'type': envelope.type,
    'id': envelope.id,
    if (envelope.replyTo != null) 'reply_to': envelope.replyTo,
    'ts': envelope.ts,
    'payload': envelope.payload,
  });

  /// Parses a text frame.
  ///
  /// Returns a [ProtocolFailure] rather than throwing, so callers can answer
  /// with `ERROR PROTO_MALFORMED` and close after the third strike (SRD 4.7).
  Result<Envelope> decode(String frame) {
    final Object? decoded;
    try {
      decoded = jsonDecode(frame);
    } on FormatException catch (error) {
      return Err(ProtocolFailure('Frame is not valid JSON.', cause: error));
    }
    if (decoded is! Map<String, Object?>) {
      return const Err(ProtocolFailure('Frame is not a JSON object.'));
    }
    final type = decoded['type'];
    final id = decoded['id'];
    final ts = decoded['ts'];
    final payload = decoded['payload'] ?? const <String, Object?>{};
    if (type is! String || id is! String || ts is! int) {
      return const Err(
        ProtocolFailure('Envelope is missing v, type, id or ts.'),
      );
    }
    if (payload is! Map<String, Object?>) {
      return const Err(ProtocolFailure('Envelope payload must be an object.'));
    }
    final replyTo = decoded['reply_to'];
    return Ok(
      Envelope(
        type: type,
        id: id,
        ts: ts,
        replyTo: replyTo is String ? replyTo : null,
        payload: payload,
      ),
    );
  }
}
