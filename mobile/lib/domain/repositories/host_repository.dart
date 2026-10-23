import 'package:deckhand/domain/entities/host.dart';

/// Persistence for the list of known hosts.
///
/// Implementation: `shared_preferences`. Hosts are not secret, but a pinned
/// fingerprint only counts once it is also stored in secure storage.
abstract interface class HostRepository {
  /// Returns every saved host, most recently connected first.
  Future<List<Host>> loadHosts();

  /// Inserts or updates [host].
  Future<void> saveHost(Host host);

  /// Removes the host with [id] and its credentials.
  Future<void> deleteHost(String id);
}
