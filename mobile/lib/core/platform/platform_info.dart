import 'dart:io' show Platform;

/// Facts about the device the app runs on.
///
/// Behind an interface so widget tests can run on the host without touching
/// `dart:io` platforms.
abstract interface class PlatformInfo {
  /// True when the app runs on Android.
  bool get isAndroid;

  /// True when the app runs on iOS.
  bool get isIOS;

  /// True when text input should request numeric keyboards by default.
  bool get prefersNumericKeyboards;
}

/// [PlatformInfo] backed by `dart:io`.
final class IOPlatformInfo implements PlatformInfo {
  /// Creates an instance that reads from `dart:io`.
  const IOPlatformInfo();

  @override
  bool get isAndroid => Platform.isAndroid;

  @override
  bool get isIOS => Platform.isIOS;

  @override
  bool get prefersNumericKeyboards => true;
}
