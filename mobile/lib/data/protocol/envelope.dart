/// A protocol message envelope (SRD 7.2).
final class Envelope {
  /// Creates an envelope.
  const Envelope({
    required this.type,
    required this.id,
    required this.ts,
    this.version = 1,
    this.replyTo,
    this.payload = const {},
  });

  /// Protocol version integer.
  final int version;

  /// Message type in `SCREAMING_SNAKE_CASE`, for example `ACTION_RUN`.
  final String type;

  /// Sender-generated id, unique within the session, at most 64 characters.
  final String id;

  /// Optional id of the request being answered.
  final String? replyTo;

  /// Sender wall clock in milliseconds since the epoch. Informational only.
  final int ts;

  /// Message-specific payload.
  final Map<String, Object?> payload;
}
