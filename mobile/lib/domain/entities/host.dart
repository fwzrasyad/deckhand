/// A development PC the phone can connect to.
///
/// Hosts are stored on the phone (`shared_preferences`); the pinned fingerprint
/// is the only thing about a host that is trusted, and it lives in secure
/// storage (SRD 4.5, SEC-018).
final class Host {
  /// Creates a host.
  const Host({
    required this.id,
    required this.name,
    required this.address,
    required this.port,
    this.pinnedFingerprint,
    this.lastConnectedAt,
  });

  /// Stable identifier generated when the host is first saved.
  final String id;

  /// Display name, defaulting to the daemon's `server_name`.
  final String name;

  /// Hostname or IP address, for example `192.168.1.20` or a Tailscale 100.x.
  final String address;

  /// TCP port of the daemon's WebSocket listener.
  final int port;

  /// Lowercase hex SHA-256 of the daemon certificate, once pinned.
  final String? pinnedFingerprint;

  /// When the app last completed an authenticated session with this host.
  final DateTime? lastConnectedAt;

  /// True when the certificate has been pinned, so connections can be trusted.
  bool get isPinned => pinnedFingerprint != null;

  /// Returns a copy with the given fields replaced.
  Host copyWith({
    String? name,
    String? address,
    int? port,
    String? pinnedFingerprint,
    DateTime? lastConnectedAt,
  }) => Host(
    id: id,
    name: name ?? this.name,
    address: address ?? this.address,
    port: port ?? this.port,
    pinnedFingerprint: pinnedFingerprint ?? this.pinnedFingerprint,
    lastConnectedAt: lastConnectedAt ?? this.lastConnectedAt,
  );
}
