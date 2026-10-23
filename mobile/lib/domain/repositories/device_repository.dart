import 'package:deckhand/domain/entities/paired_device.dart';

/// Secure persistence of device credentials and pinned fingerprints.
///
/// Implementation: `flutter_secure_storage` only (SEC-018). Implementations
/// must never write tokens to preferences, logs, or crash reports.
abstract interface class DeviceRepository {
  /// Returns the credentials for [hostId], or `null` when the phone is not
  /// paired with that host.
  Future<PairedDevice?> loadFor(String hostId);

  /// Stores or replaces the credentials for a host.
  Future<void> save(PairedDevice device);

  /// Forgets the credentials for [hostId], after `UNPAIR_SELF` or revocation.
  Future<void> clear(String hostId);
}
