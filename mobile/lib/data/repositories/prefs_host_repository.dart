import 'dart:convert';

import 'package:deckhand/data/storage/prefs_store.dart';
import 'package:deckhand/domain/entities/host.dart';
import 'package:deckhand/domain/repositories/host_repository.dart';

/// Stores known hosts as a JSON list in preferences.
///
/// Hosts are not secret; the pinned fingerprint is duplicated in secure storage
/// by `SecureDeviceRepository`, so a tampered preferences file cannot redirect
/// a trusted connection to another certificate.
final class PrefsHostRepository implements HostRepository {
  /// Creates the repository over the given preferences store.
  const PrefsHostRepository(this._prefs);

  static const String _key = 'hosts.v1';

  final PrefsStore _prefs;

  @override
  Future<List<Host>> loadHosts() async {
    final raw = _prefs.readString(_key);
    if (raw == null || raw.isEmpty) {
      return const [];
    }
    final decoded = jsonDecode(raw);
    if (decoded is! List<Object?>) {
      return const [];
    }
    return decoded
        .whereType<Map<String, Object?>>()
        .map(_hostFromJson)
        .toList(growable: false);
  }

  @override
  Future<void> saveHost(Host host) async {
    final hosts = await loadHosts();
    final updated = [
      ...hosts.where((existing) => existing.id != host.id),
      host,
    ];
    await _prefs.writeString(
      _key,
      jsonEncode(updated.map(_hostToJson).toList()),
    );
  }

  @override
  Future<void> deleteHost(String id) async {
    final hosts = await loadHosts();
    final updated = hosts.where((host) => host.id != id);
    await _prefs.writeString(
      _key,
      jsonEncode(updated.map(_hostToJson).toList()),
    );
  }
}

Map<String, Object?> _hostToJson(Host host) => {
  'id': host.id,
  'name': host.name,
  'address': host.address,
  'port': host.port,
  if (host.pinnedFingerprint != null) 'fp': host.pinnedFingerprint,
  if (host.lastConnectedAt != null)
    'last_connected': host.lastConnectedAt!.toIso8601String(),
};

Host _hostFromJson(Map<String, Object?> json) => Host(
  id: json['id']! as String,
  name: json['name']! as String,
  address: json['address']! as String,
  port: json['port']! as int,
  pinnedFingerprint: json['fp'] as String?,
  lastConnectedAt: switch (json['last_connected']) {
    final String value => DateTime.tryParse(value),
    _ => null,
  },
);
