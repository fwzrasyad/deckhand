import 'dart:convert';

import 'package:deckhand/data/storage/secure_store.dart';
import 'package:deckhand/domain/entities/paired_device.dart';
import 'package:deckhand/domain/repositories/device_repository.dart';

/// Stores device tokens and pinned fingerprints in secure storage (SEC-018).
///
/// One record per host, keyed by host id. Nothing here is ever logged; the
/// record's `toString` redacts the token.
final class SecureDeviceRepository implements DeviceRepository {
  /// Creates the repository over the given secure store.
  const SecureDeviceRepository(this._store);

  final SecureStore _store;

  @override
  Future<PairedDevice?> loadFor(String hostId) async {
    final raw = await _store.read(_keyFor(hostId));
    if (raw == null || raw.isEmpty) {
      return null;
    }
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, Object?>) {
      return null;
    }
    return PairedDevice(
      hostId: hostId,
      deviceId: decoded['device_id']! as String,
      deviceName: decoded['device_name']! as String,
      token: decoded['token']! as String,
      pinnedFingerprint: decoded['fp']! as String,
    );
  }

  @override
  Future<void> save(PairedDevice device) => _store.write(
    _keyFor(device.hostId),
    jsonEncode({
      'device_id': device.deviceId,
      'device_name': device.deviceName,
      'token': device.token,
      'fp': device.pinnedFingerprint,
    }),
  );

  @override
  Future<void> clear(String hostId) => _store.delete(_keyFor(hostId));

  String _keyFor(String hostId) => 'device.$hostId';
}
