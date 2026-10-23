/// The failures the app can surface to the user.
///
/// Failures carry a message safe to show in the UI. They never carry tokens,
/// proofs, or raw server payloads (SRD SEC-016).
sealed class Failure {
  /// Creates a failure with a user-facing [message].
  const Failure(this.message, {this.cause});

  /// Human-readable explanation, safe to display.
  final String message;

  /// The underlying error, if any. Never shown to the user.
  final Object? cause;

  @override
  String toString() => 'Failure($message)';
}

/// The network is unreachable or the socket dropped.
final class NetworkFailure extends Failure {
  /// Creates a network failure.
  const NetworkFailure(super.message, {super.cause});
}

/// The host answered with something the client cannot parse or accept.
final class ProtocolFailure extends Failure {
  /// Creates a protocol failure.
  const ProtocolFailure(super.message, {super.cause});
}

/// Pairing or authentication was rejected.
final class AuthFailure extends Failure {
  /// Creates an authentication failure.
  const AuthFailure(super.message, {super.cause});
}

/// Secure storage or preferences could not be read or written.
final class StorageFailure extends Failure {
  /// Creates a storage failure.
  const StorageFailure(super.message, {super.cause});
}

/// A parameter or layout submitted by the user is invalid.
final class ValidationFailure extends Failure {
  /// Creates a validation failure.
  const ValidationFailure(super.message, {super.cause});
}
