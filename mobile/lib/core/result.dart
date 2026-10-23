import 'package:deckhand/core/errors/failure.dart';

/// The outcome of an operation that can fail in a way the UI must handle.
///
/// Domain use cases return `Result` instead of throwing so every failure path
/// is explicit at the call site.
sealed class Result<T> {
  const Result._();

  /// Returns the payload, or `null` when this is an [Err].
  T? get valueOrNull => switch (this) {
    Ok<T>(:final value) => value,
    Err<T>() => null,
  };

  /// Returns the failure, or `null` when this is an [Ok].
  Failure? get failureOrNull => switch (this) {
    Ok<T>() => null,
    Err<T>(:final failure) => failure,
  };

  /// True when the operation succeeded.
  bool get isOk => this is Ok<T>;
}

/// Successful branch of [Result].
final class Ok<T> extends Result<T> {
  /// Creates a successful result holding [value].
  const Ok(this.value) : super._();

  /// The success payload.
  final T value;
}

/// Failed branch of [Result].
final class Err<T> extends Result<T> {
  /// Creates a failed result holding [failure].
  const Err(this.failure) : super._();

  /// Why the operation failed.
  final Failure failure;
}
