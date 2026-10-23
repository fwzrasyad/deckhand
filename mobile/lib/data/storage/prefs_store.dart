import 'package:shared_preferences/shared_preferences.dart';

/// Non-secret app preferences: saved hosts, UI settings, last used host.
///
/// Nothing secret may be written here. Tokens and fingerprints belong in
/// `SecureStore` (SEC-018).
final class PrefsStore {
  /// Creates a store over an already-loaded [SharedPreferences] instance.
  const PrefsStore(this._prefs);

  /// Loads the platform preference store.
  static Future<PrefsStore> open() async =>
      PrefsStore(await SharedPreferences.getInstance());

  final SharedPreferences _prefs;

  /// Reads a string, or `null` when unset.
  String? readString(String key) => _prefs.getString(key);

  /// Writes a string.
  Future<void> writeString(String key, String value) =>
      _prefs.setString(key, value);

  /// Reads a boolean, defaulting to [defaultValue].
  bool readBool(String key, {bool defaultValue = false}) =>
      _prefs.getBool(key) ?? defaultValue;

  /// Writes a boolean.
  Future<void> writeBool(String key, {required bool value}) =>
      _prefs.setBool(key, value);

  /// Removes [key].
  Future<void> remove(String key) => _prefs.remove(key);
}
