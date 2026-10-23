import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// The only place the app reads and writes secrets (SEC-018).
///
/// Backed by Android Keystore and the iOS Keychain. Tokens and pinned
/// fingerprints live here; everything else goes through `PrefsStore`.
final class SecureStore {
  /// Creates a store. Tests pass a fake [storage].
  SecureStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  /// Reads [key], or `null` when it is not set.
  Future<String?> read(String key) => _storage.read(key: key);

  /// Writes [value] under [key].
  Future<void> write(String key, String value) =>
      _storage.write(key: key, value: value);

  /// Removes [key].
  Future<void> delete(String key) => _storage.delete(key: key);
}
