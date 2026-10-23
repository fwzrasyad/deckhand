import 'package:logger/logger.dart';

/// Application logger with built-in redaction of secrets.
///
/// The daemon never sends a secret it does not have to, but params marked
/// `secret` and device tokens may still pass through log statements. They are
/// scrubbed here as a second line of defence (SRD SEC-016).
final class AppLogger {
  /// Creates a logger. Tests pass a silent [delegate].
  AppLogger({Logger? delegate})
    : _delegate = delegate ?? Logger(printer: SimplePrinter());

  static final RegExp _secretPattern = RegExp(
    r'(token|secret|proof|authorization)[=:]\s*\S+',
    caseSensitive: false,
  );

  final Logger _delegate;

  /// Removes anything that looks like a token, secret, or proof from [message].
  static String redact(String message) => message.replaceAllMapped(
    _secretPattern,
    (match) => '${match[1]}=***',
  );

  /// Logs a diagnostic message.
  void info(String message) => _delegate.i(redact(message));

  /// Logs a warning.
  void warn(String message) => _delegate.w(redact(message));

  /// Logs an error with an optional [error] and [stackTrace].
  void error(String message, {Object? error, StackTrace? stackTrace}) =>
      _delegate.e(redact(message), error: error, stackTrace: stackTrace);
}
